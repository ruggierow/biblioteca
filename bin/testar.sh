#!/bin/bash
# Roda a regressao da Biblioteca.
#
#   ./bin/testar.sh          rapido (~30 s): ponte, motor-web e Android
#   ./bin/testar.sh --tudo   acrescenta o iPhone, que precisa do simulador
#
# SAO DUAS FAMILIAS DE DEFEITO, E CADA UMA PRECISA DO SEU TESTE:
#
#   LOGICA   — "o botao parou de responder", "o filtro traz o livro errado".
#              Pega-se exercitando a pagina num navegador (motor-web/testes).
#
#   CONTRATO — "funciona na mesa e NAO faz nada no aparelho". NAO se pega
#              exercitando a tela; pega-se comparando o que o codigo USA com o
#              que o ambiente OFERECE. Sao dois portoes, um por fronteira:
#
#                conferir-ponte.py      Mac e Windows: a pagina x o hospedeiro.
#                                       No navegador o `confirm()` funciona, o
#                                       `window.print()` existe, o
#                                       `target="_blank"` abre — no WKWebView,
#                                       nenhum dos tres.
#
#                conferir-celulares.py  iPhone e Android: o codigo x o que o
#                                       app DECLARA ao sistema. Sem o esquema
#                                       em <queries>, o Android 11+ nao abre o
#                                       Kindle e nao avisa; sem a chave de
#                                       camera, o iPhone DERRUBA o aplicativo.
#
# Em 12/10/2026 o Remover nao fazia nada no Mac por falta do WKUIDelegate. Uma
# suite de navegador teria passado com louvor. Por isso as duas rodam juntas.
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

TUDO=0
[ "${1:-}" = "--tudo" ] && TUDO=1

falhou=0
secao() { printf '\n\033[1m== %s ==\033[0m\n' "$1"; }
resultado() {   # <codigo> <nome>
    if [ "$1" -eq 0 ]; then printf '   \033[32mOK\033[0m   %s\n' "$2"
    else printf '   \033[31mFALHOU\033[0m  %s\n' "$2"; falhou=1; fi
}

secao "Contrato com os hospedeiros (Mac e Windows)"
python3 -I bin/conferir-ponte.py; resultado $? "conferir-ponte.py"

secao "Declaracoes ao sistema (iPhone e Android)"
python3 -I bin/conferir-celulares.py; resultado $? "conferir-celulares.py"

secao "motor-web — a pagina que o Mac e o Windows embarcam"
if [ -d motor-web/testes/node_modules ]; then
    (cd motor-web/testes && npx playwright test --reporter=line 2>&1 | tail -20)
    resultado "${PIPESTATUS[0]:-$?}" "testes do motor-web"
else
    echo "   (pulado: rode  cd motor-web/testes && npm install && npx playwright install chromium)"
fi

secao "Android"
if command -v flutter >/dev/null || [ -x "$HOME/development/flutter/bin/flutter" ]; then
    PATH="$PATH:$HOME/development/flutter/bin"
    (cd motor-movel/android && flutter test 2>&1 | tail -4)
    resultado "${PIPESTATUS[0]:-$?}" "flutter test"
else
    echo "   (pulado: flutter nao encontrado)"
fi

if [ "$TUDO" -eq 1 ]; then
    secao "iPhone (precisa do simulador; demora alguns minutos)"
    SIM=$(xcrun simctl list devices available 2>/dev/null | grep -m1 -oE '[0-9A-F-]{36}')
    if [ -n "$SIM" ]; then
        (cd motor-movel/ios && xcodebuild test -project Biblioteca-iPhone.xcodeproj \
            -scheme Biblioteca.App -destination "id=$SIM" 2>&1 | grep -E 'Executed|TEST (SUCCEEDED|FAILED)' | tail -3)
        resultado "${PIPESTATUS[0]:-$?}" "xcodebuild test"
    else
        echo "   (pulado: nenhum simulador disponivel)"
    fi
else
    printf '\n(o iPhone so roda com --tudo)\n'
fi

printf '\n'
if [ "$falhou" -eq 0 ]; then printf '\033[32mTudo verde.\033[0m\n'; else printf '\033[31mHa falha acima.\033[0m\n'; fi
exit "$falhou"
