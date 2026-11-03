#!/usr/bin/env python3
"""Concilia a biblioteca do Audible com biblioteca.txt.

So LE. Nunca escreve na base: produz um relatorio e um arquivo de propostas
que o usuario revisa antes de qualquer coisa entrar.

DE ONDE SAEM OS DADOS (sem login, sem navegador, sem rede)

    ~/Library/Containers/com.audible.iphone/Data/Library/
        Application Support/amzn1.account.<conta>-BR-library.sqlite

E um SQLite comum, bem mais facil que o do Kindle: texto claro e JSON, sem
NSKeyedArchiver. Ha tambem um `anonymous-*.sqlite` ao lado, que e a sessao sem
conta — nunca e esse. Copiamos .sqlite + -wal + -shm antes de consultar.

A ARMADILHA: `products` NAO E A BIBLIOTECA

A tabela `products` (174 linhas em 31/10/2026) e o CACHE DE CATALOGO: tudo que
passou pela tela do aplicativo. Em 30/10 eu quase propus importar 122 titulos
por ler essa tabela como se fosse a biblioteca. A biblioteca de verdade tem 3.
Quem separa:

    library_item                                    esta na sua biblioteca
    user_products.customerEntitlements_
        consumableIndefinitely = 1                  comprado, e seu para sempre
        consumable             = 1                  incluso no plano: acesso
    tudo 0                                          nenhum direito: e pago

REGRA DE ENTRADA (decisao do usuario, 31/10/2026)

Entra o que esta na biblioteca do Audible DELE, ou o que ja esta no
biblioteca.txt e e gratuito pelo plano. O que e pago e ele nao comprou fica de
fora e so aparece no relatorio — ele decide se compra.

Tudo que entra recebe `local` = "Audio book". O que ele ainda NAO possui
(`consumableIndefinitely` != 1) leva "A ser adquirido." nos comentarios.

O LIMITE QUE PRECISA FICAR CLARO

So enxergamos os produtos em cache. Um livro da base disponivel no Audible que
nunca passou pela tela do aplicativo e INVISIVEL daqui. Responder isso para os
751 exigiria consultar o catalogo pela rede — outro trabalho, e maior.

O LINK E O DA WEB, DE PROPOSITO

O esquema `audible://` nao tem rota para o titulo: testei
`view?section=current&asin=`, `open?asin=` e `pageType=partner-pdp` em
31/10/2026 e as tres abrem a BIBLIOTECA, nao o livro — a mesma historia do
`kindle://`, ja anotada em motor-movel/android/lib/views/detalhe_view.dart.
Quem abre o titulo e `https://www.audible.com.br/pd/<ASIN>` (301 para a pagina
do livro, medido).

E o link vai SEM `?asin=` de proposito: o conciliador do Kindle reconhece ASIN
por `/dp/` ou `asin=`, e com a forma de consulta ele passaria a confundir ASIN
de audiolivro com ASIN de Kindle.
"""
import sqlite3, json, re, sys, shutil, tempfile, unicodedata, datetime, difflib
from pathlib import Path

CONTAINER = (Path.home() / "Library/Containers/com.audible.iphone/Data/Library"
                           "/Application Support")
BASE = Path.home() / "Library/Mobile Documents/com~apple~CloudDocs/Biblioteca/biblioteca.txt"
LOCAL = "Audio book"
A_ADQUIRIR = "A ser adquirido."
MAX_CREDITOS = 3          # acima disso o comentario fica ilegivel na tela


def banco():
    """O .sqlite da CONTA. O `anonymous-*` ao lado e a sessao sem login."""
    achados = sorted(CONTAINER.glob("amzn1.account.*-BR-library.sqlite"))
    return achados[0] if achados else None


def idade_do_banco():
    """Quantos dias desde a ultima escrita do Audible. O -wal recebe primeiro."""
    b = banco()
    if b is None:
        return None
    maior = 0
    for sufixo in ("", "-wal", "-shm"):
        a = Path(str(b) + sufixo)
        if a.exists():
            maior = max(maior, a.stat().st_mtime)
    if not maior:
        return None
    return (datetime.datetime.now().timestamp() - maior) / 86400


def nomes(campo):
    """`authors` e `narrators` vem como JSON [{name:...}, ...]."""
    try:
        return [x.get("name", "").strip() for x in json.loads(campo or "[]")
                if isinstance(x, dict) and x.get("name")]
    except (ValueError, TypeError):
        return []


