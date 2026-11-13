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
      const visto = await pagina.evaluate(() => ({
        titulo: document.querySelector("h1")?.textContent.trim() || "",
        texto: document.body.innerText,
        temLink: !!document.querySelector('a[href*="/mac/"], a[href*="platform=mac"]'),
      }));
      await pagina.close();
      if (!visto.titulo) throw new Error(`a ficha de ${id} nao trouxe nem o nome`);
      saida[id] = {
        noMac: /Not verified for macOS|View in Mac App Store/i.test(visto.texto)
               || visto.temLink,
        versao: (visto.texto.match(/Version\s+([0-9][0-9.]*)/) || [])[1] || null,
        titulo: visto.titulo,
      };
    }
    console.log(JSON.stringify(saida));
  } finally {
    await navegador.close();
  }
})().catch((e) => {
  console.error("nao consegui olhar a ficha:", e.message);
  process.exit(1);
});
