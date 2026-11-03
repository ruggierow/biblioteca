#!/usr/bin/env python3
"""Consulta o App Store Connect e prepara a ficha da loja.

    ./bin/appstore.py              o panorama
    ./bin/appstore.py --builds     so os builds recentes
    ./bin/appstore.py --ficha      mostra o texto proposto para a loja
    ./bin/appstore.py --ficha --gravar    grava o texto na ficha (RASCUNHO)

A LINHA DE COMANDO NAO SUBMETE, e isso nao mudou: nenhuma das opcoes acima
envia nada para analise. `--gravar` preenche os campos de texto do RASCUNHO da
versao, que e privado e reversivel ate alguem apertar "Enviar para analise".

O MODULO, POREM, TEM MAO PESADA — e a prosa daqui dizia o contrario ate
03/11/2026. `enviar()` faz POST e PATCH em qualquer caminho da API, e foi por
ele que passaram, a pedido explicito do usuario:

  - a ficha inteira da 1.0, inclusive as capturas e a classificacao etaria
    (30/10, quando eu havia anotado que isso "so pelo site" — estava errado);
  - o registro de versao 1.9.18, a build anexada e o texto de novidades;
  - **o envio para analise** das duas, via `reviewSubmissions`.

Entao a regra de verdade nao e "a ferramenta nao consegue", e sim: **submeter e
publicar sao decisao do usuario**. Quem chama `enviar()` para submeter tem de
ter uma ordem dele para aquilo, naquela vez. Sem ordem, prepara-se o rascunho e
pergunta-se — e dizer "nao da" quando da seria mentir para ele.

A credencial e a MESMA do TestFlight e da notarizacao:
`~/.appstoreconnect/private_keys/AuthKey_<KEYID>.p8` mais o issuer em
`~/.appstoreconnect/issuer_id`. **Nunca imprimir o conteudo da chave.**

O token e um JWT ES256 valido por 20 minutos (a Apple recusa mais que isso).
"""
import datetime
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric.utils import decode_dss_signature
import base64

BASE = "https://api.appstoreconnect.apple.com/v1"
PASTA = Path.home() / ".appstoreconnect"


def b64(d):
    return base64.urlsafe_b64encode(d).rstrip(b"=")


def token():
    chaves = sorted((PASTA / "private_keys").glob("AuthKey_*.p8"))
    if not chaves:
        sys.exit("Nao achei a chave em ~/.appstoreconnect/private_keys/")
    key_id = chaves[0].stem.replace("AuthKey_", "")
    issuer = (PASTA / "issuer_id").read_text().strip()
    chave = serialization.load_pem_private_key(chaves[0].read_bytes(), password=None)

    agora = int(time.time())
    cab = {"alg": "ES256", "kid": key_id, "typ": "JWT"}
    carga = {"iss": issuer, "iat": agora, "exp": agora + 1200,
             "aud": "appstoreconnect-v1"}
    assinando = b64(json.dumps(cab).encode()) + b"." + b64(json.dumps(carga).encode())
    bruta = chave.sign(assinando, ec.ECDSA(hashes.SHA256()))
    r, s = decode_dss_signature(bruta)
    assinatura = r.to_bytes(32, "big") + s.to_bytes(32, "big")
    return (assinando + b"." + b64(assinatura)).decode()


_TOKEN = None


def pegar(caminho):
    global _TOKEN
    if _TOKEN is None:
        _TOKEN = token()
    req = urllib.request.Request(
        caminho if caminho.startswith("http") else BASE + caminho,
        headers={"Authorization": "Bearer " + _TOKEN})
    try:
        with urllib.request.urlopen(req) as f:
            return json.loads(f.read())
    except urllib.error.HTTPError as e:
        corpo = e.read().decode(errors="replace")[:400]
        sys.exit(f"A Apple recusou ({e.code}): {corpo}")


def quando(iso):
    if not iso:
        return "?"
    return iso.replace("T", " ")[:16]


# ---------------------------------------------------------------------------
# O TEXTO DA FICHA
# ---------------------------------------------------------------------------
# Escrito a partir do que o app FAZ, conferido no codigo em 29/10/2026:
# rede so para consulta de ISBN (BrasilAPI, Open Library, Google Books), camera
# so para capa e codigo de barras, nenhuma conta, nenhum rastreio.
#
# Limites da Apple: nome 30, subtitulo 30, palavras-chave 100 (contando as
# virgulas), promocional 170, descricao 4000.

