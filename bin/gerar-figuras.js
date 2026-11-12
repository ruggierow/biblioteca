// Gera as figuras dos manuais do Mac e do Windows A PARTIR DA PAGINA que os
// dois aplicativos embarcam.
//
// POR QUE ISTO EXISTE. As figuras eram a ultima parte do manual feita a mao:
// capturas de tela guardadas em base64 dentro do HTML, sem nada que as
// refizesse. Elas apodrecem sozinhas. Em 12/11/2026, com o app na 1.9.21:
//
//   - o cabecalho do Mac e do Windows ainda anunciava **v.1.9.19**;
//   - a faixa do arquivo mostrava uma frase que a 1.9.21 TIROU do aplicativo
//     ("Vincule um arquivo... em navegadores sem suporte (Safari/Firefox)").
//     Dentro do app instalado nao ha nem vinculo nem outro navegador — era o
//     manual ensinando o que o programa nao diz mais.
//
// O segundo e pior que o primeiro: numero velho o leitor perdoa, frase que
// nao existe mais o faz procurar na tela uma coisa que nao esta la.
//
// Agora a figura e SAIDA, como o PDF ja e desde 12/11 — mesmo principio do
// `gerar-manuais-pdf.js`: saida nao se edita, se regenera.
//
//   node bin/gerar-figuras.js                 todas, nos dois idiomas
//   node bin/gerar-figuras.js --listar        so diz o que faria
//   node bin/gerar-figuras.js --nao-trocar    gera os PNG e NAO mexe no manual
//   node bin/gerar-figuras.js --trocar manual-ios 2 foto.png
//                                             poe uma captura no lugar da
//                                             figura 2 daquele manual
//
// O `--trocar` existe para o iPhone e o Android, que nao saem daqui: a tela
// deles e do aparelho, nao da pagina. A CAPTURA continua sendo a mao, mas a
// troca no manual nao — era ali que se errava o numero da figura e se
// descobria depois, no PDF.
//   node bin/gerar-figuras.js manual-windows  so as de um manual
//
// O QUE ELE NAO FAZ, e e deliberado: **moldura de janela**. As figuras antigas
// do Windows traziam a barra de titulo ("Biblioteca v1.9.19"), que so existe
// na janela de verdade. Desenhar uma barra de titulo aqui seria fabricar uma
// captura de tela — a figura passaria a mostrar algo que nunca foi
// fotografado. Entao as figuras geradas sao do CONTEUDO, como ja eram as do
// Mac e as tres do Windows feitas em 12/11. A unica figura do Windows que
// continua sendo captura de verdade e a do instalador, que e do sistema e nao
// da pagina.
//
// DE ONDE VEM O QUE APARECE
//
//   - a pagina: `motor-web/biblioteca.html`, a MESMA que vai nos dois apps,
//     servida por HTTP (em `file://` o armazenamento local e capado);
//   - o hospedeiro: um duble do Tauri (Windows) ou do WKWebView (Mac), igual
//     ao do `11-selecionar-pasta.spec.js`. E o duble que faz a pagina falar
//     como aplicativo — sem ele ela se acha num navegador e mostra OUTRO
//     texto na faixa do arquivo. Era esse o defeito da figura antiga;
//   - os livros: o `biblioteca.txt` de verdade do usuario, lido pelo duble e
//     interpretado pela propria pagina. Figura de manual com biblioteca de
//     mentira mostraria tabela vazia e contagem zero;
//   - as capas: do `biblioteca.dat`, so as dos livros que aparecem na figura
//     (sao 41 MB; injetar tudo nao cabe no armazenamento do navegador);
//   - o caminho da pasta: `/Users/você/...` e `C:\Users\você\...` (`you` no
//     manual em ingles). Nao e
//     retoque na imagem — e o caminho que o duble informa, entao a pagina
//     desenha isso de verdade. O nome do dono da maquina nao vai para um
//     documento publico.
const fs = require("fs");
const http = require("http");
const path = require("path");

const RAIZ = path.join(__dirname, "..");
const DOCS = path.join(RAIZ, "docs");
const MOTOR = path.join(RAIZ, "motor-web");
const { chromium } = require(path.join(MOTOR, "testes/node_modules/@playwright/test"));

const NUVEM = path.join(process.env.HOME,
  "Library/Mobile Documents/com~apple~CloudDocs/Biblioteca");
const TSV = path.join(NUVEM, "biblioteca.txt");
const DAT = path.join(NUVEM, "biblioteca.dat");

const PORTA = 8739;

