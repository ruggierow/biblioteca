#!/usr/bin/env python3
"""Compara o que os aplicativos de CELULAR usam com o que eles DECLARAM ao sistema.

    ./bin/conferir-celulares.py

Sai 0 se tudo que o codigo usa esta declarado; 1 e lista o que falta.

POR QUE EXISTE, E POR QUE E DIFERENTE DO conferir-ponte.py

No Mac e no Windows a fronteira perigosa e a PONTE entre a pagina e o
hospedeiro (`bin/conferir-ponte.py`). No iPhone e no Android nao ha pagina: a
fronteira e o que o aplicativo DECLARA ao sistema operacional. Errar ali falha
do mesmo jeito — e, num dos casos, com o mesmo silencio:

  Android, desde o 11: um app so "enxerga" outro se declarar o esquema em
  <queries>. Sem isso, `launchUrl('kindle://...')` simplesmente NAO FAZ NADA.
  Nem erro, nem aviso. O proprio manifesto deste projeto ja traz um comentario
  dizendo isso — alguem ja apanhou.

  iPhone: usar a camera sem `NSCameraUsageDescription` no Info.plist nao e
  silencioso, e pior: o sistema DERRUBA o aplicativo na hora. Um usuario que
  abre o leitor de codigo de barras ve o app fechar.

As regras abaixo saem de medicao, nao de suposicao: cada uma nasceu de olhar o
que este codigo realmente faz.
"""
import json
import plistlib
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DART = RAIZ / "motor-movel/android/lib"
MANIFESTO = RAIZ / "motor-movel/android/android/app/src/main/AndroidManifest.xml"
PUBSPEC = RAIZ / "motor-movel/android/pubspec.yaml"
SWIFT = RAIZ / "motor-movel/ios/Biblioteca.App"
PLIST = RAIZ / "motor-movel/ios/Biblioteca.App/Info.plist"
VERSAO = (RAIZ / "VERSION").read_text().strip()

COMENTARIO = re.compile(r"^\s*(//|///|\*|<!--|#)")


def fontes(pasta, sufixos):
    """O codigo, arquivo a arquivo, com as linhas de comentario fora.

    Decidir por LINHA, e nunca apagar trechos do texto: apagar comentarios em
    bloco ja fez um portao irmao ficar verde por ter comido o que devia
    conferir (ver bin/conferir-ponte.py).
    """
    for p in sorted(pasta.rglob("*")):
        if p.suffix not in sufixos or not p.is_file():
            continue
        util = [l for l in p.read_text(encoding="utf-8", errors="ignore").splitlines()
                if not COMENTARIO.match(l)]
        yield p, "\n".join(util)


# O codigo nomeia um esquema de varias formas, e a primeira versao desta
# conferencia so enxergava uma delas — exigia `'kindle://` com aspa colada.
# Resultado: ela nao viu o kindle no Android, que e justamente o caso que
# importa. Portao que nao enxerga o caso principal e pior que portao nenhum,
# porque da a impressao de cobertura.
FORMAS_DE_ESQUEMA = [
    r"\b([a-z][a-z0-9+.-]*)://",                      # kindle://..., em string OU em regex
    r"""startsWith\(\s*['"]([a-z][a-z0-9+.-]*):""",      # Dart
    r"""hasPrefix\(\s*["']([a-z][a-z0-9+.-]*):""",       # Swift
    r"""scheme[^=\n]*==\s*["']([a-z][a-z0-9+.-]*)["']""",  # url.scheme == "kindle"
]
# Nao precisam de declaracao: sao do proprio processo ou do proprio arquivo.
ESQUEMAS_DISPENSADOS = {"file", "data", "blob", "about", "package", "asset"}


def esquemas_usados(pasta, sufixos):
    achados = set()
    for _, texto in fontes(pasta, sufixos):
        for forma in FORMAS_DE_ESQUEMA:
            achados |= set(re.findall(forma, texto))
    return achados - ESQUEMAS_DISPENSADOS


def usa(padrao, pasta, sufixos):
    """Os arquivos em que o padrao aparece fora de comentario."""
    return [p.name for p, texto in fontes(pasta, sufixos) if re.search(padrao, texto)]