def ler_audible():
    b = banco()
    if b is None:
        sys.exit(f"Nao achei a biblioteca do Audible em {CONTAINER}\n"
                 "O aplicativo Audible precisa estar instalado e ter entrado na conta.")
    tmp = Path(tempfile.mkdtemp(prefix="audible-"))
    for sufixo in ("", "-wal", "-shm"):
        origem = Path(str(b) + sufixo)
        if origem.exists():
            shutil.copy2(origem, tmp / origem.name)
    c = sqlite3.connect(tmp / b.name)
    na_biblioteca = {a for (a,) in c.execute("select asin from library_item")}
    itens = []
    for (asin, tipo, titulo, autores, narradores, lancamento,
         consumivel, para_sempre) in c.execute(
            "select p.asin, p.contentType, p.title, p.authors, p.narrators,"
            " p.releaseDate, u.customerEntitlements_consumable,"
            " u.customerEntitlements_consumableIndefinitely"
            " from products p left join user_products u on u.asin = p.asin"):
        itens.append({"asin": asin, "tipo": tipo, "titulo": (titulo or "").strip(),
                      "autores": nomes(autores), "narradores": nomes(narradores),
                      # O ano do AUDIOLIVRO, nao o da obra: ha varios 2026 para
                      # classicos. So serve quando a obra nao esta catalogada.
                      "ano_audio": (lancamento or "")[:4],
                      "na_biblioteca": asin in na_biblioteca,
                      "consumivel": consumivel == 1,
                      "para_sempre": para_sempre == 1})
    shutil.rmtree(tmp, ignore_errors=True)
    return itens


