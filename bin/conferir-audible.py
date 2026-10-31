#!/usr/bin/env python3
"""Portao do caminho do Audible: o vigia e as regras de quem entra na base.

Duas familias de defeito, as duas ja vistas neste projeto:

1. SILENCIO QUE NAO E CONFERENCIA. O vigia le um banco PARADO, nao acha nada
   porque nao ha o que achar, e responde "nada novo" todo dia com cara de estar
   funcionando — a licao `portao-que-nao-olha-passa-verde`. Em 31/10/2026 isso
   nao era hipotese: o banco do Audible estava da vespera e escondia um livro
   adicionado no dia anterior.

       banco velho  ->  NAO_OLHEI, e analisar() nem e chamada
       banco fresco ->  conclusao de verdade, SEM_NOVIDADE ou COM_NOVIDADE

2. REGRA DE ENTRADA QUE AFROUXA SOZINHA. O conciliador tem quatro decisoes do
   usuario embutidas — quem entra, o `local`, a mensagem "A ser adquirido." e o
   ano que nunca pode faltar. Aqui elas sao EXERCIDAS, com um banco de mentira,
   em vez de conferidas por leitura de prosa.

Roda sem Audible, sem rede e sem tocar em biblioteca.txt: tanto o conciliador
quanto a base sao substituidos por dubles.
"""
import importlib.util, re, sys, types
from pathlib import Path

AQUI = Path(__file__).resolve().parent
falhas = []


