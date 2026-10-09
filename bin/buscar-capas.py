#!/usr/bin/env python3
"""Procura capa para os livros que estao sem, no Google Books.

SO MEDE por padrao: baixa as imagens, monta uma folha de contato e para. Para
escrever no biblioteca.dat e preciso pedir com --gravar, e mesmo assim so
entram as que tem o AUTOR conferido.

    ./bin/buscar-capas.py                    # procura e monta a folha
    ./bin/buscar-capas.py --limite 20        # so os 20 primeiros (prova rapida)
    ./bin/buscar-capas.py --gravar           # grava as de autor conferido
    ./bin/buscar-capas.py --gravar --ids a,b # grava tambem estas, aprovadas na folha

AS QUATRO ARMADILHAS, todas medidas, todas tratadas aqui:

1. `intitle:`/`inauthor:` devolvem ZERO nesta API autenticada por conta de
   servico, ate para titulo tecnico em ingles. Busca em TEXTO LIVRE funciona.
2. Casar por SUBSTRING erra em titulo curto: "Familia" casou com "Lexico
   familiar". Substring so vale com >= 12 caracteres; titulo de uma palavra
   exige igualdade.
3. **Conferir so o TITULO nao basta** (09/10/2026): "Mathcad - User's Guide
   2000" casou com "S-PLUS 2000 User's Guide" — 80% das palavras significativas,
   faltando justamente *Mathcad*. Por isso o autor decide o que e gravado.
4. A API devolve 503 em rajada: 6 tentativas com recuo de 3s x n.

E uma observacao de catalogo: autor diferente nem sempre e capa errada. Em
livro de arte e antologia a base registra o curador ou "Varios" e a fonte
registra o artista ou o organizador. Por isso as duvidosas vao para a folha em
vez de serem descartadas.

A credencial e a mesma do Google Play (`~/.googleplay/chave.json`), com escopo
`auth/books`; nao ha chave de API.
"""
import argparse, base64, io, json, re, sys, time, urllib.parse, urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import biblioteca_comum as bc

CHAVE = Path.home() / ".googleplay/chave.json"
TRABALHO = Path.home() / "Documents/biblioteca-capas"


def token():
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import padding
    k = json.loads(CHAVE.read_text())
    agora = int(time.time())
    b = lambda o: base64.urlsafe_b64encode(json.dumps(o).encode()).rstrip(b"=")
    cab = b({"alg": "RS256", "typ": "JWT"})
    rei = b({"iss": k["client_email"], "scope": "https://www.googleapis.com/auth/books",
             "aud": "https://oauth2.googleapis.com/token", "iat": agora, "exp": agora + 3600})
    pk = serialization.load_pem_private_key(k["private_key"].encode(), password=None)
    s = base64.urlsafe_b64encode(pk.sign(cab + b"." + rei, padding.PKCS1v15(), hashes.SHA256())).rstrip(b"=")
    d = urllib.parse.urlencode({"grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
                                "assertion": (cab + b"." + rei + b"." + s).decode()}).encode()
    return json.load(urllib.request.urlopen(urllib.request.Request("https://oauth2.googleapis.com/token", data=d)))["access_token"]


SUFIXO = re.compile(r"\s*[-–—]\s*(\d+)?\s*[ªaº]?\.?\s*(ed\.?|edi[cç][aã]o|edition|vol\.?|volume|livro)\b.*$", re.I)

def enxuto(t):
    """Tira sufixo de edicao e o subtitulo depois do dois-pontos — este ultimo
    so quando o que sobra ainda identifica (>= 12 caracteres), senao
    "Digital Design: ..." viraria a busca inutil "Digital"."""
    t = SUFIXO.sub("", t or "")
    if ":" in t:
        cabeca = t.split(":")[0].strip()
        if len(cabeca) >= 12:
            t = cabeca
    return t.strip()