// O caminho que a figura mostra, por hospedeiro e por idioma. O marcador do
// dono da pasta e TRADUZIDO — o manual em ingles ja dizia `/Users/you/`, e uma
// figura nova dizendo `você` no meio de uma frase em ingles denunciaria de
// onde ela saiu.
const PASTA = {
  Mac: {
    pt: "/Users/você/Library/Mobile Documents/com~apple~CloudDocs/Biblioteca",
    en: "/Users/you/Library/Mobile Documents/com~apple~CloudDocs/Biblioteca",
  },
  Windows: {
    pt: "C:\\Users\\você\\iCloudDrive\\Biblioteca",
    en: "C:\\Users\\you\\iCloudDrive\\Biblioteca",
  },
};

// As pecas da pagina que viram figura.
const PECAS = {
  cabecalho: { sel: "header" },
  arquivo: { sel: "main > section:has(#ajuda-arquivo)" },
  cadastro: { sel: "main > section:has(#form-cadastro)" },
  pesquisa: { sel: "main > section:has(#btn-pesquisar)" },
  // A tabela se mede em LINHAS, nao em pixels: cortar por altura fixa pegava
  // meia linha no alto e na base, que e o tipo de desleixo que salta aos olhos
  // numa figura de manual.
  tabela: { sel: "#tabela-container", linhas: 5, capas: true },
  paginacao: { sel: "#tabela-container .paginacao" },
};

// Que figura de que manual e qual peca. O numero e a ORDEM da imagem dentro do
// HTML (a 1 e sempre o icone da capa), nao o numero da legenda.
const FIGURAS = [
  { manual: "manual-mac", n: 2, peca: "cabecalho", hospedeiro: "Mac" },
  { manual: "manual-mac", n: 9, peca: "arquivo", hospedeiro: "Mac" },
  { manual: "manual-windows", n: 2, peca: "cabecalho", hospedeiro: "Windows" },
  { manual: "manual-windows", n: 4, peca: "cadastro", hospedeiro: "Windows" },
  { manual: "manual-windows", n: 5, peca: "pesquisa", hospedeiro: "Windows" },
  // A 8 nao mostrava so texto velho: pegou o app no meio da partida, com o
  // aviso "Inicializando..." na tela. Figura de manual nao mostra estado de
  // passagem.
  { manual: "manual-windows", n: 8, peca: "arquivo", hospedeiro: "Windows" },
  { manual: "manual-windows", n: 9, peca: "tabela", hospedeiro: "Windows" },
  { manual: "manual-windows", n: 10, peca: "paginacao", hospedeiro: "Windows" },
  { manual: "manual-windows", n: 12, peca: "cadastro", hospedeiro: "Windows" },
];

const TIPOS = { ".html": "text/html; charset=utf-8", ".js": "text/javascript",
  ".css": "text/css", ".json": "application/json", ".png": "image/png",
  ".svg": "image/svg+xml", ".txt": "text/plain; charset=utf-8" };

function servidor() {
  return new Promise((pronto) => {
    const s = http.createServer((req, res) => {
      const rel = decodeURIComponent(req.url.split("?")[0]).replace(/^\/+/, "");
      const arq = path.join(MOTOR, rel);
      if (!arq.startsWith(MOTOR) || !fs.existsSync(arq) || fs.statSync(arq).isDirectory()) {
        res.writeHead(404); res.end("nao achei"); return;
      }
      res.writeHead(200, { "Content-Type": TIPOS[path.extname(arq)] || "application/octet-stream" });
      res.end(fs.readFileSync(arq));
    });
    s.listen(PORTA, "127.0.0.1", () => pronto(s));
  });
}

/**
 * O duble do hospedeiro, injetado ANTES de qualquer script da pagina.
 *
 * E na primeira linha que a pagina decide onde esta. Entrar depois seria
 * fotografar o modo navegador com um enfeite por cima — e o modo navegador
 * mostra outro texto na faixa do arquivo.
 */
function duble(hospedeiro, pasta, tsv, idioma) {
  return [hospedeiro, pasta, tsv, idioma];
}

