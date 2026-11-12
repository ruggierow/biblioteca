// Gera os PDFs dos manuais A PARTIR DO HTML que esta no git.
//
// POR QUE ISTO EXISTE. Ate 12/11/2026 os oito manuais (quatro plataformas, dois
// idiomas) eram HTML e PDF gerados lado a lado por um roteiro que vivia so na
// sessao em que foram feitos: o `manifest.json` de onde os dois saiam NUNCA foi
// para o git. Resultado: no dia em que uma frase precisou mudar -- o "Selecionar
// pasta" mudou o primeiro acesso das quatro plataformas -- havia como editar o
// HTML e NAO havia como refazer o PDF. E o PDF e o que vai dentro do .dmg e o
// que a pagina do app oferece para baixar.
//
// Agora ha UMA fonte, o HTML versionado, e o PDF e SAIDA dela. O mesmo
// principio do RTL do outro projeto: saida nao se edita, se regenera.
//
// Quem desenha e o proprio Chromium do Playwright, que ja e dependencia de
// `motor-web/testes` -- nenhuma biblioteca nova, e o PDF fica igual ao que se
// ve no navegador, com os links do sumario funcionando.
//
//   node bin/gerar-manuais-pdf.js            todos os oito
//   node bin/gerar-manuais-pdf.js manual-mac manual-mac-en
//
// Confere no fim: um PDF que saiu menor que 200 KB ou com uma pagina so quase
// certamente perdeu as figuras, e passar isso adiante em silencio e o defeito
// que este projeto mais combate.

const path = require("path");
const fs = require("fs");

const RAIZ = path.join(__dirname, "..");
const DOCS = path.join(RAIZ, "docs");
const { chromium } = require(path.join(RAIZ, "motor-web/testes/node_modules/@playwright/test"));

const TODOS = [];
for (const plataforma of ["mac", "windows", "ios", "android"]) {
  TODOS.push(`manual-${plataforma}`, `manual-${plataforma}-en`);
}

/// O rodape de cada pagina, com versao e data — como no manual antigo.
///
/// A data sai da CAPA do proprio HTML, nao do relogio: regerar o PDF sem mexer
/// no texto nao pode mudar a data que o leitor ve, senao todo PDF aparece
/// alterado em todo diff.
function rodape(html, versao) {
  const m = html.match(/(?:Manual gerado em|Manual generated on)\s+([0-9-]{8,10})/);
  const data = m ? m[1] : "";
  const titulo = (html.match(/<title>(.*?)<\/title>/) || [, "Biblioteca"])[1];
  return `<div style="width:100%;font-size:7pt;color:#777;padding:0 14mm;
     font-family:-apple-system,'Segoe UI',sans-serif;display:flex;justify-content:space-between;">
     <span>${titulo} — v${versao}${data ? " — " + data : ""}</span>
     <span class="pageNumber"></span></div>`;
}

(async () => {
  const versao = fs.readFileSync(path.join(RAIZ, "VERSION"), "utf8").trim();
  const pedidos = process.argv.slice(2);
  const alvos = pedidos.length ? pedidos : TODOS;

  const navegador = await chromium.launch();
  let falhou = 0;
  for (const nome of alvos) {
    const entrada = path.join(DOCS, `${nome}.html`);
    const saida = path.join(DOCS, `${nome}.pdf`);
    if (!fs.existsSync(entrada)) {
      console.log(`   FALTA  ${nome}.html`);
      falhou = 1;
      continue;
    }
    const html = fs.readFileSync(entrada, "utf8");
    const pagina = await navegador.newPage();
    await pagina.goto("file://" + entrada, { waitUntil: "load" });
    await pagina.pdf({
      path: saida,
      format: "A4",
      printBackground: true,
      displayHeaderFooter: true,
      headerTemplate: "<span></span>",
      footerTemplate: rodape(html, versao),
      margin: { top: "14mm", bottom: "16mm", left: "14mm", right: "14mm" },
    });
    await pagina.close();

    const kb = Math.round(fs.statSync(saida).size / 1024);
    const paginas = (fs.readFileSync(saida).toString("latin1").match(/\/Type\s*\/Page[^s]/g) || []).length;
    const magro = kb < 200 || paginas < 2;
    console.log(`   ${magro ? "SUSPEITO" : "ok      "} ${nome}.pdf — ${paginas} pagina(s), ${kb} KB`);
    if (magro) falhou = 1;
  }
  await navegador.close();
  if (falhou) {
    console.log("\nHa PDF suspeito acima: pouca pagina ou pouco peso costuma ser figura perdida.");
  }
  process.exit(falhou);
})();
