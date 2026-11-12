#!/usr/bin/env python3
"""Portao das figuras geradas: a do manual ainda e a tela de hoje?

    ./bin/conferir-figuras.py              gera e compara (precisa do Chromium)
    ./bin/conferir-figuras.py --sem-gerar  compara o que ja esta em dist/figuras

POR QUE ELE EXISTE. Em 12/11/2026, poucas horas depois de as figuras do Mac e
do Windows virarem SAIDA do `gerar-figuras.js`, o texto da pagina mudou (os
acentos que faltavam) e **as 34 figuras ficaram velhas no mesmo instante**. Eu
so percebi porque estava olhando. Da proxima vez ninguem estaria.

E a mesma familia do `conferir-pagina.py`, que compara a pagina publicada com
o que o gerador produz hoje. Aqui o alvo e a figura dentro do manual.

COMO ELE COMPARA: byte a byte. O desenho e deterministico — duas passadas
seguidas produzem PNG identico, medido em 12/11 com 46 arquivos —, entao
qualquer diferenca e mudanca de verdade na pagina, nao ruido de fonte.

O QUE ELE NAO OLHA, de proposito: as figuras que NAO saem do gerador — as
quatro telas de celular e o instalador do Windows. Aquelas sao captura de
aparelho e de sistema; para elas a pergunta "mudou?" se responde abrindo o
aparelho, e esta medida em 12/11 (ver a licao das figuras geradas).

O NOME DO ARQUIVO E O CONTRATO: `dist/figuras/<manual>--NN.png` e a imagem de
numero NN daquele manual. Nao ha tabela repetida aqui — repetir a lista de
figuras criaria duas verdades, e a deste portao seria a que ninguem corrige.
"""
import base64
import re
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DOCS = RAIZ / "docs"
FIGURAS = RAIZ / "dist" / "figuras"

falhas, oks = [], []


def reprova(m):
    falhas.append(m)
    print(f"   FALHOU: {m}")


def passa(m):
    oks.append(m)


def imagens_do_manual(nome):
    """As imagens embutidas no manual, em ordem, ja decodificadas."""
    html = (DOCS / f"{nome}.html").read_text()
    return [base64.b64decode(u) for u in
            re.findall(r'data:image/\w+;base64,([^"\')]+)', html)]


def main():
    if "--sem-gerar" not in sys.argv[1:]:
        print("--- desenhando as figuras (sem tocar nos manuais) ---")
        r = subprocess.run(["node", str(RAIZ / "bin" / "gerar-figuras.js"),
                            "--nao-trocar"], capture_output=True, text=True)
        if r.returncode != 0:
            print(r.stdout[-2000:])
            print(r.stderr[-2000:])
            print("\nREPROVADO: o gerador nao rodou — nao conferi nada.")
            return 1

    print("--- a figura do manual x a tela de hoje ---")
    arquivos = sorted(FIGURAS.glob("manual-*--*.png"))
    if not arquivos:
        reprova("nao ha figura gerada em dist/figuras — rode sem --sem-gerar")
    cache = {}
    for arq in arquivos:
        manual, numero = arq.stem.rsplit("--", 1)
        n = int(numero)
        if manual not in cache:
            if not (DOCS / f"{manual}.html").exists():
                reprova(f"{arq.name}: nao existe docs/{manual}.html")
                continue
            cache[manual] = imagens_do_manual(manual)
        imagens = cache[manual]
        if n > len(imagens):
            reprova(f"{manual} nao tem figura {n} (tem {len(imagens)})")
        elif imagens[n - 1] != arq.read_bytes():
            reprova(f"{manual} figura {n}: a do manual NAO e a tela de hoje. "
                    f"Rode ./bin/gerar-figuras.js e refaca os PDFs")
        else:
            passa(f"{manual} figura {n}")

    print(f"   ({len(oks)} figura(s) conferida(s))")
    print()
    if falhas:
        print(f"REPROVADO: {len(falhas)} figura(s) fora de dia.")
        return 1
    print("As figuras geradas sao a tela de hoje.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