const INJETAR = ([hospedeiro, pasta, tsv, idioma]) => {
  localStorage.setItem("biblioteca-idioma", idioma);
  localStorage.setItem("biblioteca-livros", "[]");
  localStorage.setItem("biblioteca-fotos", "{}");
  const sono = () => new Promise((r) => setTimeout(r, 1));

  if (hospedeiro === "Windows") {
    window.__TAURI__ = { core: { invoke: async (cmd) => {
      await sono();
      switch (cmd) {
        case "carregar_tsv": return tsv;
        case "info_do_arquivo":
          return JSON.stringify({ caminho: pasta + "\\biblioteca.txt",
            modificado: "", configurada: pasta, usandoConfigurada: true });
        default: return "";
      }
    } } };
    return;
  }

  // Mac: o Swift rele e reinjeta os livros sozinho na abertura.
  window.__BIBLIOTECA_NATIVE__ = true;
  window.__BIBLIOTECA_CAMINHO__ = pasta + "/biblioteca.txt";
  window.__BIBLIOTECA_KINDLE__ = false;
  window.__BIBLIOTECA_AUDIBLE__ = false;
  window.__BIBLIOTECA_LOJAS_AVISO__ = "";
  window.webkit = { messageHandlers: new Proxy({}, { get: () => ({
    postMessage: async () => { await sono(); return ""; } }) }) };
  window.addEventListener("load", () => setTimeout(() => {
    try {
      biblioteca = parseTSV(tsv);                                        // eslint-disable-line
      localStorage.setItem("biblioteca-livros", JSON.stringify(biblioteca)); // eslint-disable-line
      atualizarTudo();                                                   // eslint-disable-line
      atualizarBannerSync("ok");                                         // eslint-disable-line
      esconderCarregando();                                              // eslint-disable-line
    } catch (e) { console.error("reinjetar:", e); }
  }, 5));
};

/** As capas dos livros que a figura mostra, lidas do .dat. */
function capasDe(ids) {
  if (!fs.existsSync(DAT)) return {};
  const todas = JSON.parse(fs.readFileSync(DAT, "utf8"));
  const escolhidas = {};
  for (const id of ids) if (todas[id]) escolhidas[id] = todas[id];
  return escolhidas;
}

/** Troca a imagem de numero `n` do manual pelo PNG novo. */
function trocarNoManual(manual, n, png) {
  const arq = path.join(DOCS, `${manual}.html`);
  const html = fs.readFileSync(arq, "utf8");
  const novo = "data:image/png;base64," + fs.readFileSync(png).toString("base64");
  let vistas = 0, trocou = false;
  const saida = html.replace(/data:image\/\w+;base64,[^"')]+/g, (achado) => {
    vistas += 1;
    if (vistas !== n) return achado;
    trocou = true;
    return novo;
  });
  if (!trocou) throw new Error(`${manual}.html nao tem figura numero ${n} (tem ${vistas})`);
  fs.writeFileSync(arq, saida);
}

