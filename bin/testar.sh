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
#                conferir-espera-ios.py a espera pela build do iPhone: ausencia
#                                       na API e processamento, nao falha de
#                                       envio — com consulta, relogio e sono
#                                       de mentira, sem rede.
#
#                conferir-audible.py    o caminho do Audible: o vigia (banco
#                                       velho nunca vira "nada novo") e as
#                                       regras de quem entra na base — com
#                                       biblioteca de mentira, sem rede.
#
#                conferir-espelho.py    o guarda que roda ANTES de espelhar. A
#                                       identidade titulo+autores NAO e unica:
#                                       o mesmo livro pode estar como impresso
#                                       e como Kindle. Comparar por conjunto
#                                       engolia um dos dois, e um livro novo
#                                       do celular era anunciado como "so
#                                       alterado" e NAO era trazido.
#
#                conferir-vigia-loja.py o vigia das lojas, na parte da Play. A
#                                       Apple muda de estado sozinha; a Play
#                                       nao. Em 08/11/2026 a 1.9.20 nao foi
#                                       enviada e nos quatro dias seguintes
#                                       NADA MUDOU la — um vigia de mudanca
#                                       calaria com razao. Por isso ele
#                                       pergunta tambem se a versao do
#                                       repositorio esta liberada, e este
#                                       portao exercita essa pergunta com
#                                       relogio e loja de mentira.
#
#                conferir-paises.py     a MESMA tabela escrita a mao em quatro
#                                       linguagens. Em 13/10/2026, 22 dos 47
#                                       nomes do motor-web estavam sem acento:
#                                       "Mocambique" no Mac, "Moçambique" no
#                                       iPhone. Nada quebrava.
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

secao "O portugues da tela — acento que falta e acento que varia"
python3 -I bin/conferir-acentos.py; resultado $? "conferir-acentos.py"

secao "Tabela de paises nas quatro"
python3 -I bin/conferir-paises.py; resultado $? "conferir-paises.py"

secao "Vigia do Kindle — silencio e conclusao, nao desistencia"
python3 -I bin/conferir-vigia.py; resultado $? "conferir-vigia.py"

secao "Vigia das lojas — na Play, parado nao e igual a certo"
python3 -I bin/conferir-vigia-loja.py; resultado $? "conferir-vigia-loja.py"

secao "Guarda do espelho — contar as edicoes, nao so reconhece-las"
python3 -I bin/conferir-espelho.py; resultado $? "conferir-espelho.py"

python3 -I bin/conferir-audible.py; resultado $? "conferir-audible.py"

python3 -I bin/conferir-espera-ios.py; resultado $? "conferir-espera-ios.py"

secao "A pagina do app — nao pode ficar atras da versao"
python3 -I bin/conferir-pagina.py; resultado $? "conferir-pagina.py"

secao "motor-web — a pagina que o Mac e o Windows embarcam"
if [ -d motor-web/testes/node_modules ]; then
    (cd motor-web/testes && npx playwright test --reporter=line 2>&1 | tail -20)
    resultado "${PIPESTATUS[0]:-$?}" "testes do motor-web"
else
    echo "   (pulado: rode  cd motor-web/testes && npm install && npx playwright install chromium)"
fi

secao "Mac — as duas funcoes do Selecionar pasta que mexem em arquivo"
# A pagina ja e medida acima, nos dois hospedeiros. O que falta e o lado SWIFT:
# `olharAPasta` e `criarArquivoNaPasta`, que sao as unicas partes do fluxo
# capazes de perder a biblioteca de alguem. O par delas no Windows roda na VM
# com `cargo test`.
if command -v swift >/dev/null; then
    (cd motor-web/macos && swift test 2>&1 | grep -E "Executed [0-9]+ tests, with" | tail -1)
    resultado "${PIPESTATUS[0]:-$?}" "swift test"
else
    echo "   (pulado: swift nao encontrado)"
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
