// Portao do olheiro das fichas da App Store: a pergunta "esta oferecido no
// Mac?" responde NAO quando nao esta.
//
//   node bin/conferir-olheiro.js
//
// POR QUE ELE EXISTE. Ate 14/11/2026 o `noMac` tinha um termo
// `a[href*="/mac/"]`, que casa com `apps.apple.com/us/mac/discover` — um link
// da BARRA DE NAVEGACAO presente em toda pagina da App Store. O termo nunca
// podia dar `false`: o olheiro respondia "ainda esta no Mac" para qualquer
// app, inclusive para um que nunca esteve. No dia em que a oferta sumiu de
// verdade, quem percebeu fui eu, olhando a pagina a mao; o vigia continuaria
// calado para sempre.
//
// O controle que ja existia NAO pegava isso: controle protege contra o
// medidor ficar cego JUNTO (a Apple trocar o texto da ficha), nao contra um
// termo que sempre acende. Por isso o caso 1 abaixo e o coracao deste portao:
// uma pagina que so tem a NAVEGACAO da App Store tem de responder "nao".
//
// Sem rede: as fichas sao de mentira, montadas aqui e servidas ao Chromium
// com `setContent`. Quem e exercitado e a MESMA `LER_FICHA` que o olheiro usa
// na pagina de verdade — um portao que exercitasse uma copia nao mediria nada.
const path = require("path");
const RAIZ = path.join(__dirname, "..");
const { chromium } = require(path.join(RAIZ, "motor-web/testes/node_modules/@playwright/test"));
const { LER_FICHA, decidir } = require(path.join(__dirname, "olhar-ficha-da-loja.js"));

// A navegacao que TODA ficha da App Store tem, e que nao diz nada sobre este
// app: foi exatamente ela que o termo velho media.
const NAVEGACAO = `
  <nav>
    <a href="https://apps.apple.com/us/store">Store</a>
    <a href="https://apps.apple.com/us/mac/discover">Mac</a>
    <a href="https://apps.apple.com/us/vision/apps-and-games">Vision</a>
    <a href="https://apps.apple.com/us/ipad/discover">iPad</a>
  </nav>`;

const CASOS = [
  {
    nome: "so a navegacao da App Store: NAO esta oferecido no Mac",
    ficha: `${NAVEGACAO}
            <h1>Biblioteca Pessoal</h1>
            <p>iPad, iPhone</p>
            <h2>Compatibility</h2><p>Requires iOS 17.6 or later.</p>
            <p>Version 1.9.21</p>`,
    espera: { noMac: false, versao: "1.9.21", titulo: "Biblioteca Pessoal" },
  },
  {
    nome: "o botao da oferta: esta oferecido no Mac",
    ficha: `${NAVEGACAO}
            <h1>Liber: Home Library Catalog</h1>
            <p>Free - Designed for iPhone. Not verified for macOS.</p>
            <button>View in Mac App Store</button>
            <p>Version 1.5.0</p>`,
    espera: { noMac: true, versao: "1.5.0", titulo: "Liber: Home Library Catalog" },
  },
  {
    nome: "so o texto, sem o botao: ainda e oferta",
    ficha: `${NAVEGACAO}
            <h1>App de Mentira</h1>
            <p>Designed for iPad. Not verified for macOS.</p>
            <p>Version 2.0</p>`,
    espera: { noMac: true, versao: "2.0", titulo: "App de Mentira" },
  },
  {
    nome: "um botao que so PARECE: 'Mac' no rotulo nao e a oferta",
    ficha: `${NAVEGACAO}
            <h1>Outro App</h1>
            <button>More by this developer on Mac</button>
            <p>Version 3.1</p>`,
    espera: { noMac: false, versao: "3.1", titulo: "Outro App" },
  },
  {
    nome: "ficha vazia: sem nome, para o olheiro tratar como 'nao olhei'",
    ficha: `${NAVEGACAO}<p>desculpe</p>`,
    espera: { noMac: false, versao: null, titulo: "" },
  },
];

(async () => {
  const navegador = await chromium.launch();
  let falhou = 0;
  try {
    const pagina = await navegador.newPage();
    for (const caso of CASOS) {
      await pagina.setContent(`<!doctype html><body>${caso.ficha}</body>`);
      const deu = decidir(await pagina.evaluate(LER_FICHA));
      const erros = Object.entries(caso.espera)
        .filter(([campo, valor]) => deu[campo] !== valor)
        .map(([campo, valor]) => `${campo}: esperava ${JSON.stringify(valor)}, veio ${JSON.stringify(deu[campo])}`);
      if (erros.length) {
        falhou = 1;
        console.log(`  FALHOU  ${caso.nome}`);
        erros.forEach((e) => console.log(`          ${e}`));
      } else {
        console.log(`  ok      ${caso.nome}`);
      }
    }
  } finally {
    await navegador.close();
  }
  if (falhou) console.log("\nO olheiro das fichas esta medindo errado.");
  else console.log(`\n${CASOS.length} casos: o olheiro responde NAO quando e nao.`);
  process.exit(falhou);
})().catch((e) => {
  console.error("nao consegui rodar o portao do olheiro:", e.message);
  process.exit(1);
});
