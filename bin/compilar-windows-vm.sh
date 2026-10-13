#!/bin/bash
# Leva os fontes E CONFERE antes de compilar. Na 1.9.6 eu montei este script a
# partir do da tentativa anterior, que nao copiava fonte nenhuma: a VM compilou
# o codigo de ontem e o instalador saiu com o nome novo e o conteudo velho.
set -eu
# A VERSAO VEM DO ARQUIVO, nunca escrita aqui. Ate 13/10/2026 ela estava fixa
# no codigo, e uma montagem de versao nova com o numero velho e exatamente o
# defeito que este script existe para impedir.
V="$(tr -d '[:space:]' < "$(dirname "$0")/../VERSION")"
S='\\Mac\Documents-old\RISK-V-CLAUDE\RISK-Claude\Biblioteca'
exec_vm() { prlctl exec "Windows 11" cmd.exe /c "$1" 2>&1; }

echo "--- copiando fontes ---"
exec_vm "xcopy /E /I /Y /Q \"$S\motor-web\tauri\src-tauri\" C:\build\biblioteca-tauri\src-tauri" | tail -1
exec_vm "copy /Y \"$S\motor-web\biblioteca.html\" C:\build\biblioteca-tauri\src\index.html" | tail -1
exec_vm "copy /Y \"$S\motor-web\windows\biblioteca.nsi\" C:\build\windows" | tail -1

echo "--- portao: o que chegou tem de ser o NOVO ---"
falhou=0
confere() {   # <padrao> <arquivo> <rotulo>
    if exec_vm "findstr /C:\"$1\" \"$2\"" | grep -q .; then
        echo "   ok: $3"
    else
        echo "   FALTOU: $3"; falhou=1
    fi
}
confere "copiar_texto"  "C:\build\biblioteca-tauri\src-tauri\src\lib.rs"      "comando copiar_texto (Rust)"
confere "BIBLIOTECA_URL" "C:\build\biblioteca-tauri\src-tauri\src\lib.rs"      "abertura por Start-Process (Rust)"
confere "atributoCopiar" "C:\build\biblioteca-tauri\src\index.html"           "marca do titulo no link (HTML)"
confere "UrlAssociations" "C:\build\biblioteca-tauri\src-tauri\src\lib.rs"     "navegador lido do registro (Rust)"
confere "comISBN" "C:\build\biblioteca-tauri\src\index.html"              "ISBN guardado no comentario (HTML)"
confere "carregando-detalhe" "C:\build\biblioteca-tauri\src\index.html"   "aviso de carregamento (HTML)"
confere "preencherSeletorDePais" "C:\build\biblioteca-tauri\src\index.html" "campo de pais no formulario (HTML)"
confere "info_do_arquivo" "C:\build\biblioteca-tauri\src-tauri\src\lib.rs"  "data do arquivo na faixa (Rust)"
# Sem ASPAS nos padroes: elas se perdem atravessando o prlctl exec e a
# conferencia da falso negativo (aconteceu nesta mesma montagem).
confere "$V" "C:\build\biblioteca-tauri\src-tauri\Cargo.toml"  "Cargo.toml em $V"
confere "$V" "C:\build\windows\biblioteca.nsi"                 "instalador NSIS em $V"
[ "$falhou" -eq 0 ] || { echo "ABORTADO: a VM nao esta com os fontes da $V."; exit 1; }

echo "--- compilando ---"
# O exec_vm as vezes devolve "PrlJob_GetResult: Invalid argument" e NAO roda o
# comando. Sem este portao o empacotador embrulha o binario ANTIGO com o nome
# da versao nova — aconteceu na 1.9.9 e quase foi publicado assim.
saida_compilacao=$(exec_vm "C:\build\compilar.bat")
echo "$saida_compilacao" | tail -3
echo "$saida_compilacao" | grep -q "Finished .release. profile" || {
    echo "ABORTADO: a compilacao nao reportou sucesso."; exit 1; }
echo "--- empacotando ---"
exec_vm "C:\build\empacotar.bat" | tail -3
# O instalador vai para motor-web/windows/, que e onde o ./bin/empacotar.sh o
# procura. NAO para dist/: empacotar.sh comeca apagando dist/ inteiro, e o
# instalador trazido para la seria destruido pelo passo seguinte.
echo "--- trazendo o instalador ---"
exec_vm "copy /Y C:\build\windows\Biblioteca-$V-setup.exe \"$S\motor-web\windows\"" | tail -1
DESTINO="$(dirname "$0")/../motor-web/windows/Biblioteca-$V-setup.exe"
[ -f "$DESTINO" ] || { echo "ABORTADO: o instalador nao chegou ao Mac."; exit 1; }
echo "   $(cd "$(dirname "$DESTINO")" && pwd)/$(basename "$DESTINO")  ($(du -h "$DESTINO" | cut -f1))"
