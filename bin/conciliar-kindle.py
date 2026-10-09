#!/usr/bin/env python3
"""Concilia a biblioteca do Kindle com biblioteca.txt.

So LE. Nunca escreve na base: produz um relatorio e um arquivo de propostas
que o usuario revisa antes de qualquer coisa entrar.

DE ONDE SAEM OS DADOS (nao precisa de login, nem de navegador, nem da Amazon)

    ~/Library/Containers/com.amazon.Lassen/Data/Library/Protected/BookData.sqlite

O app mantem o banco aberto, entao copiamos o .sqlite + -wal + -shm antes de
consultar. O XML do app classico (com.amazon.Kindle) esta velho; nao usar.

ARMADILHA: ZDISPLAYAUTHOR e irmaos sao BLOBS cifrados e saem como lixo. O autor
em texto claro esta em ZSYNCMETADATAATTRIBUTES, um bplist do NSKeyedArchiver,
com os campos sob a chave `attributes`.

ZRAWPUBLICATIONDATE e epoch Unix PURO, nao Core Data. Lido com o deslocamento
do Core Data da 2056. Sem deslocamento da a publicacao da edicao Kindle, que e
a data que o usuario adotou para o campo ano.

O QUE E LIVRO: a coluna ZRAWBOOKTYPE classifica, e e melhor que adivinhar pelo
titulo (ha dicionarios em marata e malaiala que nenhuma regra de nome pega):

    10 = livro      11 = amostra      13 = documento pessoal     16 = dicionario

Decisao do usuario (09/10/2026): a base de sincronizacao sao SO os livros (10).
Documentos pessoais (os PDFs) ficam de fora; amostras so aparecem no relatorio.

A linha representa a obra NUMA EDICAO, e o campo `local` e quem distingue:
`Kindle` de um lado, a prateleira ou a pessoa com quem o livro esta do outro.
Decisao do usuario (09/10/2026): "gostaria de distinguir a edicao impressa da
edicao do Kindle, portanto poderiamos ter o mesmo livro nas duas edicoes".

Por isso, quando a obra ja existe na base:
  - se a linha achada tem local `Kindle`, e a MESMA edicao -> so completar o link;
  - se tem qualquer outro local, aquela e a IMPRESSA -> a compra no Kindle vira
    linha nova, e o relatorio diz onde esta a impressa, para o usuario conferir
    que nao e engano.
"""
import sqlite3, plistlib, json, re, sys, shutil, tempfile, unicodedata, datetime, difflib
from pathlib import Path

BANCO = Path.home() / "Library/Containers/com.amazon.Lassen/Data/Library/Protected/BookData.sqlite"
BASE  = Path.home() / "Library/Mobile Documents/com~apple~CloudDocs/Biblioteca/biblioteca.txt"
LIVRO, AMOSTRA, DOCUMENTO, DICIONARIO = 10, 11, 13, 16


def desarquiva(blob):
    """NSKeyedArchiver -> dict. Segue os UID por $objects e desembrulha NSDictionary/NSArray."""
    p = plistlib.loads(blob)
    objs = p["$objects"]
    def anda(o):
        if isinstance(o, plistlib.UID):
            return anda(objs[o.data])
        if isinstance(o, dict):
            if "NS.keys" in o and "NS.objects" in o:
                return {anda(k): anda(v) for k, v in zip(o["NS.keys"], o["NS.objects"])}
            if "NS.objects" in o:
                return [anda(v) for v in o["NS.objects"]]
            return {k: anda(v) for k, v in o.items() if k != "$class"}
        return o
    return anda(p["$top"]["root"])


def autor_de(attr):
    """O campo `authors` vem em forma variada: texto, lista, lista de dict, lista de lista."""
    def primeiro(a):
        if isinstance(a, str):
            return a
        if isinstance(a, dict):
            return primeiro(a.get("author") or a.get("name") or "")
        if isinstance(a, (list, tuple)):
            for x in a:
                achado = primeiro(x)
                if achado:
                    return achado
        return ""
    return primeiro(attr.get("authors")).strip()


def ler_kindle():
    if not BANCO.exists():
        sys.exit(f"Nao achei o banco do Kindle em {BANCO}\n"
                 "O aplicativo Kindle do Mac precisa estar instalado e ter sincronizado ao menos uma vez.")
    tmp = Path(tempfile.mkdtemp(prefix="kindle-"))
    for sufixo in ("", "-wal", "-shm"):
        origem = Path(str(BANCO) + sufixo)
        if origem.exists():
            shutil.copy2(origem, tmp / origem.name)
    c = sqlite3.connect(tmp / BANCO.name)
    itens = []
    for tipo, pub, blob in c.execute(
            "select ZRAWBOOKTYPE, ZRAWPUBLICATIONDATE, ZSYNCMETADATAATTRIBUTES "
            "from ZBOOK where ZSYNCMETADATAATTRIBUTES is not null"):
        raiz = desarquiva(blob)
        attr = raiz.get("attributes", raiz) if isinstance(raiz, dict) else {}
        if not isinstance(attr, dict):
            continue
        ano = ""
        if pub and pub > 0:
            try:
                ano = str(datetime.datetime.utcfromtimestamp(pub).year)
            except (OverflowError, OSError, ValueError):
                ano = ""
        itens.append({"tipo": tipo, "asin": (attr.get("ASIN") or "").strip(),
                      "titulo": (attr.get("title") or "").strip(),
                      "autor": autor_de(attr), "ano": ano,
                      "compra": str(attr.get("purchase_date") or "")[:10]})
    shutil.rmtree(tmp, ignore_errors=True)
    return itens


EDICAO = re.compile(r"\s*\((?:[^()]*\b(?:edition|edicao|edição)\b[^()]*)\)\s*$", re.I)