def carrega(nome):
    spec = importlib.util.spec_from_file_location(
        nome.replace("-", "_"), AQUI / f"{nome}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ---------------------------------------------------------------- o vigia

def duble(idade, entram=0):
    """Um conciliador de mentira, com a idade e o achado que o caso pede."""
    m = types.SimpleNamespace()
    m.chamou_analisar = False

    def analisar():
        m.chamou_analisar = True
        item = {"titulo": "T", "na_biblioteca": True}
        return {"entram": [(item, None, "2020")] * entram,
                "biblioteca": [item] * 3, "conferidos": []}

    m.idade_do_banco = lambda: idade
    m.analisar = analisar
    return m


def caso(titulo, idade, esperado, deve_analisar, **kw):
    v = carrega("vigia-audible")
    d = duble(idade, **kw)
    v.conciliador = lambda: d
    v.avisa = lambda *a, **k: None          # nao enche a tela de notificacao
    v.anota = lambda *a, **k: None          # nem o log
    obtido = v.uma_passada(abrir=False)
    nome = {0: "SEM_NOVIDADE", 10: "COM_NOVIDADE", 20: "NAO_OLHEI"}
    if obtido != esperado:
        falhas.append(f"{titulo}: esperava {nome[esperado]}, veio {nome.get(obtido, obtido)}")
    elif d.chamou_analisar != deve_analisar:
        falhas.append(f"{titulo}: analisar() foi chamada = {d.chamou_analisar}, "
                      f"devia ser {deve_analisar}")
    else:
        print(f"   ok   {titulo}")


v = carrega("vigia-audible")
print("Portao do Audible")
print(" -- o vigia")

caso("banco de 20 dias nao vira 'nada novo'", 20.0, v.NAO_OLHEI, False, entram=6)
caso("banco de 2 dias tambem reprova", 2.0, v.NAO_OLHEI, False)
caso("banco ausente reprova", None, v.NAO_OLHEI, False)
caso("banco fresco e vazio: silencio legitimo", 0.2, v.SEM_NOVIDADE, True)
caso("banco fresco com audiolivro novo avisa", 0.2, v.COM_NOVIDADE, True, entram=1)

if not 0.5 <= v.LIMITE_DIAS <= 3:
    falhas.append(f"LIMITE_DIAS={v.LIMITE_DIAS} fora do razoavel para tarefa diaria")
else:
    print(f"   ok   LIMITE_DIAS = {v.LIMITE_DIAS} dia(s)")

# O vigia escreve — o log. O que nao pode e escrever em OUTRO lugar, por isso a
# conferencia e pelo ALVO, nao pelo verbo.
fonte = (AQUI / "vigia-audible.py").read_text(encoding="utf-8")
PERMITIDOS = {"LOG"}
alvos = set(re.findall(r"(\w+)(?:\.with_suffix\([^)]*\))?\.open\(", fonte))
alvos |= set(re.findall(r"(\w+)\.write_(?:text|bytes)\(", fonte))
intrusos = alvos - PERMITIDOS
# A prosa PODE dizer "nunca escreve em biblioteca.txt" — e o que ela diz. O que
# nao pode e o codigo ALCANCAR a base. A agulha e montada em pedacos: escrita
# inteira, ela casaria com este proprio arquivo e o portao reprovaria sozinho,
# como ja aconteceu em 30/10 com o portao do espelho.
caminho_da_base = "Mobile " + "Documents"
if intrusos:
    falhas.append(f"vigia-audible.py escreve em alvo nao previsto: {sorted(intrusos)}")
elif re.search(r"\.BASE\b", fonte) or caminho_da_base in fonte:
    falhas.append("vigia-audible.py alcanca o caminho da base; ele nao deve conhece-lo")
else:
    print(f"   ok   o vigia so escreve em {sorted(PERMITIDOS)}, nunca na base")


# ------------------------------------------------- as regras de quem entra

print(" -- as regras de entrada")
ca = carrega("conciliar-audible")

PRODUTOS = [
    # na_biblioteca, consumivel, para_sempre
    dict(asin="AAAAAAAAAA", tipo="Product", titulo="Comprado", autores=["Autor Um"],
         narradores=["Voz"], ano_audio="2024", na_biblioteca=True,
         consumivel=True, para_sempre=True),
    dict(asin="BBBBBBBBBB", tipo="Product", titulo="Do plano", autores=["Autor Dois"],
         narradores=[], ano_audio="2026", na_biblioteca=False,
         consumivel=True, para_sempre=False),
    dict(asin="CCCCCCCCCC", tipo="Product", titulo="Pago", autores=["Autor Tres"],
         narradores=[], ano_audio="2026", na_biblioteca=False,
         consumivel=False, para_sempre=False),
    dict(asin="DDDDDDDDDD", tipo="Show", titulo="Do plano", autores=["Podcast"],
         narradores=[], ano_audio="2026", na_biblioteca=False,
         consumivel=True, para_sempre=False),
    dict(asin="EEEEEEEEEE", tipo="Product", titulo="So no Audible", autores=["Autor Cinco"],
         narradores=[], ano_audio="", na_biblioteca=True,
         consumivel=True, para_sempre=False),
    dict(asin="FFFFFFFFFF", tipo="Product", titulo="Ja cadastrado", autores=["Autor Seis"],
         narradores=[], ano_audio="2020", na_biblioteca=True,
         consumivel=True, para_sempre=True),
]
# A base de mentira: 9 campos, como a de verdade.
def l(n, titulo, local, ano, temas="", pais="", comentarios=""):
    return {"n": n, "campos": [titulo, "Autor", temas, ano, "0", comentarios, local, "0", pais],
            "titulo": titulo,
            "asins": set(re.findall(r"audible\.com\.br/pd/([A-Za-z0-9]+)", comentarios))}

BASE = [
    l(1, "Comprado", "Prateleira", "1950", "Tema", "BR"),
    l(2, "Do plano", "Grupo de Literatura", "1912", "Tema alemao", "DE"),
    l(3, "Do plano", "Kindle", "2018"),            # a do Kindle nao pode ganhar
    l(4, "Pago", "Prateleira", "2001"),
    l(5, "Ja cadastrado", "Prateleira", "1999",
      comentarios="Ouvir: https://www.audible.com.br/pd/FFFFFFFFFF"),
]
ca.ler_audible = lambda: [dict(p) for p in PRODUTOS]
ca.ler_base = lambda: [dict(x, campos=list(x["campos"])) for x in BASE]
r = ca.analisar()
entrou = {i["asin"]: (i, fonte, ano) for i, fonte, ano in r["entram"]}


def exige(titulo, condicao, detalhe=""):
    if condicao:
        print(f"   ok   {titulo}")
    else:
        falhas.append(f"{titulo}{': ' + detalhe if detalhe else ''}")


exige("o comprado entra", "AAAAAAAAAA" in entrou)
exige("o incluso no plano, estando na base, entra", "BBBBBBBBBB" in entrou)
exige("o PAGO fora da biblioteca nao entra",
      "CCCCCCCCCC" not in entrou and len(r["pagos"]) == 1)
exige("podcast nunca entra", "DDDDDDDDDD" not in entrou)
exige("quem ja tem o ASIN na base nao entra de novo", "FFFFFFFFFF" not in entrou)
exige("sem ano em lugar nenhum, segura e avisa",
      "EEEEEEEEEE" not in entrou and len(r["sem_ano"]) == 1)

if "BBBBBBBBBB" in entrou:
    i, fonte, ano = entrou["BBBBBBBBBB"]
    exige("a fonte e a linha IMPRESSA, nao a do Kindle",
          fonte["n"] == 2, f"veio a linha {fonte['n']}")
    exige("o ano vem da obra, nao do audiolivro",
          ano == "1912", f"veio {ano}")

# A conferencia de forma de TODA linha proposta. Junta os problemas numa lista
# PROPRIA: a primeira versao olhava a lista geral de falhas e, bastando haver
# qualquer falha anterior, acusava a forma das linhas tambem — relatorio que
# culpa o inocente.
torto = []
for asin, (i, fonte, ano) in entrou.items():
    linha = ca.linha_de(i, fonte, ano)
    if len(linha) != 9:
        torto.append(f"{i['titulo']}: linha com {len(linha)} campos, deviam ser 9")
    if not linha[3].strip():
        torto.append(f"{i['titulo']}: ano VAZIO — a pagina descarta a linha")
    if linha[6] != ca.LOCAL:
        torto.append(f"{i['titulo']}: local {linha[6]!r}, devia ser {ca.LOCAL!r}")
falhas.extend(torto)
exige(f"toda linha proposta tem 9 campos, ano e local {ca.LOCAL!r}", not torto)

comprado = ca.comentario(PRODUTOS[0])
do_plano = ca.comentario(PRODUTOS[1])
exige("o que NAO e seu leva a mensagem", ca.A_ADQUIRIR in do_plano, do_plano)
exige("o que ja e seu NAO leva a mensagem", ca.A_ADQUIRIR not in comprado, comprado)

# O link do Audible e o da web porque `audible://` nao tem rota para o titulo
# (medido em 31/10/2026). E vai SEM a forma de consulta de proposito: o
# conciliador do Kindle reconhece ASIN por `/dp/` ou pela chave de consulta, e
# com ela passaria a tratar ASIN de audiolivro como ASIN de Kindle.
COMO_O_KINDLE_LE = r"(?:/dp/|asin=)([A-Z0-9]{10})"
exige("o link abre o titulo na web", "audible.com.br/pd/AAAAAAAAAA" in comprado, comprado)
exige("o link do Audible NAO e lido pelo conciliador do Kindle",
      not re.search(COMO_O_KINDLE_LE, comprado), comprado)
# E a volta: o portao tem de reprovar se um dia alguem puser a chave de consulta.
exige("a conferencia acima pega de verdade uma forma de consulta",
      bool(re.search(COMO_O_KINDLE_LE, "pd/?" + "asin=AAAAAAAAAA")))

if falhas:
    print("\nFALHOU:")
    for f in falhas:
        print(f"   {f}")
    sys.exit(1)
print("\nPortao do Audible: tudo verde.")