VAZIAS = {"a","o","as","os","de","da","do","das","dos","e","em","um","uma",
          "the","of","and","to","in","for","an"}

def titulo_casa(nosso, deles):
    a, b = bc.normal(nosso), bc.normal(deles)
    if not a or not b: return False
    if a == b: return True
    curto, longo = (a, b) if len(a) <= len(b) else (b, a)
    if len(curto) >= 12 and curto in longo: return True
    pa = [w for w in a.split() if w not in VAZIAS]
    pb = {w for w in b.split() if w not in VAZIAS}
    if len(pa) <= 1: return False
    return sum(1 for w in pa if w in pb) / len(pa) >= 0.70


FORA_DO_NOME = {"ed","eds","org","jr","filho","neto","de","da","do","dos","das","e","and","von","van"}

def sobrenomes(texto):
    return {p for parte in re.split(r"[;,]", texto or "")
            for p in bc.normal(parte).split() if len(p) > 2 and p not in FORA_DO_NOME}


def consultar(q, tok):
    u = "https://www.googleapis.com/books/v1/volumes?q=" + urllib.parse.quote(q) + "&maxResults=5"
    for n in range(1, 7):
        try:
            return json.load(urllib.request.urlopen(
                urllib.request.Request(u, headers={"Authorization": "Bearer " + tok}), timeout=40))
        except Exception:
            if n == 6: raise
            time.sleep(3 * n)


def folha_de_contato(boas, duvidosas, pasta, destino):
    def cartao(x, classe):
        img = base64.b64encode((pasta / f"{x['id']}.jpg").read_bytes()).decode()
        return (f'<div class="c {classe}"><img src="data:image/jpeg;base64,{img}">'
                f'<div class="t">{x["nosso"]}</div><div class="a">{x["nosso_autor"] or "—"}</div>'
                f'<div class="f">achou: <b>{x["deles"]}</b><br>autor da fonte: '
                f'{"; ".join(x.get("autor_deles") or []) or "—"}<br>id: {x["id"]}</div></div>')
    destino.write_text(f"""<!doctype html><meta charset="utf-8"><title>Capas candidatas</title>
<style>body{{font:14px -apple-system,sans-serif;margin:24px;background:#fafafa;color:#222}}
h2{{font-size:16px;margin-top:32px;border-bottom:2px solid #ddd;padding-bottom:6px}}
.g{{display:flex;flex-wrap:wrap;gap:14px}}
.c{{width:176px;background:#fff;border-radius:8px;padding:10px;box-shadow:0 1px 4px #0002}}
.c img{{width:100%;border-radius:4px;display:block}}
.t{{font-weight:600;margin-top:8px;font-size:12.5px;line-height:1.25}}
.a{{color:#666;font-size:11.5px}} .f{{color:#888;font-size:10.5px;margin-top:6px;
border-top:1px solid #eee;padding-top:5px;line-height:1.3}}
.ok{{border-left:4px solid #2a7}} .du{{border-left:4px solid #e82}}</style>
<h1>Capas candidatas</h1>
<h2>Autor confere — entram com --gravar ({len(boas)})</h2>
<div class="g">{"".join(cartao(x,"ok") for x in boas)}</div>
<h2>Autor NAO confere — so entram se voce passar o id em --ids ({len(duvidosas)})</h2>
<div class="g">{"".join(cartao(x,"du") for x in duvidosas)}</div>""", encoding="utf-8")


