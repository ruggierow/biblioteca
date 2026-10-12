#!/usr/bin/env python3
"""Propoe o pais de cada livro — para o mapa. SO PROPOE.

    ./bin/semear-pais.py                 propoe e monta a folha de revisao
    ./bin/semear-pais.py --gravar        grava a 9a coluna na base
    ./bin/semear-pais.py --gravar --so-tema   grava apenas o que veio do tema

NAO GRAVE ANTES DE A 1.9.14 ESTAR NAS QUATRO MAQUINAS. Ate a 1.9.13, Mac e
Windows DESCARTAVAM em silencio a linha com 9 colunas, e o Mac grava sozinho: um
aparelho atrasado abriria a biblioteca vazia e gravaria o vazio por cima. O
comando avisa, mas nao tem como conferir isso daqui.

AS DUAS FONTES, E POR QUE A ORDEM E ESSA

  TEMA (gentilico)  "Literatura Japonesa" -> JP. Diz de onde vem a LITERATURA.
  ISBN (prefixo)    978-85 -> BR.          Diz onde fica a EDITORA.

Nao e a mesma pergunta. Uma edicao brasileira de Tolstoi tem ISBN 978-85: pelo
ISBN ela e Brasil, pelo tema e Russia. Para um mapa do acervo, "de onde vem o
que eu leio" e mais interessante que "onde foi impresso" — e por isso o tema
vence quando os dois existem. O ISBN entra onde nao ha tema, e a folha de
revisao sempre diz de qual fonte veio cada palpite.

A TABELA E EXPLICITA, GENTILICO POR GENTILICO, e saiu dos temas que existem
nesta base — nao de regra difusa. Ha "Literatura Policial" e "Literatura" sem
complemento no acervo: uma regra por semelhanca classificaria as duas como pais.
"""
import argparse
import datetime
import html
import json
import re
import shutil
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import biblioteca_comum as bc

# gentilico normalizado -> (ISO, nome em portugues)
GENTILICOS = {
    "brasileira": ("BR", "Brasil"), "barsileira": ("BR", "Brasil"),   # erro de digitacao na base
    "americana": ("US", "Estados Unidos"), "norte americana": ("US", "Estados Unidos"),
    "francesa": ("FR", "França"), "inglesa": ("GB", "Reino Unido"), "britanica": ("GB", "Reino Unido"),
    "japonesa": ("JP", "Japão"), "italiana": ("IT", "Itália"), "alema": ("DE", "Alemanha"),
    "portuguesa": ("PT", "Portugal"), "russa": ("RU", "Rússia"), "colombiana": ("CO", "Colômbia"),
    "chilena": ("CL", "Chile"), "cubana": ("CU", "Cuba"), "argentina": ("AR", "Argentina"),
    "mexicana": ("MX", "México"), "nigeriana": ("NG", "Nigéria"), "espanhola": ("ES", "Espanha"),
    "australiana": ("AU", "Austrália"), "mocambicana": ("MZ", "Moçambique"),
    "sul africana": ("ZA", "África do Sul"), "canadense": ("CA", "Canadá"),
    "hungara": ("HU", "Hungria"), "turca": ("TR", "Turquia"), "suica": ("CH", "Suíça"),
    "dinamarquesa": ("DK", "Dinamarca"), "irlandesa": ("IE", "Irlanda"),
    "peruana": ("PE", "Peru"), "uruguaia": ("UY", "Uruguai"), "senegalesa": ("SN", "Senegal"),
    "ruandesa": ("RW", "Ruanda"), "angolana": ("AO", "Angola"), "bielorussa": ("BY", "Bielorrússia"),
    "polonesa": ("PL", "Polônia"), "belga": ("BE", "Bélgica"), "iraniana": ("IR", "Irã"),
    "israelense": ("IL", "Israel"), "palestina": ("PS", "Palestina"), "libanesa": ("LB", "Líbano"),
    "egipcia": ("EG", "Egito"), "grega": ("GR", "Grécia"), "chinesa": ("CN", "China"),
    "coreana": ("KR", "Coreia do Sul"), "indiana": ("IN", "Índia"), "sueca": ("SE", "Suécia"),
    "noruegues": ("NO", "Noruega"), "holandesa": ("NL", "Holanda"), "tcheca": ("CZ", "Tchéquia"),
    "austriaca": ("AT", "Áustria"), "escocesa": ("GB", "Reino Unido"),
}