# "Biblioteca" sozinho JA ESTA EM USO por outra conta — o nome e unico na App
# Store inteira, e a Apple recusa com
# ENTITY_ERROR.ATTRIBUTE.INVALID.DUPLICATE.DIFFERENT_ACCOUNT. "Biblioteca
# Pessoal" estava livre e foi o gravado em 29/10/2026.
NOME = "Biblioteca Pessoal"

SUBTITULO = "Catálogo dos seus livros"

PALAVRAS = "livros,acervo,catálogo,estante,biblioteca pessoal,isbn,leitura,coleção"

PROMOCIONAL = ("Catalogue a sua estante e leve o acervo no bolso. "
               "Sem conta e sem nuvem obrigatória: o arquivo é seu.")

DESCRICAO = """\
Biblioteca é um catálogo pessoal dos livros que você tem.

Ele nasceu de uma estante de verdade, grande demais para a memória: qual
edição eu tenho, onde ela está, para quem eu emprestei, eu já comprei este
livro? O aplicativo responde a essas perguntas no bolso — na frente da
estante ou dentro da livraria.

O QUE ELE FAZ

• Cadastra o livro por título, autor, tema, ano e local do exemplar: a
  prateleira, a sala, a caixa, a pessoa com quem ele está.
• Lê o código de barras do ISBN com a câmera e preenche o cadastro sozinho.
• Guarda a foto da capa, tirada por você ou trazida pela busca.
• Registra empréstimos: quem está com o livro e desde quando.
• Pesquisa por qualquer campo e cruza filtros.
• Mostra o acervo por país de origem, para você ver de onde vem o que lê.
• Separa a edição impressa da edição digital do mesmo livro.

SEU ARQUIVO, SUAS REGRAS

Não há conta, não há cadastro, não há servidor nosso. Tudo fica num arquivo de
texto simples que VOCÊ escolhe onde guardar — no aparelho ou na sua própria
nuvem. Esse arquivo abre em qualquer editor e em qualquer planilha, e continua
seu no dia em que você quiser parar de usar o aplicativo.

NOS QUATRO APARELHOS

O mesmo acervo no iPhone, no Android, no Mac e no Windows, pelo arquivo
compartilhado na sua nuvem. O que você cadastra na frente da estante aparece
no computador.

PRIVACIDADE

O aplicativo não coleta dado nenhum. A única conexão que ele faz é a consulta
de um ISBN que você mesmo pediu, e nela vai só o número do livro.
"""

SUPORTE = "https://github.com/ruggierow/biblioteca"
PRIVACIDADE = "https://ruggierow.github.io/biblioteca/privacidade.html"


def ficha(gravar):
    """Mostra — e com --gravar preenche — o texto do RASCUNHO da versao."""
    apps = pegar("/apps?limit=20")["data"]
    app = apps[0]
    v = pegar(f"/apps/{app['id']}/appStoreVersions?limit=1")["data"][0]
    estado = v["attributes"]["appStoreState"]
    print(f"app {app['attributes']['name']!r}  versao {v['attributes']['versionString']}"
          f"  estado {estado}")
    if estado not in ("PREPARE_FOR_SUBMISSION", "DEVELOPER_REJECTED", "REJECTED"):
        sys.exit(f"A versao esta em {estado}. So mexo em rascunho — "
                 f"nada daqui toca uma versao ja enviada.")

    limites = [("nome", NOME, 30), ("subtitulo", SUBTITULO, 30),
               ("palavras-chave", PALAVRAS, 100), ("promocional", PROMOCIONAL, 170),
               ("descricao", DESCRICAO, 4000)]
    print()
    estourou = False
    for rotulo, texto, teto in limites:
        n = len(texto)
        marca = "ok " if n <= teto else "ESTOUROU"
        if n > teto:
            estourou = True
        print(f"   {marca} {rotulo:16s} {n:>5} / {teto}")
    if estourou:
        sys.exit("\nAlgum campo passou do limite da Apple. Corrija antes de gravar.")

    print(f"\n   suporte:     {SUPORTE}")
    print(f"   privacidade: {PRIVACIDADE}")
    print("\n--- descricao ---")
    print(DESCRICAO)

    if not gravar:
        print("Nada foi gravado. Confira e rode de novo com --gravar.")
        print("A pagina da privacidade precisa estar NO AR antes de enviar para analise.")
        return 0

    loc = pegar(f"/appStoreVersions/{v['id']}/appStoreVersionLocalizations")["data"]
    alvo = next((l for l in loc if l["attributes"]["locale"] == "pt-BR"), loc[0])
    enviar("PATCH", f"/appStoreVersionLocalizations/{alvo['id']}", {
        "data": {"type": "appStoreVersionLocalizations", "id": alvo["id"],
                 "attributes": {"description": DESCRICAO, "keywords": PALAVRAS,
                                "promotionalText": PROMOCIONAL,
                                "supportUrl": SUPORTE}}})
    print("   texto da versao gravado.")

    infos = pegar(f"/apps/{app['id']}/appInfos")["data"]
    rascunho = next((i for i in infos
                     if i["attributes"].get("appStoreState") == "PREPARE_FOR_SUBMISSION"),
                    infos[0])
    il = pegar(f"/appInfos/{rascunho['id']}/appInfoLocalizations")["data"]
    alvo = next((l for l in il if l["attributes"]["locale"] == "pt-BR"), il[0])
    enviar("PATCH", f"/appInfoLocalizations/{alvo['id']}", {
        "data": {"type": "appInfoLocalizations", "id": alvo["id"],
                 "attributes": {"name": NOME, "subtitle": SUBTITULO,
                                "privacyPolicyUrl": PRIVACIDADE}}})
    print("   nome, subtitulo e politica de privacidade gravados.")
    print("\nFALTA, e so no site: capturas de tela, classificacao etaria, "
          "respostas de privacidade do app, preco, e o envio para analise.")
    return 0


