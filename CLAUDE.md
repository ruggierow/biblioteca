# Biblioteca — Guia para o Claude Code

## O desenho do projeto

**Dois motores**, e o nome de cada pasta diz o motor e a plataforma que gera.

```
motor-web/biblioteca.html   ← o app web. Arquivo único, sem build, sem servidor.
motor-web/macos/            ← Swift + WKWebView. Só embrulha o HTML.
motor-web/windows/          ← atalhos .bat/.ps1/.vbs. Só abrem o HTML.
motor-movel/ios/            ← SwiftUI nativo, iPhone.
motor-movel/android/        ← Flutter, Android.
comum/                      ← o contrato entre todos.
legado/                     ← congelado: terminal C++, Tauri.
```

Consolidado em 3 de setembro de 2026. Antes disso eram cinco projetos soltos,
cinco numerações de versão e cinco cópias divergentes do `biblioteca.html`.

## As três regras que evitam voltar ao caos

**1. Uma cópia só do motor web.** Edite `motor-web/biblioteca.html` e mais nada.
O app macOS chega nele por link simbólico
(`macos/Sources/BibliotecaMacWeb/Resources/biblioteca.html`); os atalhos
procuram `./biblioteca.html` e depois `../biblioteca.html`. Se você encontrar
outra cópia do HTML em algum lugar, ela é lixo — apague, não sincronize.

**2. Uma versão só.** O arquivo `VERSION` na raiz. Para mudar:

```bash
echo "1.8.1" > VERSION && ./bin/versionar.sh
```

Nunca edite o número direto no HTML, no `Info.plist` ou no `pubspec.yaml`.

**3. Mexeu no contrato, confira nos cinco.** `comum/` documenta o que precisa
valer igual em todas as plataformas, porque os apps trocam dados entre si:

| Documento | Do que trata |
|---|---|
| `comum/formato-tsv.md` | o `biblioteca.txt` de 8 colunas |
| `comum/foto-id.md` | o hash FNV-1a que liga um livro à sua capa |
| `comum/permissoes.md` | como a câmera é pedida e a negação tratada |

Esses três têm implementações paralelas em Swift, Dart e JavaScript. Uma
alteração em qualquer um deles é uma alteração em todos.

## Compilar e rodar

```bash
# App iOS (simulador, sem assinatura)
cd motor-movel/ios
xcodebuild build -scheme "Biblioteca.App" -project Biblioteca-iPhone.xcodeproj \
  -destination 'platform=iOS Simulator,name=iPhone 17' \
  -configuration Debug CODE_SIGNING_ALLOWED=NO

# App Android
cd motor-movel/android && flutter analyze && flutter build apk --release

# App macOS
cd motor-web/macos && xcodebuild -project Biblioteca-Mac.xcodeproj -scheme BibliotecaWeb build

# App Windows (nativo, Tauri) — compila na VM Parallels e traz o instalador
./bin/compilar-windows.sh

# App web — é só abrir o arquivo
open motor-web/biblioteca.html

# Pacotes de distribuição do motor web
./bin/empacotar.sh
```

## Gerar uma release

O usuário pede em palavras ("gera uma nova release do Android"). A sequência é
sempre a mesma, e a ordem importa — o número vem antes do build:

```bash
echo "1.8.1" > VERSION && ./bin/versionar.sh      # carimba nos 5 pontos
cd motor-movel/android && flutter build apk --release
# sai em build/app/outputs/flutter-apk/app-release.apk
```

Para o iPhone, o mesmo `versionar.sh` e depois Archive no Xcode. Para o motor
web, `./bin/empacotar.sh`, que recusa rodar se o HTML e o VERSION divergirem.

**Antes de chamar de release de verdade:** o Android ainda assina com a chave de
debug. Serve para instalar no aparelho do usuário e no emulador, não para
distribuir. E trocar de chave depois força desinstalar/reinstalar — o que apaga
as fotos de capa em `Documents/capas/`.

## O Windows virou app nativo (10/09/2026)

Até a v1.8.2 o Windows rodava o `biblioteca.html` no Chrome, aberto por um
`.vbs`, e o usuário vinculava o arquivo à mão pelo seletor — com a permissão
caducando a cada reinício. Desde a v1.8.3 o Windows roda o **app Tauri**, que
acha sozinho `C:\Users\<voce>\iCloudDrive\Biblioteca\`, como o Mac faz.

- O HTML vai **embutido no executável** — não é mais instalado à parte.
- `./bin/compilar-windows.sh` compila na VM e gera o instalador NSIS.
- `motor-web/tauri/src/index.html` é link simbólico para o motor; links
  simbólicos não atravessam para o Windows, então o script materializa o
  arquivo na cópia (`cp -L`).
- **Sem `vcvarsall.bat arm64` o build falha:** o `cc-rs` sai procurando `clang`
  em vez do `cl.exe`.
- O app aberto segura o `.exe` e o `cargo` não relinka ("Access is denied") —
  o script fecha o app antes de compilar.

## Convenções de código

- Nomes de funções, variáveis e comentários em português, como no código existente.
- iOS: arquivos `.swift` novos em `motor-movel/ios/Biblioteca.App/` entram na
  compilação sozinhos (Xcode 16 synchronized groups). Não edite `project.pbxproj`.
- A divisão iOS/Flutter é deliberada, não um acidente a corrigir: a captura de
  capa do iOS usa o framework Vision da Apple, sem equivalente em Dart. O
  Flutter atende o Android.

## Pendências conhecidas

- `motor-movel/android/test/widget_test.dart` referencia uma classe `MyApp` que
  não existe — sobra do template do Flutter. É o único erro do `flutter analyze`.
- O release Android ainda assina com a chave de debug (`android/app/build.gradle.kts`
  tem o TODO padrão). Antes de publicar, configure uma chave de verdade.
- `motor-movel/ios` tem repositório git local com um único commit e muito
  trabalho não commitado; `motor-movel/android` tem remoto em
  `ruggierow/biblioteca-flutter`. O restante da árvore não está sob git.

## Pegadinha do ambiente

Esta máquina tem dois *homes*. O código vive em `/Users/wilson-16-06-2022/`;
o iCloud, o Xcode e o DerivedData, em `/Users/wilson/`. O shell roda como `wilson`.

O `biblioteca.txt` de verdade fica em
`~/Library/Mobile Documents/com~apple~CloudDocs/Biblioteca/biblioteca.txt`.
O `motor-web/biblioteca.txt` do repositório é só um exemplo de desenvolvimento.
