#!/usr/bin/env python3
"""Publica o .aab nas faixas FECHADAS da Play, e confere que ele chegou.

    ./bin/publicar-play.py              o plano: confere tudo e NAO envia nada
    ./bin/publicar-play.py --publicar   envia, e confere DEPOIS de enviar
    ./bin/publicar-play.py --conferir   o portao: a versao do VERSION esta no
                                        ar nas faixas fechadas?  (0 sim, 1 nao)
    ./bin/publicar-play.py --faixas     o estado de todas as faixas, sem julgar

`--pacotes <pasta>` troca onde ele procura o `.aab` (por omissao,
`~/Desktop/Biblioteca-Web`). Existe para dar para APONTAR O PORTAO PARA UMA
PASTA DE MENTIRA e ver se ele reprova — portao que nunca foi visto reprovando
nao se sabe se olha.

Sem `--publicar` nada e enviado. Essa e a mesma divisao do `appstore.py`:
preparar e conferir sao de graca, **publicar e decisao do usuario**, pedida
naquela vez.

POR QUE ELE EXISTE

A 1.9.19, a 1.9.20 e a 1.9.21 foram publicadas a mao, chamada por chamada. E a
**1.9.20 nunca chegou a Play**: em 12/11/2026, quatro dias depois, o mais novo
nas faixas fechadas ainda era o codigo 30 (1.9.19). O Android ficou uma versao
atras na loja e ninguem notou, porque nada olhava.

A causa cabe numa linha do `ls`: para a 1.9.20 existe o
`Biblioteca-Android-1.9.20-b31.apk` e **nao existe o `.aab`**. Metade do
`flutter build` nao rodou. O `publicar-release.sh` so precisa do APK — e o que
a pagina oferece —, entao a ausencia do pacote que a Play exige nao incomodou
ninguem. Por isso a primeira coisa que este programa faz e procurar o `.aab`.

O PORTAO, EM DUAS PONTAS

Antes de falar com o Google, tres fontes escritas em lugares diferentes tem de
concordar — o `VERSION`, o `version:` do `pubspec.yaml` e o
**manifesto dentro do proprio pacote**. A terceira e a que importa: nome de
arquivo e coisa que eu digito, e pacote velho renomeado passa por novo.
O numero de versao tambem e conferido contra os que a Play ja recebeu, porque
**codigo de versao queima** (403 "Version code 29 has already been used.",
medido em 04/11/2026 — dois pacotes diferentes com o mesmo numero).

E confere-se a IMPRESSAO DIGITAL da chave que assinou o pacote. Essa e a de
consequencia mais feia: com a chave errada o Android recusa atualizar por cima,
o testador tem de desinstalar, e desinstalar apaga as capas que ele guardou no
aparelho. Num clone sem o `key.properties` o build assina com a chave de DEBUG
e nao avisa.

Depois de enviar, abre-se um edit NOVO e le-se a faixa. Enviar sem conferir e
exatamente a postura que deixou a 1.9.20 de fora: ninguem perguntou se chegou.

A CREDENCIAL, E O QUE ELA NAO PODE

`~/.googleplay/chave.json`, a mesma conta de servico de sempre.
**Nunca imprimir o conteudo.** A permissao concedida a ela e
"Liberar para faixas de teste": **producao ficou de fora de proposito**, e por
isso nao ha nenhuma faixa de producao neste arquivo. Promover e decisao dele,
pelo Console.
"""
import argparse
import json
import re
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PACOTES = Path.home() / "Desktop" / "Biblioteca-Web"
CHAVE = Path.home() / ".googleplay" / "chave.json"

PKG = "com.wilson.biblioteca.biblioteca"
API = f"https://androidpublisher.googleapis.com/androidpublisher/v3/applications/{PKG}"
SUBIR = ("https://androidpublisher.googleapis.com/upload/androidpublisher/v3"
         f"/applications/{PKG}")

# As DUAS faixas fechadas que ele tem. O nome proprio vem com o erro de
# digitacao do Console ("inical"); corrigi-lo aqui faria o PUT criar uma faixa
# NOVA e vazia, sem testador nenhum.
FAIXAS = ("alpha", "Teste inical do Biblioteca")

