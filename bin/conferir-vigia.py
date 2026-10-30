#!/usr/bin/env python3
"""Portao do vigia do Kindle: silencio tem de significar "conferi e nao ha".

A familia de defeito que este portao existe para pegar (ja nos pegou nove
vezes neste projeto, ver a licao `portao-que-nao-olha-passa-verde`): o vigia
le um banco PARADO, nao acha livro novo porque nao ha o que achar, e responde
"nada novo" todo dia com cara de estar funcionando.

Em 30/10/2026 isso nao era hipotese: o banco do Kindle estava com 20 dias e
escondia um livro comprado em 18/10. Logo:

    banco velho  ->  NAO_OLHEI, e analisar() nem e chamada
    banco fresco ->  conclusao de verdade, SEM_NOVIDADE ou COM_NOVIDADE

Roda sem Kindle, sem rede e sem tocar em biblioteca.txt: o conciliador e
substituido por um dublê.
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


def duble(idade, novos=0, outra=0, completar=0):
    """Um conciliador de mentira, com a idade e o achado que o caso pede."""
    m = types.SimpleNamespace()
    m.chamou_analisar = False

    def analisar():
        m.chamou_analisar = True
        livro = {"compra": "2026-10-18", "titulo": "T", "autor": "A"}
        linha = {"n": 1, "titulo": "T"}
        return {"novos": [(livro, None)] * novos,
                "outra_edicao": [(livro, linha)] * outra,
                "completar": [(livro, linha)] * completar,
                "livros": [livro] * 10, "conferidos": [livro] * 10}

    m.idade_do_banco = lambda: idade
    m.analisar = analisar
    return m


def caso(titulo, idade, esperado, deve_analisar, **kw):
    v = carrega("vigia-kindle")
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


v = carrega("vigia-kindle")
print("Portao do vigia do Kindle")

# O caso que da nome ao portao.
caso("banco de 20 dias nao vira 'nada novo'", 20.0, v.NAO_OLHEI, False, novos=3)
caso("banco de 2 dias tambem reprova", 2.0, v.NAO_OLHEI, False)
caso("banco ausente reprova", None, v.NAO_OLHEI, False)
caso("banco fresco e vazio: silencio legitimo", 0.2, v.SEM_NOVIDADE, True)
caso("banco fresco com livro novo avisa", 0.2, v.COM_NOVIDADE, True, novos=1)
caso("edicao Kindle de impresso tambem conta", 0.2, v.COM_NOVIDADE, True, outra=1)
caso("linha sem o link tambem conta", 0.2, v.COM_NOVIDADE, True, completar=1)

# O limite tem de ser folgado o bastante para a tarefa diaria nao gritar sozinha.
if not 0.5 <= v.LIMITE_DIAS <= 3:
    falhas.append(f"LIMITE_DIAS={v.LIMITE_DIAS} fora do razoavel para tarefa diaria")
else:
    print(f"   ok   LIMITE_DIAS = {v.LIMITE_DIAS} dia(s)")

# E a regra que vale para todo este caminho: o vigia nunca escreve na base.
# Escrever ele escreve — o log e o plist do agendamento. O que nao pode e
# escrever em OUTRO lugar, por isso a conferencia e pelo ALVO, nao pelo verbo.
# (A primeira versao desta regra casava qualquer `open(..."w")` e reprovou a
#  gravacao do plist. Portao estrito demais reprova em voz alta, que e o lado
#  certo de errar — mas nao serve como portao.)
fonte = (AQUI / "vigia-kindle.py").read_text(encoding="utf-8")
PERMITIDOS = {"LOG", "AGENDA"}
alvos = set(re.findall(r"(\w+)(?:\.with_suffix\([^)]*\))?\.open\(", fonte))
alvos |= set(re.findall(r"(\w+)\.write_(?:text|bytes)\(", fonte))
intrusos = alvos - PERMITIDOS
if intrusos:
    falhas.append(f"vigia-kindle.py escreve em alvo nao previsto: {sorted(intrusos)}")
elif re.search(r"\.BASE\b|Mobile Documents", fonte):
    # A prosa PODE dizer "nunca escreve em biblioteca.txt" — e o que ela diz.
    # O que nao pode e o codigo ALCANCAR a base: nem `ck.BASE`, nem o caminho.
    falhas.append("vigia-kindle.py alcanca o caminho da base; ele nao deve conhece-lo")
else:
    print(f"   ok   o vigia so escreve em {sorted(PERMITIDOS)}, nunca na base")

if falhas:
    print("\nFALHOU:")
    for f in falhas:
        print(f"   {f}")
    sys.exit(1)
print("\nPortao do vigia: tudo verde.")
