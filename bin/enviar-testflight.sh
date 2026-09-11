#!/bin/bash
# Envia o .ipa do iPhone para o TestFlight.
#
#   ./bin/enviar-testflight.sh
#
# PREREQUISITO (uma vez so): a chave de API do App Store Connect.
#
#   1. A chave e um arquivo AuthKey_XXXXXXXXXX.p8, onde XXXXXXXXXX e o Key ID.
#      Guarde-a em  ~/.appstoreconnect/private_keys/  com o nome original.
#      A Apple so deixa baixar a chave UMA vez — se esta for a unica copia,
#      guarde um backup fora do Mac antes.
#
#   2. O Issuer ID e um UUID que aparece em App Store Connect >
#      Usuarios e Acesso > Integracoes > Chaves de API, no topo da pagina.
#      Grave-o em  ~/.appstoreconnect/issuer_id  (uma linha).
#
# O script deduz o Key ID pelo nome do arquivo — nenhuma senha e digitada.
set -euo pipefail

RAIZ="$(cd "$(dirname "$0")/.." && pwd)"
V="$(cat "$RAIZ/VERSION")"
IPA="${1:-}"

if [ -z "$IPA" ]; then
    IPA="$RAIZ/dist/Biblioteca-iOS-v$V.ipa"
fi
[ -f "$IPA" ] || { echo "Nao achei o .ipa: $IPA"; echo "Gere-o com ./bin/arquivar-ios.sh"; exit 1; }

PASTA_CHAVES="$HOME/.appstoreconnect/private_keys"
CHAVE="$(ls "$PASTA_CHAVES"/AuthKey_*.p8 2>/dev/null | head -1 || true)"
if [ -z "$CHAVE" ]; then
    echo "Nenhuma chave em $PASTA_CHAVES/"
    echo "Coloque ali o arquivo AuthKey_XXXXXXXXXX.p8 e rode de novo."
    exit 1
fi
KEY_ID="$(basename "$CHAVE" .p8)"; KEY_ID="${KEY_ID#AuthKey_}"

ARQ_ISSUER="$HOME/.appstoreconnect/issuer_id"
[ -f "$ARQ_ISSUER" ] || { echo "Falta o Issuer ID em $ARQ_ISSUER"; exit 1; }
ISSUER="$(tr -d '[:space:]' < "$ARQ_ISSUER")"

echo "Pacote:   $(basename "$IPA")  ($(du -h "$IPA" | cut -f1))"
echo "Key ID:   $KEY_ID"
echo

echo "Validando antes de enviar..."
xcrun altool --validate-app -f "$IPA" -t ios \
    --apiKey "$KEY_ID" --apiIssuer "$ISSUER"

echo
echo "Enviando (alguns minutos)..."
xcrun altool --upload-app -f "$IPA" -t ios \
    --apiKey "$KEY_ID" --apiIssuer "$ISSUER"

echo
echo "Enviado. O build leva 5 a 15 minutos processando antes de aparecer"
echo "em App Store Connect > TestFlight. Depois disso:"
echo "  - testadores internos (ate 100, precisam estar na equipe): liberam na hora;"
echo "  - testadores externos (ate 10.000, basta o e-mail): o PRIMEIRO build"
echo "    passa por Beta App Review, cerca de um dia. Os seguintes sao diretos."
