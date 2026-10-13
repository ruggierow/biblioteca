#!/usr/bin/env python3
"""Confere que as QUATRO tabelas de pais concordam — codigo por codigo.

    ./bin/conferir-paises.py

AS QUATRO, e por que elas existem separadas:

    motor-web/biblioteca.html          const PAISES   (Mac e Windows)
    motor-movel/ios/.../Paises.swift   Paises.nomes   (iPhone)
    motor-movel/android/.../paises.dart  Paises._nomes (Android)
    bin/semear-pais.py                 NOMES          (a folha de revisao)

Nao ha como compartilhar uma tabela entre JavaScript embarcado, Swift, Dart e
Python sem um gerador, e um gerador para 47 linhas custaria mais do que paga.
O preco de manter as quatro a mao e a DIVERGENCIA, e ela e silenciosa: nada
quebra, o programa roda, e o mesmo livro aparece com dois nomes.

NAO E HIPOTETICO. Em 13/10/2026, ao por o campo de pais no formulario, 22 dos
47 nomes do motor-web estavam sem acento: o Mac mostrava "Mocambique",
"Africa do Sul" e "Ira" onde os dois celulares mostravam "Moçambique",
"África do Sul" e "Irã". Ninguem tinha notado, porque o codigo ISO — que e o
que a base guarda e o que o mapa casa — estava certo nas quatro.

O QUE ESTE PORTAO CONFERE

  1. o mesmo CONJUNTO de codigos nas quatro;
  2. o mesmo NOME para cada codigo (com acento, exatamente igual);
  3. que ele conferiu algo: zero tabela lida e FALHA, nao sucesso.

O item 3 e a licao de um portao anterior, que conferia ZERO unidades desde uma
renomeacao e ficava verde um dia inteiro.
"""
import io
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent

VERMELHO, VERDE, FIM = "\033[31m", "\033[32m", "\033[0m"


def do_motor_web():
    """`const PAISES = { BR: ["Brasil", -10, -55, "AMERICA DO SUL"], ...}`."""
    texto = io.open(RAIZ / "motor-web/biblioteca.html", encoding="utf-8").read()
    ini = texto.index("const PAISES = {")
    fim = texto.index("};", ini)
    return dict(re.findall(r'([A-Z]{2}): \["([^"]+)"', texto[ini:fim]))


def do_iphone():
    texto = io.open(
        RAIZ / "motor-movel/ios/Biblioteca.App/Models/Paises.swift", encoding="utf-8"
    ).read()
    bloco = texto.split("private static let nomes: [String: String] = [", 1)[1]
    bloco = bloco.split("\n    ]", 1)[0]
    return dict(re.findall(r'"([A-Z]{2})"\s*:\s*"([^"]+)"', bloco))


def do_android():
    texto = io.open(
        RAIZ / "motor-movel/android/lib/models/paises.dart", encoding="utf-8"
    ).read()
    bloco = texto.split("static const _nomes = <String, String>{", 1)[1]
    bloco = bloco.split("};", 1)[0]
    return dict(re.findall(r"'([A-Z]{2})'\s*:\s*'([^']+)'", bloco))


def do_semeador_por_leitura():
    texto = io.open(RAIZ / "bin/semear-pais.py", encoding="utf-8").read()
    gent = texto.split("GENTILICOS = {", 1)[1].split("\n}", 1)[0]
    pref = texto.split("PREFIXOS = ", 1)[1].split("\n]", 1)[0]
    nomes = {}
    for iso, nome in re.findall(r'\("([A-Z]{2})",\s*"([^"]+)"\)', gent + pref):
        nomes[iso] = nome
    return nomes


FONTES = [
    ("motor-web (Mac/Windows)", do_motor_web),
    ("iPhone", do_iphone),
    ("Android", do_android),
    ("semear-pais.py", do_semeador_por_leitura),
]


def main():
    tabelas = {}
    for nome, ler in FONTES:
        try:
            t = ler()
        except Exception as erro:            # noqa: BLE001
            print(f"{VERMELHO}FALHA{FIM}  nao consegui ler a tabela do {nome}: {erro}")
            return 1
        if not t:
            print(f"{VERMELHO}FALHA{FIM}  a tabela do {nome} saiu VAZIA — o leitor "
                  f"deve estar desatualizado. Zero nao e sucesso.")
            return 1
        tabelas[nome] = t
        print(f"   {nome}: {len(t)} pais(es)")

    problemas = []

    # 1. o mesmo conjunto de codigos. A referencia e o motor-web, que e quem
    #    desenha o mapa: um pais que ele nao conhece nao tem onde ser posto.
    base = "motor-web (Mac/Windows)"
    codigos = set(tabelas[base])
    for nome, t in tabelas.items():
        if nome == base:
            continue
        # O semeador PODE ter codigos a mais: ele propoe a partir de gentilico e
        # de prefixo de ISBN, e nem todo prefixo ja virou pais do acervo. O que
        # nao pode e o contrario — propor um pais que o mapa nao sabe posicionar.
        faltam = codigos - set(t)
        sobram = set(t) - codigos
        if faltam:
            problemas.append(f"{nome}: nao tem {', '.join(sorted(faltam))}")
        if sobram and nome != "semear-pais.py":
            problemas.append(f"{nome}: tem a mais {', '.join(sorted(sobram))}")
        if sobram and nome == "semear-pais.py":
            problemas.append(
                f"{nome}: propoe {', '.join(sorted(sobram))}, que o mapa NAO sabe "
                f"posicionar — acrescente em PAISES, no motor-web, ou a bolha "
                f"sumiria sem erro")

    # 2. o mesmo nome para cada codigo
    for iso in sorted(codigos):
        vistos = {}
        for nome, t in tabelas.items():
            if iso in t:
                vistos.setdefault(t[iso], []).append(nome)
        if len(vistos) > 1:
            partes = "; ".join(f'"{n}" em {", ".join(onde)}' for n, onde in vistos.items())
            problemas.append(f"{iso}: nomes diferentes — {partes}")

    print()
    if problemas:
        for p in problemas:
            print(f"   {VERMELHO}x{FIM}  {p}")
        print(f"\n{VERMELHO}{len(problemas)} divergencia(s).{FIM}")
        return 1

    print(f"As quatro tabelas concordam: {len(codigos)} paises, mesmo nome em todas.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