def main():
    faltas = []
    conferidos = 0

    # ---------------- Android ----------------
    print("ANDROID")
    manifesto = MANIFESTO.read_text(encoding="utf-8")
    declarados = set(re.findall(r'android:scheme="([^"]+)"', manifesto))
    permissoes = set(re.findall(r'<uses-permission[^>]*android:name="([^"]+)"', manifesto))

    abertos = esquemas_usados(DART, {".dart"})
    print(f"   esquemas abertos pelo codigo: {', '.join(sorted(abertos)) or '(nenhum)'}")
    print(f"   esquemas declarados em <queries>: {', '.join(sorted(declarados)) or '(nenhum)'}")
    for e in sorted(abertos):
        conferidos += 1
        if e not in declarados:
            faltas.append(("Android", f'esquema "{e}://"',
                           f'declarar <intent><data android:scheme="{e}"/></intent> em <queries>',
                           "desde o Android 11 o launchUrl nao faz NADA, em silencio"))

    regras_android = [
        (r"mobile_scanner|MobileScanner|camera", "android.permission.CAMERA",
         "o leitor de codigo de barras nao abre a camera"),
        (r"http\.get|http\.post|HttpClient|launchUrl", "android.permission.INTERNET",
         "qualquer acesso a rede falha"),
    ]
    for padrao, permissao, porque in regras_android:
        arquivos = usa(padrao, DART, {".dart"})
        if not arquivos:
            continue
        conferidos += 1
        marca = "ok" if permissao in permissoes else "!!"
        print(f"   {marca} {permissao:32s} usado em {arquivos[0]}"
              + (f" e mais {len(arquivos)-1}" if len(arquivos) > 1 else ""))
        if permissao not in permissoes:
            faltas.append(("Android", permissao, "declarar <uses-permission>", porque))

    pubspec = PUBSPEC.read_text(encoding="utf-8")
    m = re.search(r"^version:\s*([0-9.]+)", pubspec, re.M)
    conferidos += 1
    if not m or m.group(1) != VERSAO:
        faltas.append(("Android", "versao do pubspec",
                       f"deveria ser {VERSAO}, esta {m.group(1) if m else '?'}",
                       "a loja recusa, ou publica com o numero errado"))
    else:
        print(f"   ok versao {VERSAO} no pubspec")

    # ---------------- iPhone ----------------
    print("\nIPHONE")
    plist = plistlib.loads(PLIST.read_bytes())
    regras_ios = [
        (r"AVCaptureDevice", "NSCameraUsageDescription",
         "o sistema DERRUBA o aplicativo ao abrir a camera"),
        (r"PHPhotoLibrary|PhotosPicker|UIImagePickerController", "NSPhotoLibraryUsageDescription",
         "o sistema derruba o aplicativo ao abrir a fototeca"),
        (r"AVAudioSession|AVCaptureDevice\.default\(for: \.audio", "NSMicrophoneUsageDescription",
         "o sistema derruba o aplicativo ao usar o microfone"),
    ]
    for padrao, chave, porque in regras_ios:
        arquivos = usa(padrao, SWIFT, {".swift"})
        if not arquivos:
            continue
        conferidos += 1
        tem = chave in plist and str(plist[chave]).strip()
        print(f"   {'ok' if tem else '!!'} {chave:34s} usado em {arquivos[0]}"
              + (f" e mais {len(arquivos)-1}" if len(arquivos) > 1 else ""))
        if not tem:
            faltas.append(("iPhone", chave, "acrescentar a chave no Info.plist, com texto", porque))

    # canOpenURL exige a lista; o `open(_:)` sozinho NAO exige. A regra so vale
    # se o codigo realmente pergunta antes de abrir.
    if usa(r"canOpenURL", SWIFT, {".swift"}):
        conferidos += 1
        esquemas_ios = esquemas_usados(SWIFT, {".swift"})
        declarados_ios = set(plist.get("LSApplicationQueriesSchemes", []))
        for e in sorted(esquemas_ios - declarados_ios - {"http", "https", "file"}):
            faltas.append(("iPhone", f'esquema "{e}://"',
                           "acrescentar em LSApplicationQueriesSchemes",
                           "canOpenURL devolve false e o app desiste de abrir, em silencio"))
    else:
        print("   —  canOpenURL nao e usado; LSApplicationQueriesSchemes nao e exigido")

    conferidos += 1
    if str(plist.get("CFBundleShortVersionString", "")) != VERSAO:
        faltas.append(("iPhone", "versao do Info.plist",
                       f"deveria ser {VERSAO}, esta {plist.get('CFBundleShortVersionString')}",
                       "a App Store recusa, ou publica com o numero errado"))
    else:
        print(f"   ok versao {VERSAO} no Info.plist")

    # ---------------- veredito ----------------
    print()
    if conferidos == 0:
        print("ABORTADO: nao reconheci uso nenhum — o portao nao olhou nada.")
        return 1
    if not faltas:
        print(f"Tudo declarado. {conferidos} item(ns) conferido(s) nos dois aplicativos.")
        return 0
    print(f"FALTAM {len(faltas)} declaracao(oes):\n")
    for onde, o_que, como, porque in faltas:
        print(f"   {onde}: {o_que}")
        print(f"      {como}")
        print(f"      sem isso, {porque}\n")
    return 1


if __name__ == "__main__":
    sys.exit(main())
