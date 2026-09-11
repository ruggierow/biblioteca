#!/bin/bash
# Gera o .ipa do iPhone assinado para distribuicao, em dist/.
#
#   ./bin/arquivar-ios.sh
#
# Depois, para mandar ao TestFlight:  ./bin/enviar-testflight.sh
#
# Por que "clean archive" e nao so "archive": um xcodebuild interrompido deixa
# o produto marcado como atualizado, e o Xcode PULA a etapa de assinatura na
# proxima vez. Ja aconteceu aqui — um app sem assinatura foi parar em
# /Applications. O clean e barato perto disso.
set -euo pipefail

RAIZ="$(cd "$(dirname "$0")/.." && pwd)"
V="$(cat "$RAIZ/VERSION")"
PROJ="$RAIZ/motor-movel/ios"
DIST="$RAIZ/dist"; mkdir -p "$DIST"
TRAB="$(mktemp -d)"; trap 'rm -rf "$TRAB"' EXIT

TIME="Q87ANATBD3"   # o time que tem o certificado Apple Distribution

echo "Arquivando Biblioteca $V para iOS..."
xcodebuild clean archive \
    -project "$PROJ/Biblioteca-iPhone.xcodeproj" \
    -scheme Biblioteca.App \
    -configuration Release \
    -destination "generic/platform=iOS" \
    -archivePath "$TRAB/Biblioteca.xcarchive" \
    -allowProvisioningUpdates \
    CODE_SIGN_STYLE=Automatic DEVELOPMENT_TEAM="$TIME" \
    > "$TRAB/archive.log" 2>&1 \
  || { echo "Falhou. Ultimas linhas:"; tail -30 "$TRAB/archive.log"; exit 1; }

cat > "$TRAB/ExportOptions.plist" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
	<key>method</key><string>app-store-connect</string>
	<key>teamID</key><string>$TIME</string>
	<key>uploadSymbols</key><true/>
	<key>signingStyle</key><string>automatic</string>
	<key>destination</key><string>export</string>
</dict>
</plist>
PLIST

echo "Exportando com assinatura de distribuicao..."
xcodebuild -exportArchive \
    -archivePath "$TRAB/Biblioteca.xcarchive" \
    -exportOptionsPlist "$TRAB/ExportOptions.plist" \
    -exportPath "$TRAB/export" \
    -allowProvisioningUpdates \
    > "$TRAB/export.log" 2>&1 \
  || { echo "Falhou. Ultimas linhas:"; tail -30 "$TRAB/export.log"; exit 1; }

IPA="$DIST/Biblioteca-iOS-v$V.ipa"
cp "$TRAB/export/Biblioteca.App.ipa" "$IPA"

# Conferencia: um .ipa assinado em desenvolvimento e aceito pelo xcodebuild e
# recusado la na frente pela Apple, com mensagem obscura. Melhor pegar aqui.
cd "$TRAB" && unzip -q "$IPA" -d conf
AUT="$(codesign -dvvv conf/Payload/Biblioteca.App.app 2>&1 | grep -m1 "^Authority=" | sed 's/Authority=//')"
security cms -D -i conf/Payload/Biblioteca.App.app/embedded.mobileprovision > conf/perfil.plist 2>/dev/null
GTA="$(/usr/libexec/PlistBuddy -c "Print :Entitlements:get-task-allow" conf/perfil.plist 2>/dev/null || echo "?")"
BETA="$(/usr/libexec/PlistBuddy -c "Print :Entitlements:beta-reports-active" conf/perfil.plist 2>/dev/null || echo ausente)"

echo
echo "Pronto: dist/$(basename "$IPA")  ($(du -h "$IPA" | cut -f1))"
echo "  assinatura:          $AUT"
echo "  get-task-allow:      $GTA        (tem de ser false)"
echo "  beta-reports-active: $BETA     (e o que habilita o TestFlight)"
case "$AUT" in
    "Apple Distribution"*) ;;
    *) echo; echo "ATENCAO: nao saiu assinado como Apple Distribution."; exit 1;;
esac
[ "$GTA" = "false" ] || { echo; echo "ATENCAO: get-task-allow deveria ser false."; exit 1; }