def chave(texto):
    """Normaliza para comparar obra com obra: sem acento, sem pontuacao, sem '(Portuguese Edition)'."""
    t = EDICAO.sub("", texto or "")
    t = unicodedata.normalize("NFKD", t)
    t = "".join(ch for ch in t if not unicodedata.combining(ch)).lower()
    t = re.sub(r"[^a-z0-9 ]+", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def ler_base():
    linhas = []
    for n, ln in enumerate(BASE.read_text(encoding="utf-8").splitlines(), 1):
        if not ln.strip():
            continue
        campos = ln.split("\t")
        linhas.append({"n": n, "campos": campos, "titulo": campos[0],
                       "autor": campos[1] if len(campos) > 1 else "",
                       "asins": set(re.findall(r"(?:/dp/|asin=)([A-Z0-9]{10})", ln))})
    return linhas


def titulo_limpo(t):
    """Tira o "(Portuguese Edition)" e irmaos, que o Kindle poe e a base nao usa."""
    return EDICAO.sub("", t or "").strip()


def autor_natural(a):
    """O Kindle grava "Shibli, Adania"; a base usa "Adania Shibli"."""
    if a.count(",") == 1:
        sobrenome, nome = [x.strip() for x in a.split(",")]
        if sobrenome and nome and not re.search(r"\b(jr|filho|neto|ed|org)\b\.?$", nome, re.I):
            return f"{nome} {sobrenome}"
    return a


def comentario(asin):
    return (f"Ler: https://read.amazon.com/?asin={asin}"
            f" | Kindle: kindle://book?action=open&asin={asin}")


def main():
    itens = ler_kindle()
    base = ler_base()
    na_base = {a: l for l in base for a in l["asins"]}
    por_chave = {}
    for l in base:
        por_chave.setdefault(chave(l["titulo"]), l)

    livros = [i for i in itens if i["tipo"] == LIVRO and i["asin"]]
    conferidos = [i for i in livros if i["asin"] in na_base]
    faltando = [i for i in livros if i["asin"] not in na_base]

    def local_de(linha):
        return linha["campos"][6] if len(linha["campos"]) > 6 else ""

    novos, outra_edicao, completar = [], [], []
    for i in faltando:
        k = chave(i["titulo"])
        achada = por_chave.get(k)
        if not achada:
            perto = difflib.get_close_matches(k, por_chave.keys(), n=1, cutoff=0.90)
            achada = por_chave[perto[0]] if perto else None
        if achada is None:
            novos.append((i, None))
        elif local_de(achada) == "Kindle":
            completar.append((i, achada))     # mesma edicao, so falta o link
        else:
            outra_edicao.append((i, achada))  # a da base e a impressa

    amostras_na_base = [i for i in itens if i["tipo"] == AMOSTRA and i["asin"] in na_base]

    larg = 58
    print(f"KINDLE  livros {len(livros)}   amostras {sum(1 for i in itens if i['tipo']==AMOSTRA)}"
          f"   documentos {sum(1 for i in itens if i['tipo']==DOCUMENTO)}"
          f"   dicionarios {sum(1 for i in itens if i['tipo']==DICIONARIO)}")
    print(f"BASE    {len(base)} linhas, {len(na_base)} com endereco da Amazon")
    print()
    print(f"[=] ja conferidos (mesmo ASIN nos dois lados): {len(conferidos)}")
    print()
    print(f"[+] LIVROS NOVOS — nenhuma obra parecida na base: {len(novos)}")
    for i, _ in sorted(novos, key=lambda x: x[0]["compra"]):
        print(f"      {i['compra']:11s} {i['titulo'][:larg]:{larg}s} {i['autor'][:26]}")
    print()
    print(f"[+] EDICAO KINDLE de obra que voce ja tem IMPRESSA — linha nova: {len(outra_edicao)}")
    for i, l in outra_edicao:
        print(f"      {i['compra']:11s} {i['titulo'][:larg]:{larg}s} {i['autor'][:26]}")
        print(f"                  a impressa esta na linha {l['n']}, local: {local_de(l)}")
    print()
    print(f"[~] JA NA BASE COMO KINDLE, mas sem o link: {len(completar)}")
    for i, l in completar:
        print(f"      linha {l['n']:4d}  {l['titulo'][:larg]}")
        print(f"                  acrescentar: {comentario(i['asin'])[:72]}...")
    print()
    print(f"[!] NA BASE, mas no Kindle e AMOSTRA, nao livro comprado: {len(amostras_na_base)}")
    for i in amostras_na_base:
        print(f"      linha {na_base[i['asin']]['n']:4d}  {na_base[i['asin']]['titulo'][:larg]}")

    saida = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("propostas-kindle.tsv")
    with saida.open("w", encoding="utf-8") as f:
        for i, achada in novos + outra_edicao:
            if achada is not None:
                # A obra ja esta catalogada: o titulo, os autores e os temas sao
                # os DELA — inclusive a acentuacao, que o Kindle costuma perder.
                # Do Kindle vem so o que e da edicao: ano, os links e o local.
                campos = achada["campos"]
                linha = [campos[0], campos[1] if len(campos) > 1 else "",
                         campos[2] if len(campos) > 2 else "", i["ano"] or (campos[3] if len(campos) > 3 else ""),
                         "0", comentario(i["asin"]), "Kindle",
                         campos[7] if len(campos) > 7 else "0"]
            else:
                linha = [titulo_limpo(i["titulo"]), autor_natural(i["autor"]), "",
                         i["ano"], "0", comentario(i["asin"]), "Kindle", "0"]
            f.write("\t".join(linha) + "\n")
    print()
    print(f"Propostas de linha nova escritas em: {saida}")
    print("Nada foi escrito em biblioteca.txt.")


if __name__ == "__main__":
    main()