# A chave com que os testadores JA tem o app instalado (SHA-256 do
# certificado, a mesma impressao digital do docs/play-console-passo-a-passo.md).
# Trocar de chave nao e "assinar diferente": o Android recusa a atualizacao por
# cima, a pessoa tem de DESINSTALAR, e desinstalar apaga as capas guardadas em
# `Documents/capas/`. O `app/build.gradle.kts` cai na chave de DEBUG quando o
# `key.properties` nao existe (clone limpo, outra maquina) — e e um pacote
# assim que esta conferencia pega.
CHAVE_DOS_TESTADORES = ("5F:18:B7:F1:16:A0:B8:D1:33:08:F6:71:80:42:A2:A4:"
                        "2C:74:41:00:03:81:C3:79:60:0C:8E:DA:90:52:54:D1")

# Teto da Play para o texto de novidades, por idioma.
TETO_NOTAS = 500

# Cabecalhos das notas que NAO sao novidade (os mesmos do gerar-pagina.py).
NAO_E_NOVIDADE = {"instalacao", "instalação"}

falhas, avisos = [], []


def reprova(m):
    falhas.append(m)
    print(f"   FALHOU: {m}")


def passa(m):
    print(f"   ok: {m}")


def avisa(m):
    avisos.append(m)
    print(f"   AVISO: {m}")


# ---------------------------------------------------------------------------
# O QUE ESTA NO DISCO
# ---------------------------------------------------------------------------
def versao():
    return (RAIZ / "VERSION").read_text().strip()


def pubspec():
    """O `version: 1.9.21+32` do Android, como (nome, codigo)."""
    arq = RAIZ / "motor-movel" / "android" / "pubspec.yaml"
    m = re.search(r"^version:\s*([0-9.]+)\+(\d+)\s*$", arq.read_text(), re.M)
    if not m:
        sys.exit(f"Nao achei o `version: <nome>+<codigo>` em {arq}")
    return m.group(1), int(m.group(2))


def manifesto(aab):
    """versionName, versionCode e package lidos de DENTRO do .aab.

    O `base/manifest/AndroidManifest.xml` do bundle e protobuf, nao o XML
    binario do APK — nenhum `aapt2 dump badging` serve nele, e o `bundletool`
    nao esta instalado. Mas nao e preciso: cada atributo aparece como

        \\x12 <n> <nome>   \\x1a <n> <valor em texto>

    (campos 2 e 3 do XmlAttribute), e o valor ja vem em digitos. O byte de
    comprimento faz parte da busca, senao `versionCode` casaria dentro de
    `versionCodeMajor`.
    """
    with zipfile.ZipFile(aab) as z:
        dados = z.read("base/manifest/AndroidManifest.xml")

    def atributo(nome):
        marca = b"\x12" + bytes([len(nome)]) + nome.encode()
        i = dados.find(marca)
        if i < 0:
            return None
        j = i + len(marca)
        if dados[j] != 0x1A:          # nao e um valor de texto
            return None
        n = dados[j + 1]
        return dados[j + 2:j + 2 + n].decode(errors="replace")

    return {c: atributo(c) for c in ("versionName", "versionCode", "package")}


def assinatura(aab):
    """O SHA-256 do certificado que assinou o pacote, pelo `keytool`.

    Devolve None quando nao deu para olhar — e nao olhar NAO e aprovar.
    """
    try:
        bruto = subprocess.run(["keytool", "-printcert", "-jarfile", str(aab)],
                               capture_output=True, text=True, timeout=120)
    except (OSError, subprocess.SubprocessError):
        return None
    if bruto.returncode != 0:
        return None
    m = re.search(r"SHA256:\s*([0-9A-F:]+)", bruto.stdout)
    return m.group(1) if m else None


def notas_para_play(v):
    """O texto de novidades, de `docs/notas-<v>.md` — ou do atalho, se houver.

    Regra: a chamada (o primeiro paragrafo) mais os destaques (os cabecalhos
    `##`), que e o mesmo material que a pagina do app usa. Se o conjunto passar
    dos 500 caracteres da Play, ficam so a chamada; se nem ela couber, este
    programa **reprova** em vez de cortar. Texto cortado no meio e perda
    calada, e loja e vitrine.

    Para escrever a mao, `docs/notas-<v>-play.txt` ganha de tudo isto.
    """
    atalho = RAIZ / "docs" / f"notas-{v}-play.txt"
    if atalho.exists():
        return atalho.read_text().strip(), f"docs/{atalho.name}"

    arq = RAIZ / "docs" / f"notas-{v}.md"
    if not arq.exists():
        return None, f"nao achei docs/notas-{v}.md"
    linhas = arq.read_text().splitlines()

    chamada, destaques = [], []
    for i, l in enumerate(linhas):
        if l.startswith("## "):
            titulo = l[3:].strip()
            if titulo.lower() not in NAO_E_NOVIDADE:
                destaques.append(titulo)
        elif not chamada and l.strip() and not l.startswith("#"):
            j = i
            while j < len(linhas) and linhas[j].strip():
                chamada.append(linhas[j].strip())
                j += 1
    if not chamada:
        return None, f"docs/notas-{v}.md nao tem paragrafo de abertura"

    sem_negrito = lambda t: re.sub(r"\*\*(.+?)\*\*", r"\1", t)
    abertura = sem_negrito(" ".join(chamada))
    completo = abertura + "\n\n" + "\n".join("• " + sem_negrito(d)
                                             for d in destaques)
    if len(completo) <= TETO_NOTAS:
        return completo, "a chamada e os destaques das notas"
    return abertura, f"so a chamada (com os destaques daria {len(completo)})"


