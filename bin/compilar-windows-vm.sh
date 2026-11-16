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
# O MANUAL, que faltava aqui ate 16/11/2026. O outro caminho (o disco C: montado
# em /Volumes) copiava os dois; este, nao — e quando a extensao do Parallels nao
# carrega, e este que roda. Resultado medido na 1.9.22: o `C:\build\windows`
# ainda tinha o manual de 04/11, e o instalador da 1.9.21 saiu com ele dentro.
exec_vm "copy /Y \"$S\docs\manual-windows.html\" C:\build\windows\Manual.html" | tail -1
exec_vm "copy /Y \"$S\docs\manual-windows.pdf\" C:\build\windows\Manual.pdf" | tail -1

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

# O manual nao se confere por findstr: o PDF e binario e o HTML tem as figuras
# embutidas em base64. Confere-se pelo TAMANHO, contra o arquivo do Mac — e a
# pergunta "chegou o de hoje?", que e a que faltava.
tamanho_no_mac() { wc -c < "$(dirname "$0")/../$1" | tr -d ' '; }
tamanho_na_vm()  { exec_vm "for %I in ($1) do @echo %~zI" | tr -d '\r' \
                       | grep -E "^[0-9]+$" | tail -1; }
confere_tamanho() {   # <arquivo no Mac> <arquivo na VM> <rotulo>
    local aqui la
    aqui="$(tamanho_no_mac "$1")"; la="$(tamanho_na_vm "$2")"
    if [ -n "$la" ] && [ "$aqui" = "$la" ]; then
        echo "   ok: $3 ($aqui bytes)"
    else
        echo "   FALTOU: $3 — o Mac tem $aqui bytes e a VM ${la:-nada}"; falhou=1
    fi
}
confere_tamanho "docs/manual-windows.pdf"  "C:\build\windows\Manual.pdf"  "Manual.pdf e o de hoje"
confere_tamanho "docs/manual-windows.html" "C:\build\windows\Manual.html" "Manual.html e o de hoje"
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