def main():
    p = argparse.ArgumentParser(description="Procura capa para os livros sem capa.")
    p.add_argument("--limite", type=int, help="tenta so os N primeiros")
    p.add_argument("--gravar", action="store_true", help="grava as de autor conferido no biblioteca.dat")
    p.add_argument("--ids", default="", help="ids da folha, separados por virgula, a gravar junto")
    a = p.parse_args()

    TRABALHO.mkdir(parents=True, exist_ok=True)
    imagens = TRABALHO / "candidatas"; imagens.mkdir(exist_ok=True)
    fotos = bc.ler_fotos()
    sem = [l for l in bc.ler_base() if l.id not in fotos]
    if a.limite: sem = sem[:a.limite]
    total, com, falta = bc.censo()
    print(f"base: {total} livros, {com} com capa, {falta} sem — vou tentar {len(sem)}")

    tok = token()
    boas, duvidosas, nada, falhas = [], [], 0, 0
    for n, l in enumerate(sem, 1):
        q = f"{enxuto(l.titulo)} {(l.autores or [''])[0]}".strip()
        try:
            r = consultar(q, tok)
        except Exception:
            falhas += 1; continue
        achado = next((it["volumeInfo"] for it in r.get("items", [])
                       if it["volumeInfo"].get("imageLinks")
                       and titulo_casa(enxuto(l.titulo), it["volumeInfo"].get("title", ""))), None)
        if not achado:
            nada += 1
        else:
            link = (achado["imageLinks"].get("thumbnail") or achado["imageLinks"]["smallThumbnail"])
            link = link.replace("&edge=curl", "").replace("zoom=1", "zoom=2").replace("http://", "https://")
            try:
                (imagens / f"{l.id}.jpg").write_bytes(urllib.request.urlopen(link, timeout=40).read())
            except Exception:
                falhas += 1; continue
            x = {"id": l.id, "nosso": l.titulo, "nosso_autor": l.campos[1],
                 "deles": achado.get("title"), "autor_deles": achado.get("authors"), "consulta": q}
            (boas if sobrenomes(l.campos[1]) & sobrenomes("; ".join(achado.get("authors") or []))
             else duvidosas).append(x)
        if n % 25 == 0:
            print(f"   {n}/{len(sem)}   autor confere: {len(boas)}   duvidosas: {len(duvidosas)}", flush=True)
        time.sleep(0.4)

    # Nome COM DATA: em 09/10/2026 uma prova rapida deste comando sobrescreveu a
    # folha da varredura de 07/10, que era o registro de qual fonte deu qual
    # capa. Deu para refazer a partir do candidatos.json, mas nenhum arquivo de
    # saida aqui pode ter nome fixo.
    import datetime
    carimbo = f"{datetime.datetime.now():%Y-%m-%d_%H%M}"
    json.dump(boas, (TRABALHO / f"boas_{carimbo}.json").open("w"), ensure_ascii=False, indent=1)
    json.dump(duvidosas, (TRABALHO / f"duvidosas_{carimbo}.json").open("w"), ensure_ascii=False, indent=1)
    folha = TRABALHO / f"capas-candidatas_{carimbo}.html"
    folha_de_contato(boas, duvidosas, imagens, folha)
    print(f"\ntentadas {len(sem)}   autor confere {len(boas)}   duvidosas {len(duvidosas)}"
          f"   sem resultado {nada}   falhas de rede {falhas}")
    print(f"folha: {folha}")

    if not a.gravar:
        print("\nNada foi gravado. Olhe a folha e rode de novo com --gravar.")
        return
    from PIL import Image
    aprovados = {i.strip() for i in a.ids.split(",") if i.strip()}
    entram = boas + [x for x in duvidosas if x["id"] in aprovados]
    novas = {}
    for x in entram:
        im = Image.open(imagens / f"{x['id']}.jpg").convert("RGB")
        buf = io.BytesIO(); im.save(buf, "JPEG", quality=82, optimize=True)
        novas[x["id"]] = "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()
    copia, antes, depois = bc.gravar_fotos(novas, "capas")
    print(f"\ngravadas {len(novas)}   chaves no .dat: {antes} -> {depois}")
    print(f"copia de seguranca: {copia.name}")
    t, c, f = bc.censo()
    print(f"CENSO: {t} livros   com capa {c}   sem capa {f}")
    print("Lembre de espelhar para as outras nuvens:  ./bin/espelhar.sh")


if __name__ == "__main__":
    main()