# ---------------------------------------------------------------------------
# A PLAY
# ---------------------------------------------------------------------------
_TOKEN = None


def token():
    global _TOKEN
    if _TOKEN is None:
        if not CHAVE.exists():
            sys.exit(f"Nao achei a credencial em {CHAVE}")
        from google.oauth2 import service_account
        import google.auth.transport.requests as gat
        cred = service_account.Credentials.from_service_account_file(
            str(CHAVE),
            scopes=["https://www.googleapis.com/auth/androidpublisher"])
        cred.refresh(gat.Request())
        _TOKEN = cred.token
    return _TOKEN


def chamar(metodo, url, corpo=None, tipo="application/json"):
    """Uma chamada a API. Devolve o JSON, ou None quando a resposta e vazia."""
    dados = None
    cabecalhos = {"Authorization": "Bearer " + token()}
    if corpo is not None:
        dados = corpo if isinstance(corpo, bytes) else json.dumps(corpo).encode()
        cabecalhos["Content-Type"] = tipo
    req = urllib.request.Request(url, data=dados, method=metodo,
                                 headers=cabecalhos)
    try:
        with urllib.request.urlopen(req, timeout=600) as f:
            bruto = f.read()
    except urllib.error.HTTPError as e:
        # A mensagem do Google e o que explica "codigo ja usado" e "sem
        # permissao". Mostrar os primeiros 400 caracteres basta, e nenhum deles
        # e credencial.
        sys.exit(f"A Play recusou ({e.code}) em {metodo} {url.split('?')[0]}:\n"
                 f"   {e.read().decode(errors='replace')[:400]}")
    return json.loads(bruto) if bruto.strip() else None


def abrir_edit():
    return chamar("POST", f"{API}/edits", {})["id"]


def descartar(edit):
    """Joga o edit fora. Edit aberto e so rascunho — nada do que esta nele
    vale antes do `:commit`. Descartar o de leitura evita deixar rascunho
    pendurado na conta."""
    try:
        chamar("DELETE", f"{API}/edits/{edit}")
    except SystemExit:
        pass


def faixas_de(edit):
    """{nome da faixa: [(codigo, estado, nome da release), ...]}.

    A chave da resposta e `tracks`, no PLURAL (`track` e o nome da faixa
    dentro de cada item). Ler `track` devolve lista vazia e parece perda de
    permissao — cai nisso em 12/11/2026.
    """
    resposta = chamar("GET", f"{API}/edits/{edit}/tracks") or {}
    saida = {}
    for item in resposta.get("tracks", []):
        lancamentos = []
        for r in item.get("releases", []):
            for c in r.get("versionCodes", []) or []:
                lancamentos.append((int(c), r.get("status"), r.get("name")))
        saida[item.get("track")] = lancamentos
    return saida


def codigos_ja_enviados(edit):
    """Todos os codigos que a Play ja recebeu — bundles E apks.

    Os dois contam para o mesmo numero: o codigo queima no app, nao no formato.
    Hoje so ha bundles la, mas perguntar pelos dois custa uma chamada e evita
    um "o codigo e novo" que a Play desmentiria com 403.
    """
    usados = set()
    for colecao, chave in (("bundles", "bundles"), ("apks", "apks")):
        resposta = chamar("GET", f"{API}/edits/{edit}/{colecao}") or {}
        usados.update(int(x["versionCode"]) for x in resposta.get(chave, []))
    return sorted(usados)