def chave(texto):
    """Normaliza para comparar obra com obra: sem acento e sem pontuacao."""
    t = unicodedata.normalize("NFKD", texto or "")
    t = "".join(ch for ch in t if not unicodedata.combining(ch)).lower()
    t = re.sub(r"[^a-z0-9 ]+", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def ler_base():
    linhas = []
    for n, ln in enumerate(BASE.read_text(encoding="utf-8").splitlines(), 1):
        if not ln.strip():
            continue
        campos = (ln.split("\t") + [""] * 9)[:9]
        linhas.append({"n": n, "campos": campos, "titulo": campos[0],
                       # O identificador INTEIRO: com tamanho fixo, um mais
                       # longo casaria so em parte e o audiolivro ja cadastrado
                       # seria proposto de novo.
                       "asins": set(re.findall(r"audible\.com\.br/pd/([A-Za-z0-9]+)", ln))})
    return linhas


def comentario(item):
    """O link PRIMEIRO, depois a mensagem e os creditos.

    A ordem nao e estetica. A celula de comentario da tabela corta em tres
    linhas, e em 03/11/2026 o link ficava FORA do corte em toda largura de
    janela: a caixa tem 59 px e o link comecava em y=60. No Mac ele ainda
    aparecia — o WebKit desenha o ultimo elemento depois das reticencias — e no
    Windows nao, porque o WebView2 e Chromium e corta. Mesmo HTML, motores
    diferentes, e o usuario via o recurso faltando so numa das maquinas.

    Com o endereco na frente, o rotulo cabe na primeira linha em qualquer
    motor. E a mesma ordem que o Kindle ja usava, com o `Ler:` na frente.
    """
    partes = [f"Ouvir: https://www.audible.com.br/pd/{item['asin']}"]
    if not item["para_sempre"]:
        partes.append(A_ADQUIRIR)
    extras = item["autores"][1:]
    if extras:
        texto = ", ".join(extras[:MAX_CREDITOS])
        if len(extras) > MAX_CREDITOS:
            texto += " e outros"
        partes.append("Outros creditos: " + texto)
    if item["narradores"]:
        texto = ", ".join(item["narradores"][:MAX_CREDITOS])
        if len(item["narradores"]) > MAX_CREDITOS:
            texto += " e outros"
        partes.append("Narrado por " + texto)
    return " | ".join(partes)


def fonte_de(achadas):
    """Qual linha da base empresta titulo, autor, tema, grupo e pais.

    A impressa, quando existe: e ela que tem tema e pais, e o ano da OBRA. A do
    Kindle so e usada quando nao ha outra — foi o caso do Brás Cubas, que entra
    com o ano da edicao Kindle por nao haver linha da obra na base.
    """
    for l in achadas:
        if l["campos"][6] not in ("Kindle", LOCAL):
            return l
    return achadas[0] if achadas else None


def analisar():
    """Concilia e DEVOLVE o resultado, sem imprimir nada. Quem imprime e o main().

    Separado da impressao para o vigia (bin/vigia-audible.py) reusar as MESMAS
    regras, em vez de haver uma segunda copia delas por ai.
    """
    itens = ler_audible()
    base = ler_base()
    ja = {a: l for l in base for a in l["asins"]}
    por_chave = {}
    for l in base:
        por_chave.setdefault(chave(l["titulo"]), []).append(l)

    livros = [i for i in itens if i["tipo"] == "Product" and i["asin"]]
    conferidos = [i for i in livros if i["asin"] in ja]

    entram, pagos, sem_ano = [], [], []
    for i in livros:
        if i["asin"] in ja:
            continue
        k = chave(i["titulo"])
        achadas = por_chave.get(k)
        if not achadas:
            perto = difflib.get_close_matches(k, por_chave.keys(), n=1, cutoff=0.90)
            achadas = por_chave[perto[0]] if perto else []
        fonte = fonte_de(achadas)
        if not (i["na_biblioteca"] or (achadas and i["consumivel"])):
            if achadas:
                pagos.append((i, fonte))     # na base, mas pago: ele decide
            continue
        ano = (fonte["campos"][3] if fonte else "") or i["ano_audio"]
        if not ano:
            # Ano vazio DERRUBA a linha no leitor da pagina (parseInt -> NaN).
            # Melhor segurar e dizer em voz alta do que escrever linha que some.
            sem_ano.append((i, fonte))
            continue
        entram.append((i, fonte, ano))

    return {"itens": itens, "base": base, "ja": ja, "livros": livros,
            "conferidos": conferidos, "entram": entram, "pagos": pagos,
            "sem_ano": sem_ano,
            "biblioteca": [i for i in livros if i["na_biblioteca"]]}


def linha_de(item, fonte, ano):
    """A linha TSV proposta: a obra vem da base, a edicao em audio vem do Audible."""
    if fonte is not None:
        c = fonte["campos"]
        return [c[0], c[1], c[2], ano, "0", comentario(item), LOCAL, c[7] or "0", c[8]]
    return [item["titulo"], item["autores"][0] if item["autores"] else "", "",
            ano, "0", comentario(item), LOCAL, "0", ""]


def main():
    r = analisar()
    larg = 46
    tipos = {}
    for i in r["itens"]:
        tipos[i["tipo"]] = tipos.get(i["tipo"], 0) + 1
    print(f"AUDIBLE  cache de catalogo: {len(r['itens'])} produtos  "
          + "  ".join(f"{t} {n}" for t, n in sorted(tipos.items())))
    print(f"         SUA BIBLIOTECA: {len(r['biblioteca'])} titulo(s)")
    print(f"BASE     {len(r['base'])} linhas, {len(r['ja'])} ja com audiolivro")
    print()
    print(f"[=] ja conferidos (mesmo ASIN nos dois lados): {len(r['conferidos'])}")
    print()
    print(f"[+] ENTRAM — linha nova em audio: {len(r['entram'])}")
    for i, fonte, ano in r["entram"]:
        onde = "biblioteca" if i["na_biblioteca"] else "plano"
        de = (f"base l.{fonte['n']}" if fonte else "NOVO na base")
        aviso = "" if fonte else "  <- ano do AUDIOLIVRO, nao da obra"
        print(f"      {onde:10s} {i['titulo'][:larg]:{larg}s} {ano}  {de}{aviso}")
    print()
    print(f"[$] NA BASE, mas PAGO no Audible — voce decide se compra: {len(r['pagos'])}")
    for i, fonte in r["pagos"]:
        print(f"      {i['titulo'][:larg]:{larg}s} base l.{fonte['n'] if fonte else '?'}")
    print()
    if r["sem_ano"]:
        print(f"[!] SEGUREI por nao ter ano — a pagina descarta linha sem ano: {len(r['sem_ano'])}")
        for i, _ in r["sem_ano"]:
            print(f"      {i['titulo'][:larg]}")
        print()

    saida = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("propostas-audible.tsv")
    with saida.open("w", encoding="utf-8") as f:
        for i, fonte, ano in r["entram"]:
            f.write("\t".join(linha_de(i, fonte, ano)) + "\n")
    print(f"Propostas de linha nova escritas em: {saida}")
    print("Nada foi escrito em biblioteca.txt.")


if __name__ == "__main__":
    main()