# prefixo de ISBN -> (ISO, nome). O prefixo e o grupo de registro: alguns sao de
# IDIOMA, nao de pais (978-0 e 978-1 cobrem o mundo de lingua inglesa).
PREFIXOS = [
    ("97885", ("BR", "Brasil")), ("97865", ("BR", "Brasil")),
    ("978972", ("PT", "Portugal")), ("978989", ("PT", "Portugal")),
    ("97884", ("ES", "Espanha")), ("97888", ("IT", "Itália")),
    ("9782", ("FR", "França")), ("9783", ("DE", "Alemanha")),
    ("9784", ("JP", "Japão")), ("9785", ("RU", "Rússia")),
    ("9780", ("US", "Estados Unidos")), ("9781", ("GB", "Reino Unido")),
]

NOMES = {iso: nome for iso, nome in list(GENTILICOS.values()) + [v for _, v in PREFIXOS]}


# Temas que CONTEM um gentilico sem serem origem de nada: sao ASSUNTO.
# "Lingua Portuguesa" num dicionario Houaiss (brasileiro) virava Portugal.
TEMAS_QUE_NAO_SAO_ORIGEM = [r"\blingua\b", r"\bidioma\b", r"\bgramatica\b"]


def pelo_tema(livro):
    """O gentilico do tema, se houver — e so ele.

    A tabela e explicita de proposito. Uma regra por semelhanca classificaria
    "Literatura Policial" como pais, e ha doze livros assim nesta base.

    O que esta funcao NAO corrige: tema errado. Se a base diz que Edgar Allan
    Poe e "Literatura Inglesa", o palpite sai Reino Unido — fielmente errado. A
    folha de revisao existe para isso.
    """
    for pedaco in livro.campos[2].split(";"):
        t = bc.normal(pedaco)
        if any(re.search(x, t) for x in TEMAS_QUE_NAO_SAO_ORIGEM):
            continue
        for gent, (iso, _) in GENTILICOS.items():
            if re.search(rf"\b{re.escape(gent)}\b", t):
                return iso
    return None


def pelo_isbn(livro):
    comentarios = livro.campos[5] if len(livro.campos) > 5 else ""
    m = re.search(r"ISBN:\s*([0-9X]+)", comentarios)
    if not m:
        return None
    numero = m.group(1)
    for prefixo, (iso, _) in sorted(PREFIXOS, key=lambda x: -len(x[0])):
        if numero.startswith(prefixo):
            return iso
    return None


