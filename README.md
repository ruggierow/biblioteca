# Biblioteca

Sistema de gestão de biblioteca pessoal. **Dois motores**, cinco entregas.

O nome de cada pasta diz o motor e a plataforma que ela gera. Se você está
procurando onde mexer em alguma coisa, a resposta está nesta tabela.

| Pasta | Motor | Gera | Tecnologia |
|---|---|---|---|
| `motor-web/` | Web | — (é a fonte) | HTML + JS, arquivo único |
| `motor-web/macos/` | Web | app macOS | Swift + WKWebView |
| `motor-web/windows/` | Web | atalhos Windows | .bat / .ps1 / .vbs |
| `motor-movel/ios/` | Móvel | app iPhone | SwiftUI nativo |
| `motor-movel/android/` | Móvel | app Android (APK) | Flutter / Dart |

## Os dois motores

**Motor web** — o arquivo `motor-web/biblioteca.html`. Ele *é* o app web: uma
página só, sem servidor, sem build. As pastas `macos/` e `windows/` não têm
lógica própria; só embrulham esse arquivo para virar um app ou um atalho.

**Motor móvel** — dois apps nativos que compartilham o formato de dados e as
regras, mas não o código. `ios/` é SwiftUI e atende o iPhone; `android/` é
Flutter e atende o Android. A divisão é deliberada: a captura de capa do iOS
usa o framework Vision da Apple, que não tem equivalente em Dart.

## Uma cópia só do motor web

Antes existiam cinco cópias do `biblioteca.html` que divergiam entre si. Agora
existe **uma**, em `motor-web/biblioteca.html`. Os outros pontos apontam para ela:

- o app macOS acessa por link simbólico em `macos/Sources/BibliotecaMacWeb/Resources/`
- os atalhos procuram `./biblioteca.html` e, se não acharem, `../biblioteca.html`

Nunca edite uma cópia. Edite `motor-web/biblioteca.html` e pronto.

## Uma versão só

O arquivo `VERSION` na raiz é a única fonte. `bin/versionar.sh` carimba esse
número no HTML, no `Info.plist` do iOS, no `pubspec.yaml` do Flutter e no
`Info.plist` do app macOS. Antes da consolidação havia cinco numerações
independentes (1.7.5, 0.5.8, 1.0.0, 1.0.0+1, 0.6.0) e nenhuma resposta para
"qual a versão do Biblioteca?".

```bash
echo "1.8.1" > VERSION && ./bin/versionar.sh    # carimba em todos
./bin/empacotar.sh                              # gera os zips de distribuição
```

## O contrato entre as plataformas

Está em `comum/`. São as regras que **precisam** valer igual nos cinco lugares,
porque os apps trocam dados entre si:

- `comum/formato-tsv.md` — o arquivo de dados, 8 colunas
- `comum/foto-id.md` — o hash que liga um livro à sua foto de capa
- `comum/permissoes.md` — como cada app pede e trata permissão de câmera
- `comum/icons/` — os ícones compartilhados

Se você mudar qualquer coisa em `comum/`, mudou nos cinco. Confira os cinco.

## O que foi abandonado

`legado/` guarda o que saiu de circulação, congelado e não apagado:

- `legado/terminal-cpp/` — o menu C++ de terminal, o app original. É o único
  código do projeto com suíte de testes (28 casos, Google Test).
- `legado/web-tauri/` — empacotamento Tauri v2, substituído por
  `motor-web/macos/` e `motor-web/windows/`. Parado desde 1º de julho de 2026.

## Onde estão os arquivos de dados

A base canônica é `biblioteca.txt` no iCloud Drive da sua Apple ID:
`~/Library/Mobile Documents/com~apple~CloudDocs/Biblioteca/biblioteca.txt`.

O `motor-web/biblioteca.txt` deste repositório é só um exemplo pequeno para
desenvolvimento — não é a sua biblioteca.

**Atenção:** esta máquina tem dois *homes*. O código vive em
`/Users/wilson-16-06-2022/`; o iCloud, o Xcode e o DerivedData, em `/Users/wilson/`.