(async () => {
  const argv = process.argv.slice(2);

  // --trocar <manual> <numero> <arquivo.png>: uma captura feita fora daqui.
  const ondeTrocar = argv.indexOf("--trocar");
  if (ondeTrocar >= 0) {
    const [manual, numero, arquivo] = argv.slice(ondeTrocar + 1);
    if (!manual || !numero || !arquivo) {
      console.log("uso: --trocar <manual> <numero da figura> <arquivo.png>");
      process.exit(1);
    }
    if (!fs.existsSync(arquivo)) {
      console.log(`nao achei ${arquivo}`);
      process.exit(1);
    }
    trocarNoManual(manual, Number(numero), arquivo);
    const kb = Math.round(fs.statSync(arquivo).size / 1024);
    console.log(`   ok  ${manual} figura ${numero} <- ${path.basename(arquivo)} (${kb} KB)`);
    console.log("   Refaca o PDF: node bin/gerar-manuais-pdf.js " + manual);
    return;
  }

  const pedidos = argv.filter((a) => !a.startsWith("--"));
  const soListar = process.argv.includes("--listar");
  const naoTrocar = process.argv.includes("--nao-trocar");
  const alvos = FIGURAS.filter((f) => !pedidos.length || pedidos.includes(f.manual));

  if (soListar) {
    for (const f of alvos) {
      for (const idioma of ["pt", "en"]) {
        const sufixo = idioma === "en" ? "-en" : "";
        console.log(`   ${f.manual}${sufixo}  figura ${f.n}  ${f.peca}  (${f.hospedeiro})`);
      }
    }
    return;
  }

  for (const arq of [TSV, DAT]) {
    if (!fs.existsSync(arq)) {
      console.log(`Nao achei ${arq}.`);
      console.log("As figuras mostram a biblioteca DE VERDADE. Sem ela eu");
      console.log("desenharia tabela vazia e contagem zero — prefiro nao gerar.");
      process.exit(1);
    }
  }
  const tsv = fs.readFileSync(TSV, "utf8");
  const saidas = path.join(RAIZ, "dist", "figuras");
  fs.mkdirSync(saidas, { recursive: true });

  const servico = await servidor();
  const navegador = await chromium.launch();
  let feitas = 0;

  for (const idioma of ["pt", "en"]) {
    const sufixo = idioma === "en" ? "-en" : "";
    for (const f of alvos) {
      const manual = f.manual + sufixo;
      const contexto = await navegador.newContext({
        viewport: { width: 1280, height: 1000 },
        deviceScaleFactor: 2,
        locale: idioma === "en" ? "en-US" : "pt-BR",
      });
      const pagina = await contexto.newPage();
      const erros = [];
      pagina.on("pageerror", (e) => erros.push(String(e)));
      await pagina.addInitScript(INJETAR,
        duble(f.hospedeiro, PASTA[f.hospedeiro][idioma], tsv, idioma));
      await pagina.goto(`http://127.0.0.1:${PORTA}/biblioteca.html`,
        { waitUntil: "load" });
      await pagina.waitForSelector("#carregando", { state: "hidden", timeout: 20000 });

      const peca = PECAS[f.peca];
      if (peca.capas) {
        // As capas das linhas VISIVEIS. Perguntar a lista em memoria nao
        // serve: a tabela ordena por autor e pagina, entao os 12 primeiros da
        // lista nao sao os 12 primeiros da tela — foi assim que a primeira
        // tentativa injetou dez capas e mostrou zero. Quem diz quais linhas
        // estao na tela e a propria tela.
        const ids = await pagina.evaluate((sel) => {
          const titulos = [...document.querySelectorAll(sel + " table tbody tr td:nth-child(2)")]
            .map((td) => td.textContent.trim());
          const lista = (typeof livrosFiltrados !== "undefined" && livrosFiltrados.length) // eslint-disable-line
            ? livrosFiltrados : biblioteca;                                                // eslint-disable-line
          const porTitulo = new Map(lista.map((l) => [l.titulo.trim(), l.id]));
          return titulos.map((x) => porTitulo.get(x)).filter(Boolean);
        }, peca.sel);
        const capas = capasDe(ids);
        await pagina.evaluate((mapa) => {
          Object.assign(fotos, mapa);          // eslint-disable-line
          atualizarTudo();                     // eslint-disable-line
        }, capas);
        await pagina.waitForTimeout(250);
        // Capa que nao entrou tem de falar. A figura antiga mostrava tres
        // capas de verdade; uma tabela so de marcadores cinzentos seria
        // perda silenciosa — o defeito que este projeto mais combate.
        const nasLinhas = await pagina.evaluate((sel) =>
          document.querySelectorAll(sel + " table tbody tr img").length, peca.sel);
        console.log(`       capas: ${Object.keys(capas).length} de ${ids.length} ` +
          `livros tem foto no .dat; ${nasLinhas} apareceram na tabela`);
      }

      const alvo = pagina.locator(peca.sel).first();
      const png = path.join(saidas, `${manual}--${String(f.n).padStart(2, "0")}.png`);

      // Rolar ao topo antes de medir: com a pagina rolada, a caixa que o
      // Playwright devolve e relativa a JANELA, e o recorte de pagina inteira
      // e relativo ao DOCUMENTO. Os dois so coincidem no topo.
      await pagina.evaluate(() => window.scrollTo(0, 0));
      await pagina.waitForTimeout(120);
      const caixa = await alvo.boundingBox();
      let altura = caixa.height;
      if (peca.linhas) {
        const fim = await pagina.evaluate(([sel, n]) => {
          const linhas = document.querySelectorAll(sel + " table tbody tr");
          const ultima = linhas[Math.min(n, linhas.length) - 1];
          return ultima ? ultima.getBoundingClientRect().bottom + window.scrollY : null;
        }, [peca.sel, peca.linhas]);
        if (fim) altura = fim - (caixa.y);
      }
      await pagina.screenshot({ path: png, fullPage: true,
        clip: { x: caixa.x, y: caixa.y, width: caixa.width, height: altura } });

      if (!naoTrocar) trocarNoManual(manual, f.n, png);
      const kb = Math.round(fs.statSync(png).size / 1024);
      console.log(`   ok  ${manual} figura ${f.n} (${f.peca}) — ${kb} KB` +
        (erros.length ? `  AVISO: ${erros.length} erro(s) na pagina` : ""));
      if (erros.length) console.log("       " + erros[0].slice(0, 160));
      feitas += 1;
      await contexto.close();
    }
  }

  await navegador.close();
  servico.close();
  console.log(`\n${feitas} figura(s) em dist/figuras/.` +
    (naoTrocar ? " Nenhum manual foi tocado (--nao-trocar)."
               : " Refaca os PDFs: node bin/gerar-manuais-pdf.js"));
})();
