#!/bin/bash
# Espelha a base do iCloud para as nuvens que o celular enxerga.
#
#   ./bin/espelhar.sh
#
# POR QUE ISTO EXISTE: o Mac grava no iCloud e o ANDROID NAO LE ICLOUD. Entao o
# celular vincula uma pasta de outra nuvem, e alguem precisa copiar. Quando essa
# copia e feita a mao, uma hora ela sai na direcao errada e o arquivo VELHO cai
# por cima do novo — aconteceu em 07/10/2026 e custou 291 capas (recuperadas de
# Backups/). Este comando copia SEMPRE na mesma direcao: iCloud -> nuvens.
#
# Ele NAO le de volta — mas AGORA SE RECUSA a copiar por cima do que so existe
# no destino. O Android ESCREVE na copia do Drive (e a pasta que ele vincula),
# entao o que voce cadastra no celular vive so la ate alguem trazer. Em
# 10/10/2026 uma leitura de codigo de barras no Samsung existia so no Drive:
# espelhar naquele momento a teria apagado, em silencio.
#
#   ./bin/espelhar.sh            recusa e diz o que ha de novo no destino
#   ./bin/espelhar.sh --trazer   traz para a origem e ai espelha
#   ./bin/espelhar.sh --forcar   copia por cima assim mesmo
#
# `--forcar` existe porque o portao NAO distingue "apagado de proposito" de
# "criado no celular": os dois aparecem como linha que o destino tem e a origem
# nao. Quando VOCE editou ou removeu algo na base, o certo e forcar. Quando a
# novidade veio do aparelho, o certo e --trazer. O comando mostra as linhas
# para voce decidir qual dos dois e o caso.
set -euo pipefail

TRAZER=""; FORCAR=0
case "${1:-}" in
    --trazer) TRAZER="--trazer" ;;
    --forcar) FORCAR=1 ;;
    "")       ;;
    *)        echo "uso: $0 [--trazer|--forcar]"; exit 2 ;;
esac
CONFERIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/conferir_destino.py"

ORIGEM="$HOME/Library/Mobile Documents/com~apple~CloudDocs/Biblioteca"
ARQUIVOS=(biblioteca.txt biblioteca.dat grupos.json biblioteca-removidas.json)

# Destinos possiveis. O do Drive so existe com o "Google Drive para computador"
# instalado; sem ele a pasta nao aparece e o destino e pulado com aviso.
DESTINOS=(
    "$HOME/Library/CloudStorage/OneDrive-Personal/Biblioteca"
)
# No Drive a pasta pode ter qualquer nome e estar em qualquer lugar — o que
# manda e onde o CELULAR vinculou. Entao procuramos a pasta que JA TEM um
# biblioteca.txt dentro, ate 4 niveis abaixo da raiz do Drive; so se nao houver
# nenhuma e que caimos no nome convencional.
for raiz in "$HOME/Library/CloudStorage/"GoogleDrive-*; do
    [ -d "$raiz" ] || continue
    encontrou=0
    while IFS= read -r achado; do
        DESTINOS+=("$(dirname "$achado")"); encontrou=1
    done < <(find "$raiz" -maxdepth 5 -name biblioteca.txt -not -path '*/.*' 2>/dev/null)
    if [ "$encontrou" -eq 0 ]; then
        for sub in "$raiz/Meu Drive/Biblioteca" "$raiz/My Drive/Biblioteca"; do
            [ -d "$sub" ] && DESTINOS+=("$sub")
        done
    fi
done

echo "origem: $ORIGEM"
achou_drive=0
recusou=0
for destino in "${DESTINOS[@]}"; do
    case "$destino" in *GoogleDrive-*) achou_drive=1 ;; esac
    echo
    echo "-> $destino"
    for arq in "${ARQUIVOS[@]}"; do
        [ -f "$ORIGEM/$arq" ] || { echo "   $arq: nao existe na origem, pulado"; continue; }
        if cmp -s "$ORIGEM/$arq" "$destino/$arq"; then
            echo "   $arq: ja igual"
            continue
        fi
        # O portao: o destino tem algo que a origem nao tem? Entao copiar por
        # cima APAGA. Melhor parar e dizer o que e.
        if [ -f "$destino/$arq" ] && [ "$FORCAR" -eq 0 ]; then
            echo "   $arq: conferindo o destino…"
            if ! python3 -I "$CONFERIR" "$ORIGEM/$arq" "$destino/$arq" $TRAZER; then
                echo "   $arq: RECUSADO — copiar apagaria o que esta acima."
                echo "      Veio do celular?  rode com --trazer"
                echo "      Voce apagou/editou na base?  rode com --forcar"
                recusou=1
                continue
            fi
        fi
        cp "$ORIGEM/$arq" "$destino/$arq"
        # conferir DEPOIS de copiar: copia que nao bate e pior que copia nenhuma
        if cmp -s "$ORIGEM/$arq" "$destino/$arq"; then
            echo "   $arq: copiado ($(du -h "$destino/$arq" | cut -f1))"
        else
            echo "   $arq: FALHOU a conferencia"; exit 1
        fi
    done
done

if [ "$recusou" -ne 0 ]; then
    echo
    echo "NADA foi espelhado para os arquivos recusados: o destino tinha coisa"
    echo "que a origem nao tem, e a copia teria apagado. Traga com --trazer."
fi

if [ "$achou_drive" -eq 0 ]; then
    echo
    echo "AVISO: nenhuma pasta do Google Drive encontrada — e e o Drive que o"
    echo "celular le. Instale o \"Google Drive para computador\" e deixe a pasta"
    echo "Biblioteca sincronizada, ou o Samsung continuara vendo a base velha."
fi
