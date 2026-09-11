#!/bin/bash
# Gera os pacotes de distribuicao do motor web em dist/ e copia para o Desktop.
#
# NAO rode ao mesmo tempo que ./bin/arquivar-ios.sh — ver o aviso la.
#
# Mac  → compila, assina, notariza e empacota num .dmg pronto para distribuicao.
# Win  → distribui o instalador do app nativo (Tauri), gerado antes por
#        ./bin/compilar-windows.sh. O HTML vai embutido no executavel.
#
# Prerequisito (uma vez so):
#   xcrun notarytool store-credentials "biblioteca-notarize" \
#       --apple-id SEU@EMAIL.COM --team-id Q87ANATBD3 --password APP-SPECIFIC-PASSWORD
set -e
RAIZ="$(cd "$(dirname "$0")/.." && pwd)"
V="$(tr -d '[:space:]' < "$RAIZ/VERSION")"
MOTOR="$RAIZ/motor-web/biblioteca.html"
DIST="$RAIZ/dist"
DESKTOP_PASTA="$HOME/Desktop/Biblioteca-Web"
DOCS="$RAIZ/docs"

CERT="Developer ID Application: WILSON VICENTE RUGGIERO (Q87ANATBD3)"
ENTITLEMENTS="$RAIZ/motor-web/macos/Sources/BibliotecaMacWeb/BibliotecaMacWeb.entitlements"
NOTARIZE_PROFILE="biblioteca-notarize"

if [ ! -f "$MOTOR" ]; then echo "motor-web/biblioteca.html nao encontrado."; exit 1; fi

NA_TELA="$(grep -o 'v\.[0-9]*\.[0-9]*\.[0-9]*' "$MOTOR" | head -1 | cut -c3-)"
if [ "$NA_TELA" != "$V" ]; then
    echo "AVISO: o HTML mostra $NA_TELA e VERSION diz $V. Rode ./bin/versionar.sh primeiro."
    exit 1
fi

rm -rf "$DIST"
mkdir -p "$DIST"

# ---------------------------------------------------------------
# Pacote Mac — compila, assina, cria DMG, notariza, staple
# ---------------------------------------------------------------
MACOS_DIR="$RAIZ/motor-web/macos"
BUILD_DIR="$MACOS_DIR/build"
APP="$BUILD_DIR/Release/Biblioteca Web.app"
DMG_OUT="$DIST/Biblioteca-Mac-v$V.dmg"

echo "Compilando app macOS..."
cd "$MACOS_DIR"
xcodebuild -project Biblioteca-Mac.xcodeproj -scheme BibliotecaWeb \
    -configuration Release \
    BUILD_DIR="$BUILD_DIR" \
    CODE_SIGN_IDENTITY="$CERT" \
    CODE_SIGN_STYLE=Manual \
    DEVELOPMENT_TEAM=Q87ANATBD3 \
    OTHER_CODE_SIGN_FLAGS="--options=runtime --entitlements=$ENTITLEMENTS" \
    build -quiet
echo "  App compilado: $(du -sh "$APP" | cut -f1)"

echo "Assinando app..."
codesign --force --deep --sign "$CERT" \
    --entitlements "$ENTITLEMENTS" \
    --options runtime \
    "$APP"
codesign --verify --deep --strict "$APP" && echo "  Assinatura OK"

echo "Gerando DMG..."
TMPDIR_DMG="$(mktemp -d)"
cp -R "$APP" "$TMPDIR_DMG/"
ln -s /Applications "$TMPDIR_DMG/Applications"
# Inclui o manual (HTML + PDF) no DMG
cp "$DOCS/manual-mac.html" "$TMPDIR_DMG/Manual.html"
cp "$DOCS/manual-mac.pdf"  "$TMPDIR_DMG/Manual.pdf"
hdiutil create \
    -volname "Biblioteca" \
    -srcfolder "$TMPDIR_DMG" \
    -ov -format UDZO \
    -quiet \
    -o "$DMG_OUT"
rm -rf "$TMPDIR_DMG"

echo "Assinando DMG..."
codesign --sign "$CERT" "$DMG_OUT"

# Notariza se o perfil estiver configurado; pula com aviso se nao estiver.
if xcrun notarytool history --keychain-profile "$NOTARIZE_PROFILE" &>/dev/null; then
    echo "Notarizando DMG (pode levar alguns minutos)..."
    xcrun notarytool submit "$DMG_OUT" \
        --keychain-profile "$NOTARIZE_PROFILE" \
        --wait
    echo "Aplicando staple..."
    xcrun stapler staple "$DMG_OUT"
    echo "  dist/Biblioteca-Mac-v$V.dmg — assinado, notarizado e com staple ✓"
else
    echo "  AVISO: perfil '$NOTARIZE_PROFILE' nao configurado — DMG sem notarizacao."
    echo "  Para configurar, rode:"
    echo "    xcrun notarytool store-credentials '$NOTARIZE_PROFILE' \\"
    echo "        --apple-id SEU@EMAIL.COM --team-id Q87ANATBD3 --password APP-SPECIFIC-PASSWORD"
    echo "  dist/Biblioteca-Mac-v$V.dmg ($(du -sh "$DMG_OUT" | cut -f1)) — apenas assinado"
fi

# ---------------------------------------------------------------
# Pacote Windows — o instalador do app nativo (Tauri)
#
# Desde a v1.8.3 o Windows entrega UM arquivo: o instalador. O HTML vai
# embutido no executavel, e os launchers de navegador sairam de circulacao.
# Quem gera o instalador e ./bin/compilar-windows.sh, que compila na VM
# Parallels — aqui so conferimos e distribuimos.
# ---------------------------------------------------------------
cd "$RAIZ"
WINDIR="$RAIZ/motor-web/windows"
SETUP="$WINDIR/Biblioteca-$V-setup.exe"

if [ ! -f "$SETUP" ]; then
    echo
    echo "FALTA o instalador do Windows para a versao $V."
    echo "Rode primeiro:  ./bin/compilar-windows.sh"
    echo "(precisa da VM 'Windows 11' ligada no Parallels)"
    exit 1
fi

cp "$SETUP" "$DIST/"
echo "  dist/$(basename "$SETUP") ($(du -h "$SETUP" | cut -f1))"

# ---------------------------------------------------------------
# Copia para o Desktop
# ---------------------------------------------------------------
mkdir -p "$DESKTOP_PASTA"
cp "$DMG_OUT"                              "$DESKTOP_PASTA/"
cp "$SETUP"                                "$DESKTOP_PASTA/"

echo
echo "Pacotes copiados para:"
echo "  $DESKTOP_PASTA/"
echo
echo "Mac:     Biblioteca-Mac-v$V.dmg"
echo "Windows: Biblioteca-$V-setup.exe (app nativo; o HTML vai dentro dele)"
echo
echo "O APK Android (motor-movel/android/) e gerado pelo Flutter, nao aqui."