def folha(propostas, destino):
    por_pais = {}
    for p in propostas:
        por_pais.setdefault(p["iso"], []).append(p)
    blocos = []
    for iso in sorted(por_pais, key=lambda k: (-len(por_pais[k]), k)):
        itens = sorted(por_pais[iso], key=lambda x: bc.normal(x["titulo"]))
        blocos.append(f'<h2>{html.escape(NOMES.get(iso, iso))} '
                      f'<span class="iso">{iso}</span><span class="n">{len(itens)}</span></h2><table>')
        for p in itens:
            marca = ("tema" if p["fonte"] == "tema" else "ISBN")
            classe = "t" if p["fonte"] == "tema" else "i"
            blocos.append(
                f'<tr><td class="f {classe}">{marca}</td>'
                f'<td class="ti">{html.escape(p["titulo"])}</td>'
                f'<td class="a">{html.escape(p["autor"])}</td>'
                f'<td class="p">{html.escape(p["pista"])}</td></tr>')
        blocos.append("</table>")
    destino.write_text(f"""<!doctype html><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>País proposto por livro</title>
<style>
 body{{font:15px/1.45 -apple-system,system-ui,sans-serif;margin:0;padding:20px;background:#f4f6fb;color:#1f2937}}
 h1{{font-size:20px;margin:0 0 4px}} .sub{{color:#6b7280;font-size:13px;margin-bottom:22px;max-width:46em}}
 h2{{font-size:15px;margin:26px 0 8px;padding-bottom:5px;border-bottom:2px solid #d8dfea;color:#2b5fb3}}
 .iso{{font-size:11px;color:#9aa4b2;font-weight:400;margin-left:6px}}
 .n{{float:right;color:#6b7280;font-weight:400;font-size:13px}}
 table{{width:100%;border-collapse:collapse;background:#fff;border-radius:8px;overflow:hidden;box-shadow:0 1px 3px #0001}}
 td{{padding:6px 9px;border-bottom:1px solid #eef1f6;vertical-align:top}}
 tr:last-child td{{border-bottom:none}}
 .f{{width:3.2em;font-size:10.5px;font-weight:700;border-radius:4px;text-align:center}}
 .f.t{{color:#166b48}} .f.i{{color:#b45309}}
 .ti{{font-weight:600}} .a{{color:#4b5563;width:26%}} .p{{color:#9aa4b2;font-size:12px;width:22%}}
 @media print{{body{{background:#fff;padding:0;font-size:11px}} table{{box-shadow:none}}}}
</style>
<h1>País proposto — {len(propostas)} livros</h1>
<div class="sub">
 <b>tema</b> = deduzido do gentílico do tema; diz de onde vem a <b>literatura</b>.<br>
 <b>ISBN</b> = deduzido do começo do ISBN; diz onde fica a <b>editora</b> — uma edição
 brasileira de um autor russo aparece como Brasil. Por isso o tema vence quando os dois existem.<br>
 Gerado em {datetime.datetime.now():%d/%m/%Y %H:%M}. Nada foi gravado.
</div>
{''.join(blocos)}""", encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description="Propoe o pais de cada livro.")
    ap.add_argument("--gravar", action="store_true", help="grava a 9a coluna na base")
    ap.add_argument("--so-tema", action="store_true", help="usa apenas a pista do tema")
    a = ap.parse_args()

    livros = bc.ler_base()
    propostas, ja_tem = [], 0
    for l in livros:
        atual = l.campos[8].strip() if len(l.campos) > 8 else ""
        if atual:
            ja_tem += 1
            continue
        iso, fonte, pista = None, None, ""
        t = pelo_tema(l)
        if t:
            iso, fonte, pista = t, "tema", l.campos[2]
        elif not a.so_tema:
            i = pelo_isbn(l)
            if i:
                iso, fonte, pista = i, "isbn", re.search(r"ISBN:\s*[0-9X]+", l.campos[5]).group(0)
        if iso:
            propostas.append({"n": l.n, "iso": iso, "fonte": fonte, "pista": pista,
                              "titulo": l.titulo, "autor": l.campos[1]})

    c = Counter(p["fonte"] for p in propostas)
    print(f"base: {len(livros)} livros   ja com pais: {ja_tem}")
    print(f"propostas: {len(propostas)}   pelo tema: {c['tema']}   pelo ISBN: {c['isbn']}")
    print(f"sem pista nenhuma: {len(livros) - ja_tem - len(propostas)}")
    print()
    for iso, n in Counter(p["iso"] for p in propostas).most_common(12):
        print(f"   {iso}  {NOMES.get(iso, iso):18s} {n}")

    destino = Path.home() / "Desktop/pais-proposto.html"
    folha(propostas, destino)
    json.dump(propostas, (Path.home() / "Desktop/pais-proposto.json").open("w"),
              ensure_ascii=False, indent=1)
    print(f"\nfolha de revisao: {destino}")

    if not a.gravar:
        print("Nada foi gravado. Revise e rode de novo com --gravar.")
        return 0

    print("\nATENCAO: so grave se a 1.9.14 estiver instalada NAS QUATRO maquinas.")
    copia = bc.copia_de_seguranca(bc.BASE, "semear-pais")
    linhas = bc.BASE.read_text(encoding="utf-8").splitlines()
    por_linha = {p["n"]: p["iso"] for p in propostas}
    escritas = 0
    saida = []
    n = 0
    for bruta in linhas:
        if not bruta.strip():
            continue
        n += 1
        campos = bruta.split("\t")
        if n in por_linha:
            while len(campos) < 8:
                campos.append("")
            campos = campos[:8] + [por_linha[n]]
            escritas += 1
        saida.append("\t".join(campos))
    bc.BASE.write_text("\n".join(saida) + "\n", encoding="utf-8")

    # Portao: reler e conferir que nada se perdeu e que o pais chegou.
    depois = bc.ler_base()
    com_pais = sum(1 for l in depois if len(l.campos) > 8 and l.campos[8].strip())
    print(f"copia de seguranca: {copia.name}")
    print(f"linhas: {len(livros)} -> {len(depois)}   com pais: {ja_tem} -> {com_pais}")
    if len(depois) != len(livros):
        print("ABORTADO NA CONFERENCIA: o numero de livros mudou. Restaure a copia.")
        return 1
    print("Lembre de espelhar:  ./bin/espelhar.sh")
    return 0


if __name__ == "__main__":
    sys.exit(main())