# ---------------------------------------------------------------------------
# O PORTAO
# ---------------------------------------------------------------------------
def conferir_disco(v):
    """Tudo o que da para conferir sem rede. Devolve (aab, codigo) ou None."""
    nome, codigo = pubspec()
    if nome != v:
        reprova(f"o VERSION diz {v} e o pubspec.yaml diz {nome} — "
                f"rode ./bin/versionar.sh")
        return None
    passa(f"o VERSION e o pubspec.yaml dizem {v}")

    aab = PACOTES / f"Biblioteca-Android-{v}-b{codigo}.aab"
    if not aab.exists():
        reprova(f"nao existe {aab.name}. A Play exige o appbundle: rode "
                f"`flutter build appbundle --release` e copie para "
                f"{PACOTES}/ — foi exatamente este pacote que faltou na 1.9.20")
        return None
    passa(f"{aab.name} ({aab.stat().st_size / 1e6:.1f} MB)")

    apk = PACOTES / f"Biblioteca-Android-{v}-b{codigo}.apk"
    if not apk.exists():
        # Nao bloqueia: a Play nao quer o APK. Mas os dois saem do mesmo
        # `flutter build`, e um sozinho quer dizer meia construcao — e e o APK
        # que a pagina do app oferece para baixar.
        avisa(f"nao existe o {apk.name}, que e o que a pagina oferece. "
              f"Os dois saem do mesmo build: confira se nao ficou meia "
              f"construcao")

    m = manifesto(aab)
    if m["package"] != PKG:
        reprova(f"o pacote dentro do .aab e {m['package']}, nao {PKG}")
        return None
    if m["versionName"] != v:
        reprova(f"o .aab declara a versao {m['versionName']}, e o VERSION diz "
                f"{v} — o arquivo tem o nome novo e o conteudo velho")
        return None
    if m["versionCode"] != str(codigo):
        reprova(f"o .aab declara o codigo {m['versionCode']} e o pubspec.yaml "
                f"diz {codigo}")
        return None
    passa(f"o manifesto DENTRO do .aab declara {v} e codigo {codigo}")

    digital = assinatura(aab)
    if digital is None:
        reprova("nao consegui rodar o keytool, entao NAO CONFERI com que chave "
                "o pacote esta assinado — e pacote com a chave errada obriga o "
                "testador a desinstalar, o que apaga as capas dele")
        return None
    if digital != CHAVE_DOS_TESTADORES:
        reprova(f"o pacote esta assinado com {digital[:17]}..., e a chave dos "
                f"testadores e {CHAVE_DOS_TESTADORES[:17]}... — confira se o "
                f"motor-movel/android/key.properties existe (sem ele o build "
                f"assina com a chave de DEBUG)")
        return None
    passa("assinado com a chave que os testadores ja tem")
    return aab, codigo


