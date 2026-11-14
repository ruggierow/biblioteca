// Diz se a ficha do app na App Store ainda OFERECE o app iOS para Mac.
//
//   node bin/olhar-ficha-da-loja.js                     o app e o controle
//   node bin/olhar-ficha-da-loja.js 6799312712 ...      os ids que quiser
//
// POR QUE COM NAVEGADOR. A linha "Not verified for macOS — View in Mac App
// Store" e escrita por JavaScript: no HTML que o `curl` baixa ela NAO EXISTE,
// nem para um app que esta oferecido no Mac. Medido em 13/11/2026 com um
// controle (o `Liber`, id 6821807835), e foi o que me impediu de anunciar uma
// propagacao que nao tinha acontecido. Quem nao renderiza nao pode responder.
//
// O TERMO QUE NAO ERA MEDIDA (consertado em 14/11/2026). Ate aqui o `noMac`
// tambem olhava `a[href*="/mac/"]` — que casa com `apps.apple.com/us/mac/
// discover`, um link da BARRA DE NAVEGACAO presente em TODA pagina da App
// Store. O termo dava `true` para qualquer app, inclusive para quem nunca
// esteve no Mac: o vigia nunca teria anunciado a propagacao, e no dia em que
// ela veio quem a percebeu fui eu, olhando a pagina a mao. Termo que nao pode
// dar `false` nao e medida. O "View in Mac App Store" de verdade nem e link:
// e um `<button>` sem `href`, e e por ele que se pergunta agora.
//
// POR QUE UM CONTROLE JUNTO. Se a Apple trocar o texto da ficha, a linha some
// para TODO MUNDO e eu anunciaria uma propagacao que nao houve. O controle e
// um app alheio que esta oferecido no Mac: enquanto ELE disser "sim", um
// "nao" no nosso significa alguma coisa. Os dois dizendo "nao" no mesmo dia e
// motivo de desconfiar do medidor, nao de comemorar.
//
// Sai em JSON, uma linha, para o `vigia-loja.py` ler:
//   {"6799312712":{"noMac":true,"versao":"1.9.20","titulo":"..."}, ...}
//
// Falha e SILENCIO sao coisas diferentes: se a pagina nao carregar ou nao
// trouxer nem o nome do app, ele sai com codigo 1 e nada de JSON — quem
// chamou tem de tratar como "nao olhei", nunca como "nao esta mais no Mac".
const path = require("path");
const RAIZ = path.join(__dirname, "..");
const { chromium } = require(path.join(RAIZ, "motor-web/testes/node_modules/@playwright/test"));

// O app da Biblioteca e o CONTROLE (`Liber`, de outro autor, oferecido no Mac).
const IDS = process.argv.length > 2 ? process.argv.slice(2)
                                    : ["6799312712", "6821807835"];

// A LEITURA, que roda DENTRO da pagina. E exportada porque o portao
// (`conferir-olheiro.js`) exercita ESTA funcao sobre paginas de mentira: foi
// aqui, e nao na comparacao, que morava o termo cego.
function LER_FICHA() {
  const rotulo = (e) => (e.textContent || "").trim();
  const h1 = document.querySelector("h1");
  return {
    titulo: h1 ? h1.textContent.trim() : "",
    texto: document.body.innerText,
    // O botao, nao um link: a oferta do app iOS no Mac aparece como
    // <button>View in Mac App Store</button>. Casar o ROTULO INTEIRO e o que
    // impede de voltar a medir a navegacao da pagina.
    ofereceMac: Array.from(document.querySelectorAll("button, a"))
                     .some((e) => /^View in Mac App Store$/i.test(rotulo(e))),
  };
}

// A DECISAO, a partir da leitura. Dois termos, e os dois sao prova: o texto
// que a ficha escreve e o elemento que a ficha tem. O texto sozinho depende
// de a pagina ter renderizado; o elemento existe no DOM de qualquer jeito.
function decidir(visto) {
  return {
    noMac: /Not verified for macOS|View in Mac App Store/i.test(visto.texto)
           || visto.ofereceMac,
    versao: (visto.texto.match(/Version\s+([0-9][0-9.]*)/) || [])[1] || null,
    titulo: visto.titulo,
  };
}

module.exports = { LER_FICHA, decidir };

if (require.main !== module) return;

(async () => {
  const navegador = await chromium.launch();
  const saida = {};
  try {
    for (const id of IDS) {
      const pagina = await navegador.newPage();
      await pagina.goto(`https://apps.apple.com/us/app/id${id}`,
        { waitUntil: "domcontentloaded", timeout: 45000 });
      await pagina.waitForSelector("h1", { timeout: 30000 });
      await pagina.waitForTimeout(1200);        // o bloco do Mac entra depois
      const visto = await pagina.evaluate(LER_FICHA);
      await pagina.close();
      if (!visto.titulo) throw new Error(`a ficha de ${id} nao trouxe nem o nome`);
      saida[id] = decidir(visto);
    }
    console.log(JSON.stringify(saida));
  } finally {
    await navegador.close();
  }
})().catch((e) => {
  console.error("nao consegui olhar a ficha:", e.message);
  process.exit(1);
});
