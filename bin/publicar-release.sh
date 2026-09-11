#!/bin/bash
# Publica os instaladores como Release no GitHub, em ruggierow/biblioteca.
#
#   ./bin/publicar-release.sh
#
# Rode DEPOIS de ./bin/compilar-windows.sh, ./bin/empacotar.sh e do APK.
#
# Cada arquivo sobe DUAS vezes, com nomes diferentes, de proposito:
#
#   Biblioteca-Mac-v1.9.0.dmg   -> historico: diz exatamente que versao e
#   Biblioteca-Mac.dmg          -> nome fixo, sem versao
#
# O nome fixo existe porque o GitHub serve a release mais recente em
#   https://github.com/<dono>/<repo>/releases/latest/download/<nome>
# e esse endereco so funciona se o nome NAO mudar entre releases. E por ele que
# a pagina dos testadores aponta — assim ela nunca precisa ser reeditada: basta
# publicar a release nova e os botoes passam a servir a versao nova sozinhos.
#
# O custo e duplicar os bytes no GitHub. Para 68 MB por release, e barato perto
# de reeditar a pagina (e reavisar os testadores) toda vez.
set -euo pipefail

RAIZ="$(cd "$(dirname "$0")/.." && pwd)"
V="$(tr -d '[:space:]' < "$RAIZ/VERSION")"
REPO="ruggierow/biblioteca"
DIST="$RAIZ/dist"
DESKTOP="$HOME/Desktop/Biblioteca-Web"
TRAB="$(mktemp -d)"; trap 'rm -rf "$TRAB"' EXIT

# origem → nome fixo que a pagina usa
achar() { [ -f "$1" ] && echo "$1" || { [ -f "$2" ] && echo "$2"; }; }

MAC="$(achar "$DIST/Biblioteca-Mac-v$V.dmg" "$DESKTOP/Biblioteca-Mac-v$V.dmg")"
WIN="$(achar "$DIST/Biblioteca-$V-setup.exe" "$DESKTOP/Biblioteca-$V-setup.exe")"
APK="$(ls "$DESKTOP"/Biblioteca-Android-"$V"-b*.apk 2>/dev/null | sort -V | tail -1 || true)"

faltou=0
for par in "Mac:$MAC" "Windows:$WIN" "Android:$APK"; do
    nome="${par%%:*}"; arq="${par#*:}"
    if [ -z "$arq" ] || [ ! -f "$arq" ]; then
        echo "FALTA o pacote do $nome para a versao $V"; faltou=1
    else
        echo "  $nome: $(basename "$arq")  ($(du -h "$arq" | cut -f1))"
    fi
done
[ "$faltou" -eq 0 ] || { echo; echo "Gere os pacotes que faltam antes de publicar."; exit 1; }

cp "$MAC" "$TRAB/Biblioteca-Mac.dmg"
cp "$WIN" "$TRAB/Biblioteca-Windows-setup.exe"
cp "$APK" "$TRAB/Biblioteca-Android.apk"

NOTAS="$RAIZ/docs/notas-$V.md"
[ -f "$NOTAS" ] || { echo "Escreva as notas em docs/notas-$V.md antes de publicar."; exit 1; }

git -C "$RAIZ" rev-parse "v$V" >/dev/null 2>&1 \
    || { echo "A tag v$V nao existe. Crie-a antes: git tag -a v$V"; exit 1; }

echo
if gh release view "v$V" --repo "$REPO" >/dev/null 2>&1; then
    echo "Release v$V ja existe — atualizando os anexos..."
    gh release upload "v$V" --repo "$REPO" --clobber \
        "$MAC" "$WIN" "$APK" \
        "$TRAB/Biblioteca-Mac.dmg" "$TRAB/Biblioteca-Windows-setup.exe" "$TRAB/Biblioteca-Android.apk"
else
    echo "Criando a release v$V..."
    gh release create "v$V" --repo "$REPO" \
        --title "Biblioteca $V" --notes-file "$NOTAS" \
        "$MAC" "$WIN" "$APK" \
        "$TRAB/Biblioteca-Mac.dmg" "$TRAB/Biblioteca-Windows-setup.exe" "$TRAB/Biblioteca-Android.apk"
fi

echo
echo "Conferindo os enderecos que a pagina dos testadores usa..."
ok=1
for f in Biblioteca-Mac.dmg Biblioteca-Windows-setup.exe Biblioteca-Android.apk; do
    u="https://github.com/$REPO/releases/latest/download/$f"
    c="$(curl -sIL -o /dev/null -w '%{http_code}' "$u")"
    echo "  $c  $f"
    [ "$c" = "200" ] || ok=0
done
[ "$ok" -eq 1 ] && echo && echo "Pronto. A pagina dos testadores ja serve a $V, sem precisar ser editada."
