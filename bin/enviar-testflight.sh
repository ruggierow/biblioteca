#!/bin/bash
# Envia o .ipa do iPhone para o TestFlight.
#
#   ./bin/enviar-testflight.sh
#
# Ha DOIS jeitos de autenticar. O script usa o que estiver configurado.
#
# --- Caminho A: senha especifica de app (mais simples) -----------------
# Guarde a senha no chaveiro UMA vez (voce digita, o script nunca ve):
#
#   xcrun altool --store-password-in-keychain-item BIBLIOTECA_ALTOOL \
#       -u SEU@EMAIL.COM -p SUA-SENHA-DE-APP
#
# e grave o seu Apple ID em  ~/.appstoreconnect/apple_id  (uma linha).
# A senha de app sai de appleid.apple.com > Iniciar Sessao e Seguranca.
# Dali em diante o script passa "@keychain:BIBLIOTECA_ALTOOL" ao altool —
# a senha nao aparece em linha de comando, log, nem historico do shell.
#
# --- Caminho B: chave de API do App Store Connect ----------------------
# Um arquivo AuthKey_XXXXXXXXXX.p8 (os 10 caracteres sao o Key ID), baixado
# de App Store Connect > Usuarios e Acesso > Integracoes. E um arquivo, nao
# um texto para digitar, e a Apple so deixa baixa-lo uma vez.
#
#   ~/.appstoreconnect/private_keys/AuthKey_XXXXXXXXXX.p8
#   ~/.appstoreconnect/issuer_id       (o UUID da mesma pagina)
#
# CUIDADO: senha de app tem o formato xxxx-xxxx-xxxx-xxxx e NAO e a chave.
# Um .p8 comeca com "-----BEGIN PRIVATE KEY-----" e tem ~250 bytes.
set -euo pipefail

RAIZ="$(cd "$(dirname "$0")/.." && pwd)"
V="$(cat "$RAIZ/VERSION")"
D="$HOME/.appstoreconnect"
IPA="${1:-$RAIZ/dist/Biblioteca-iOS-v$V.ipa}"

[ -f "$IPA" ] || { echo "Nao achei o .ipa: $IPA"; echo "Gere-o com ./bin/arquivar-ios.sh"; exit 1; }

CRED=()
CHAVE="$(ls "$D"/private_keys/AuthKey_*.p8 2>/dev/null | head -1 || true)"

if [ -n "$CHAVE" ] && openssl pkey -in "$CHAVE" -noout 2>/dev/null; then
    [ -f "$D/issuer_id" ] || { echo "Achei a chave mas falta o Issuer ID em $D/issuer_id"; exit 1; }
    KID="$(basename "$CHAVE" .p8)"; KID="${KID#AuthKey_}"
    CRED=(--apiKey "$KID" --apiIssuer "$(tr -d '[:space:]' < "$D/issuer_id")")
    echo "Autenticando pela chave de API (Key ID $KID)."
elif security find-generic-password -l BIBLIOTECA_ALTOOL >/dev/null 2>&1; then
    [ -f "$D/apple_id" ] || { echo "Falta o seu Apple ID em $D/apple_id (uma linha)"; exit 1; }
    CRED=(-u "$(tr -d '[:space:]' < "$D/apple_id")" -p "@keychain:BIBLIOTECA_ALTOOL")
    echo "Autenticando pela senha especifica de app guardada no chaveiro."
else
    echo "Nenhuma credencial configurada. Escolha um dos dois caminhos"
    echo "descritos no cabecalho deste script:"
    echo "  A) senha especifica de app  -> mais simples, use esta se estiver na duvida"
    echo "  B) chave de API .p8         -> arquivo baixado do App Store Connect"
    [ -n "$CHAVE" ] && echo && echo "(havia um $(basename "$CHAVE") em private_keys/, mas o openssl o recusou:" && echo " nao e uma chave privada valida.)"
    exit 1
fi

echo "Pacote: $(basename "$IPA")  ($(du -h "$IPA" | cut -f1))"
echo
echo "Validando antes de enviar..."
xcrun altool --validate-app -f "$IPA" -t ios "${CRED[@]}"
echo
echo "Enviando (alguns minutos)..."
xcrun altool --upload-app -f "$IPA" -t ios "${CRED[@]}"
echo
echo "Enviado. O build leva 5 a 15 minutos processando antes de aparecer em"
echo "App Store Connect > TestFlight. Depois disso:"
echo "  - testadores internos (ate 100, precisam estar na equipe): liberam na hora;"
echo "  - testadores externos (ate 10.000, basta o e-mail): o PRIMEIRO build passa"
echo "    por Beta App Review, cerca de um dia. Os seguintes sao diretos."
