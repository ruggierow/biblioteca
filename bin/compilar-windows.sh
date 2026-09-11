#!/bin/bash
# Compila o app Windows (Tauri) e gera o instalador NSIS, pilotando a VM
# Parallels a partir do Mac. Ao final o setup.exe volta para motor-web/windows/.
#
# Por que assim: o Tauri para Windows precisa do MSVC, que so existe no Windows.
# A VM ja tem tudo instalado (Rust aarch64 + Build Tools + NSIS), e o Mac
# alcanca o disco C: dela por /Volumes — entao da para fazer tudo daqui.
#
# Pre-requisitos na VM (instalados em 10/09/2026):
#   - Rust stable aarch64-pc-windows-msvc em C:\rust
#   - VS Build Tools 2022 com C++ ARM64 + Windows SDK
#   - NSIS em C:\Program Files (x86)\NSIS
set -e

VM="Windows 11"
RAIZ="$(cd "$(dirname "$0")/.." && pwd)"
V="$(tr -d '[:space:]' < "$RAIZ/VERSION")"
MONTADO="/Volumes/[C] Windows 11.hidden"
STAGE="$MONTADO/build"

if [ ! -d "$MONTADO" ]; then
    echo "O disco C: da VM nao esta montado em $MONTADO."
    echo "Ligue a VM '$VM' no Parallels e tente de novo."
    exit 1
fi
if ! prlctl list -a 2>/dev/null | grep -q "running.*$VM"; then
    echo "A VM '$VM' nao esta rodando."
    exit 1
fi

echo "Versao: $V"

# ---------------------------------------------------------------
# 1. Fontes para a VM
#    -L materializa os links simbolicos: o src/index.html aponta para o motor,
#    e link simbolico do macOS nao atravessa para o Windows.
# ---------------------------------------------------------------
echo "Copiando fontes para a VM..."
rm -rf "$STAGE/biblioteca-tauri/src" "$STAGE/biblioteca-tauri/src-tauri/src"
mkdir -p "$STAGE/biblioteca-tauri/src"
cp -RL "$RAIZ/motor-web/tauri/src-tauri/." "$STAGE/biblioteca-tauri/src-tauri/"
cp -L  "$RAIZ/motor-web/tauri/src/index.html" "$STAGE/biblioteca-tauri/src/index.html"
find "$STAGE/biblioteca-tauri" -name "._*" -delete 2>/dev/null || true

# ---------------------------------------------------------------
# 2. Compilar (dentro do ambiente do MSVC — sem vcvarsall o cc-rs procura clang)
# ---------------------------------------------------------------
cat > "$STAGE/compilar.bat" <<'FIM'
@echo off
call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvarsall.bat" arm64 >nul
if errorlevel 1 (echo FALHA no vcvarsall & exit /b 1)
set RUSTUP_HOME=C:\rust\.rustup
set CARGO_HOME=C:\rust\.cargo
set PATH=C:\rust\.cargo\bin;%PATH%
cd /d C:\build\biblioteca-tauri\src-tauri
cargo build --release
exit /b %ERRORLEVEL%
FIM
# O app aberto segura o .exe e o cargo nao consegue relinkar ("Access is denied").
# Sem fechar antes, o build falha e o instalador sairia com o binario ANTIGO.
echo "Fechando o app na VM, se estiver aberto..."
prlctl exec "$VM" cmd.exe /c "taskkill /IM biblioteca-tauri.exe /F >nul 2>&1 & taskkill /IM Biblioteca.exe /F >nul 2>&1 & exit 0" >/dev/null 2>&1 || true

EXE="$STAGE/biblioteca-tauri/src-tauri/target/release/biblioteca-tauri.exe"
rm -f "$EXE"     # garante que um binario velho nao seja confundido com sucesso

echo "Compilando na VM (alguns minutos)..."
SAIDA=$(prlctl exec "$VM" cmd.exe /c "C:\\build\\compilar.bat" 2>&1) || true
echo "$SAIDA" | grep -E "^error|error\[|warning: unused|Finished" || true
if echo "$SAIDA" | grep -qE "^error|error\[|error:"; then
    echo "FALHOU: erro de compilacao (acima)."
    exit 1
fi
if [ ! -f "$EXE" ]; then echo "FALHOU: o executavel nao foi gerado."; exit 1; fi
echo "  Executavel: $(du -h "$EXE" | cut -f1)  ($(date -r "$EXE" '+%d/%m %H:%M:%S'))"

# ---------------------------------------------------------------
# 3. Montar a pasta do instalador e rodar o NSIS
# ---------------------------------------------------------------
echo "Montando o instalador..."
rm -rf "$STAGE/windows"; mkdir -p "$STAGE/windows"
cp "$EXE" "$STAGE/windows/biblioteca-tauri.exe"
cp "$RAIZ/motor-web/windows/biblioteca.nsi" "$STAGE/windows/"
cp "$RAIZ/motor-web/windows/biblioteca.ico" "$STAGE/windows/"
cp "$RAIZ/docs/manual-windows.html" "$STAGE/windows/Manual.html"
cp "$RAIZ/docs/manual-windows.pdf"  "$STAGE/windows/Manual.pdf"
find "$STAGE/windows" -name "._*" -delete 2>/dev/null || true

cat > "$STAGE/empacotar.bat" <<'FIM'
@echo off
cd /d C:\build\windows
"C:\Program Files (x86)\NSIS\makensis.exe" biblioteca.nsi
exit /b %ERRORLEVEL%
FIM
prlctl exec "$VM" cmd.exe /c "C:\\build\\empacotar.bat" 2>&1 | tail -6

SETUP="$STAGE/windows/Biblioteca-$V-setup.exe"
# O volume montado demora um instante para refletir o que o Windows acabou de
# gravar; sem esta espera o teste falha com o arquivo ja pronto do outro lado.
for _ in 1 2 3 4 5 6 7 8 9 10; do [ -f "$SETUP" ] && break; sleep 1; done
if [ ! -f "$SETUP" ]; then echo "FALHOU: o instalador nao foi gerado."; exit 1; fi

# ---------------------------------------------------------------
# 4. Trazer de volta
# ---------------------------------------------------------------
cp "$SETUP" "$RAIZ/motor-web/windows/"
echo
echo "Pronto: motor-web/windows/Biblioteca-$V-setup.exe ($(du -h "$SETUP" | cut -f1))"
echo "O HTML nao entra mais no pacote — vai embutido no executavel."
