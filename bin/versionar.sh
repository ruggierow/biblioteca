#!/bin/bash
# Carimba o numero de VERSION em todas as plataformas.
#
#   echo "1.8.1" > VERSION && ./bin/versionar.sh
#
# Antes da consolidacao havia cinco numeracoes independentes. Este script
# existe para que nunca mais haja: VERSION e a unica fonte.
set -e
RAIZ="$(cd "$(dirname "$0")/.." && pwd)"
V="$(tr -d '[:space:]' < "$RAIZ/VERSION")"

if [ -z "$V" ]; then echo "VERSION esta vazio."; exit 1; fi
echo "Carimbando versao $V"

python3 - "$RAIZ" "$V" <<'FIM'
import plistlib, re, sys, pathlib

raiz, v = pathlib.Path(sys.argv[1]), sys.argv[2]
mudou = []

def plist(caminho, rotulo):
    p = raiz / caminho
    if not p.exists():
        print(f"  - {rotulo}: nao encontrado, pulando"); return
    d = plistlib.loads(p.read_bytes())
    if d.get("CFBundleShortVersionString") == v:
        print(f"  = {rotulo}: ja estava em {v}"); return
    antes = d.get("CFBundleShortVersionString", "?")
    d["CFBundleShortVersionString"] = v
    # FMT_XML: manter o plist legivel e com diff limpo no git
    p.write_bytes(plistlib.dumps(d, fmt=plistlib.FMT_XML))
    mudou.append(f"  * {rotulo}: {antes} -> {v}")

def texto(caminho, padrao, novo, rotulo):
    p = raiz / caminho
    if not p.exists():
        print(f"  - {rotulo}: nao encontrado, pulando"); return
    s = p.read_text(encoding="utf-8")
    s2, n = re.subn(padrao, novo, s)
    if n == 0:
        print(f"  ! {rotulo}: padrao nao encontrado -- CONFIRA"); return
    if s2 == s:
        print(f"  = {rotulo}: ja estava em {v}"); return
    p.write_text(s2, encoding="utf-8")
    mudou.append(f"  * {rotulo}: {n} ocorrencia(s) -> {v}")

# Motor web: o <span> ao lado do titulo na tela principal
texto("motor-web/biblioteca.html",
      r"v\.\d+\.\d+\.\d+", f"v.{v}", "motor-web/biblioteca.html")

# App macOS
plist("motor-web/macos/Sources/BibliotecaMacWeb/Info.plist", "app macOS")

# App iOS: Info.plist e o build setting do Xcode
plist("motor-movel/ios/Biblioteca.App/Info.plist", "app iOS (Info.plist)")
texto("motor-movel/ios/Biblioteca-iPhone.xcodeproj/project.pbxproj",
      r"MARKETING_VERSION = [^;]+;", f"MARKETING_VERSION = {v};",
      "app iOS (MARKETING_VERSION)")

# App Windows (Tauri). Sao QUATRO pontos, todos ficavam para tras:
# o instalador NSIS ja estava em 1.8.3 e o Tauri em 1.8.2 — a versao que o
# usuario via na janela nao era a que o instalador anunciava.
texto("motor-web/tauri/src-tauri/tauri.conf.json",
      r'("version":\s*)"\d+\.\d+\.\d+"', f'\\g<1>"{v}"', "app Windows (tauri.conf.json)")
texto("motor-web/tauri/src-tauri/tauri.conf.json",
      r'("title":\s*"Biblioteca v)\d+\.\d+\.\d+"', f'\\g<1>{v}"', "app Windows (titulo da janela)")
texto("motor-web/tauri/src-tauri/Cargo.toml",
      r'(?m)^version = "\d+\.\d+\.\d+"', f'version = "{v}"', "app Windows (Cargo.toml)")
texto("motor-web/windows/biblioteca.nsi",
      r'(!define APP_VERSION\s+)"\d+\.\d+\.\d+"', f'\\g<1>"{v}"', "instalador NSIS")

# App Android: preserva o build number depois do +
texto("motor-movel/android/pubspec.yaml",
      r"(?m)^version:\s*\d+\.\d+\.\d+\+(\d+)\s*$", f"version: {v}+\\1",
      "app Android (pubspec.yaml)")

print()
if mudou:
    print("Alterados:"); [print(m) for m in mudou]
else:
    print("Nada a fazer: tudo ja estava em " + v)
FIM