def main():
    global PACOTES
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--publicar", action="store_true",
                   help="envia o .aab e libera nas faixas fechadas")
    p.add_argument("--conferir", action="store_true",
                   help="so pergunta se a versao do VERSION esta no ar")
    p.add_argument("--faixas", action="store_true",
                   help="mostra o estado de todas as faixas")
    p.add_argument("--pacotes", metavar="PASTA", default=str(PACOTES),
                   help="onde procurar o .aab (serve para testar o portao)")
    a = p.parse_args()

    PACOTES = Path(a.pacotes).expanduser()
    v = versao()

    if a.faixas:
        edit = abrir_edit()
        try:
            for faixa, lancamentos in sorted(faixas_de(edit).items()):
                if not lancamentos:
                    print(f"   {faixa:32s} VAZIA")
                for codigo, estado, nome in lancamentos:
                    print(f"   {faixa:32s} codigo {codigo:<4} {estado:12s} "
                          f"{nome or ''}")
        finally:
            descartar(edit)
        return 0

    if a.conferir:
        # O portao que faltava em 08/11/2026. Nao olha o disco: pergunta a
        # Play se a versao que este repositorio diz ser a atual esta nas duas
        # faixas fechadas, liberada.
        _, codigo = pubspec()
        print(f"--- a {v} (codigo {codigo}) nas faixas fechadas ---")
        edit = abrir_edit()
        try:
            atual = faixas_de(edit)
        finally:
            descartar(edit)
        for faixa in FAIXAS:
            liberados = [c for c, estado, _ in atual.get(faixa, [])
                         if estado == "completed"]
            if codigo in liberados:
                passa(f"{faixa}: codigo {codigo} liberado")
            elif liberados:
                reprova(f"{faixa}: o liberado la e o codigo {max(liberados)}, "
                        f"nao o {codigo} desta versao")
            else:
                reprova(f"{faixa}: nao ha nada liberado")
        print()
        if falhas:
            print(f"REPROVADO: a {v} NAO esta no ar nas faixas fechadas.")
            return 1
        print(f"A {v} esta no ar nas duas faixas fechadas.")
        return 0

    print(f"--- publicar a {v} nas faixas fechadas da Play ---")
    achado = conferir_disco(v)
    if achado is None:
        print("\nREPROVADO: nada foi enviado.")
        return 1
    aab, codigo = achado

    texto, origem = notas_para_play(v)
    if texto is None:
        reprova(f"sem texto de novidades: {origem}")
    elif len(texto) > TETO_NOTAS:
        reprova(f"o texto de novidades tem {len(texto)} caracteres e a Play "
                f"aceita {TETO_NOTAS}. Encurte a chamada de "
                f"docs/notas-{v}.md, ou escreva docs/notas-{v}-play.txt")
    else:
        passa(f"novidades: {len(texto)}/{TETO_NOTAS} caracteres, de {origem}")

    edit = abrir_edit()
    try:
        enviados = codigos_ja_enviados(edit)
        if codigo in enviados:
            reprova(f"a Play JA recebeu o codigo {codigo}. Codigo de versao "
                    f"queima: suba o numero no pubspec.yaml e construa de "
                    f"novo (os de la: {', '.join(map(str, enviados))})")
        else:
            passa(f"o codigo {codigo} e novo para a Play "
                  f"(o mais alto de la e {max(enviados) if enviados else 0})")

        atual = faixas_de(edit)
        for faixa in FAIXAS:
            tem = atual.get(faixa, [])
            onde = (", ".join(f"codigo {c} {e}" for c, e, _ in tem)
                    if tem else "VAZIA")
            print(f"   hoje em {faixa!r}: {onde}")

        if falhas:
            print("\nREPROVADO: nada foi enviado.")
            return 1

        print(f"\n--- o texto que vai para a loja ---\n{texto}\n")

        if not a.publicar:
            print("Nada foi enviado. Confira o texto e rode de novo com "
                  "--publicar.")
            if avisos:
                print(f"E {len(avisos)} aviso(s) la em cima.")
            return 0

        print(f"Enviando {aab.name}...")
        resposta = chamar("POST",
                          f"{SUBIR}/edits/{edit}/bundles?uploadType=media",
                          aab.read_bytes(), "application/octet-stream")
        recebido = int(resposta["versionCode"])
        if recebido != codigo:
            # Nao commitar: o edit morre no `finally` e nada foi liberado.
            reprova(f"a Play registrou o codigo {recebido} e eu enviei o "
                    f"{codigo}. Edit descartado, nada liberado")
            return 1
        passa(f"a Play recebeu o codigo {recebido}")

        for faixa in FAIXAS:
            chamar("PUT",
                   f"{API}/edits/{edit}/tracks/{urllib.parse.quote(faixa)}",
                   {"track": faixa,
                    "releases": [{"name": f"{codigo} ({v})",
                                  "versionCodes": [str(codigo)],
                                  "status": "completed",
                                  # Acento VALE aqui: e texto publico, UTF-8.
                                  # So pt-BR, porque e a unica ficha escrita.
                                  "releaseNotes": [{"language": "pt-BR",
                                                    "text": texto}]}]})
            passa(f"faixa {faixa!r} apontada para o codigo {codigo}")

        chamar("POST", f"{API}/edits/{edit}:commit")
        print("   ok: edit publicado (commit)")
        edit = None                      # commitado: nao ha o que descartar
    finally:
        if edit:
            descartar(edit)

    # A segunda ponta do portao: ler de um edit NOVO. Dizer "enviei" e
    # diferente de dizer "esta la", e a 1.9.20 morreu nessa diferenca.
    print("\n--- conferindo o que a Play diz AGORA ---")
    novo = abrir_edit()
    try:
        depois = faixas_de(novo)
    finally:
        descartar(novo)
    for faixa in FAIXAS:
        liberados = [c for c, estado, _ in depois.get(faixa, [])
                     if estado == "completed"]
        if codigo in liberados:
            passa(f"{faixa}: codigo {codigo} liberado")
        else:
            reprova(f"{faixa}: o codigo {codigo} NAO aparece liberado "
                    f"(la esta {liberados or 'nada'})")

    print()
    if falhas:
        print(f"REPROVADO: {len(falhas)} problema(s) — confira no Console.")
        return 1
    print(f"A {v} (codigo {codigo}) esta liberada nas duas faixas fechadas.")
    if avisos:
        print(f"Com {len(avisos)} aviso(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