def enviar(metodo, caminho, corpo):
    global _TOKEN
    if _TOKEN is None:
        _TOKEN = token()
    dados = json.dumps(corpo).encode()
    req = urllib.request.Request(BASE + caminho, data=dados, method=metodo,
                                 headers={"Authorization": "Bearer " + _TOKEN,
                                          "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req) as f:
            return json.loads(f.read() or b"{}")
    except urllib.error.HTTPError as e:
        sys.exit(f"A Apple recusou ({e.code}): {e.read().decode(errors='replace')[:400]}")


def main():
    if "--ficha" in sys.argv[1:]:
        return ficha("--gravar" in sys.argv[1:])
    so_builds = "--builds" in sys.argv[1:]
    apps = pegar("/apps?limit=20")["data"]
    if not apps:
        sys.exit("Nenhum app nesta conta.")

    for app in apps:
        a = app["attributes"]
        print(f"\n=== {a['name']}  ({a['bundleId']}) ===")
        print(f"    id: {app['id']}   SKU: {a.get('sku')}   "
              f"idioma principal: {a.get('primaryLocale')}")

        builds = pegar(f"/builds?filter[app]={app['id']}&limit=5"
                       f"&sort=-uploadedDate")["data"]
        print(f"\n    BUILDS recentes ({len(builds)}):")
        for b in builds:
            at = b["attributes"]
            print(f"      {at.get('version'):>5}  enviado {quando(at.get('uploadedDate'))}  "
                  f"processamento: {at.get('processingState')}  "
                  f"expira: {quando(at.get('expirationDate'))}")
        if so_builds:
            continue

        versoes = pegar(f"/apps/{app['id']}/appStoreVersions?limit=5")["data"]
        print(f"\n    VERSOES NA LOJA ({len(versoes)}):")
        if not versoes:
            print("      nenhuma — o app NUNCA teve versao de loja criada "
                  "(so TestFlight)")
        for v in versoes:
            at = v["attributes"]
            print(f"      {at.get('versionString')}  estado: {at.get('appStoreState')}  "
                  f"plataforma: {at.get('platform')}  "
                  f"lancamento: {at.get('releaseType')}")

        infos = pegar(f"/apps/{app['id']}/appInfos")["data"]
        for i in infos:
            at = i["attributes"]
            print(f"\n    FICHA: estado {at.get('appStoreState')}   "
                  f"classificacao etaria: {at.get('appStoreAgeRating') or 'NAO PREENCHIDA'}   "
                  f"direitos de marca: {at.get('brazilAgeRating') or '—'}")
            loc = pegar(f"/appInfos/{i['id']}/appInfoLocalizations")["data"]
            for l in loc:
                la = l["attributes"]
                faltam = [c for c in ("name", "subtitle", "privacyPolicyUrl")
                          if not la.get(c)]
                print(f"      [{la.get('locale')}] nome: {la.get('name')!r}   "
                      f"subtitulo: {la.get('subtitle')!r}")
                print(f"           politica de privacidade: "
                      f"{la.get('privacyPolicyUrl') or 'FALTA'}")
                if faltam:
                    print(f"           FALTAM: {', '.join(faltam)}")


if __name__ == "__main__":
    main()
