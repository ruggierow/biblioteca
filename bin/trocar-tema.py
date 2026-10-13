#!/usr/bin/env python3
"""Troca um tema (e, se pedido, o pais) nos livros. SO PROPOE.

    ./bin/trocar-tema.py --de "Fotigrafia" --para "Fotografia"
    ./bin/trocar-tema.py --autor "Edgar Allan Poe" \
        --de "Literatura Inglesa" --para "Literatura Americana" --pais US
    ./bin/trocar-tema.py --uniformizar          # so caixa e acento, em bloco
    ./bin/trocar-tema.py ... --gravar

Sem `--autor`, vale para a base inteira.

`--uniformizar` junta o MESMO tema escrito de formas diferentes ("Digital
design" e "Digital Design"), mantendo a grafia que aparece mais. Ele NAO toca em
erro de digitacao: "Barsileira" e "Brasileira" sao letras diferentes, e juntar
por semelhanca erraria — "Mathematica" (o programa da Wolfram) viraria
"Matemática", e sao coisas distintas. Erro de digitacao vai no --de/--para, um a
um, com olho humano.

POR QUE UM COMANDO, E NAO A MAO NO APP

O tema e a fonte do pais: `semear-pais.py` le o gentilico ("Literatura
Japonesa" -> JP). Trocar o tema no app NAO mexe no pais — o semeador so propoe
para quem esta sem. Os dois andam juntos aqui para nao ficar uma classificacao
dizendo uma coisa e o mapa, outra.

O QUE ELE NAO FAZ, DE PROPOSITO

Nao cria tema que ja nao exista na base, nem adivinha o autor. Quem decide a
classificacao e o dono da biblioteca; isto aqui so aplica a decisao sem erro
de digitacao, em todas as linhas de uma vez.
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import biblioteca_comum as bc

VERDE, AMARELO, FIM = "\033[32m", "\033[33m", "\033[0m"


def temas(livro):
    return [t.strip() for t in livro.campos[2].split(";") if t.strip()]


def uniformizar(gravar):
    """Junta as variantes de caixa/acento, mantendo a grafia mais usada."""
    base = bc.ler_base()
    cont = {}
    for l in base:
        for t in temas(l):
            cont[t] = cont.get(t, 0) + 1

    grupos = {}
    for t, n in cont.items():
        grupos.setdefault(bc.normal(t), []).append((t, n))

    trocas = {}   # grafia a sair -> grafia a ficar
    for variantes in grupos.values():
        if len(variantes) < 2:
            continue
        variantes.sort(key=lambda x: -x[1])
        fica = variantes[0][0]
        for sai, _ in variantes[1:]:
            trocas[sai] = fica

    if not trocas:
        print("Nenhum tema escrito de mais de uma forma.")
        return 0

    print(f"{len(trocas)} grafia(s) a uniformizar:\n")
    atingidos = 0
    for sai, fica in sorted(trocas.items()):
        quantos = cont[sai]
        atingidos += quantos
        print(f'   "{sai}" ({quantos}) -> "{fica}" ({cont[fica]})')
    print(f"\n{len(cont)} temas distintos hoje; {len(grupos)} depois.")
    print(f"{atingidos} ocorrencia(s) de tema serao reescritas.")

    if not gravar:
        print("\nNada foi gravado. Confira e rode de novo com --gravar.")
        return 0

    copia = bc.copia_de_seguranca(bc.BASE, "uniformizar-temas")
    mexidos = 0
    for l in base:
        atuais = temas(l)
        novos, visto = [], set()
        for t in atuais:
            t2 = trocas.get(t, t)
            if bc.normal(t2) in visto:      # a troca pode criar repetido na linha
                continue
            visto.add(bc.normal(t2))
            novos.append(t2)
        if novos != atuais:
            l.campos[2] = "; ".join(novos)
            mexidos += 1
    bc.BASE.write_text("\n".join("\t".join(l.campos) for l in base) + "\n",
                       encoding="utf-8")
    print(f"\n{VERDE}Gravado.{FIM}  {mexidos} livro(s) alterado(s). "
          f"copia de seguranca: {copia.name}")
    return 0


def main():
    ap = argparse.ArgumentParser(description="Troca um tema nos livros.")
    ap.add_argument("--autor", help="limita a um autor; sem ele, vale para a base toda")
    ap.add_argument("--de", help="o tema a sair (comparado sem acento e sem caixa)")
    ap.add_argument("--para", help="o tema a entrar")
    ap.add_argument("--uniformizar", action="store_true",
                    help="junta as variantes de caixa/acento de cada tema")
    ap.add_argument("--pais", help="codigo ISO de 2 letras a gravar junto")
    ap.add_argument("--gravar", action="store_true")
    a = ap.parse_args()

    if a.uniformizar:
        if a.de or a.para or a.autor or a.pais:
            sys.exit("--uniformizar vai sozinho: ele decide o que trocar.")
        return uniformizar(a.gravar)
    if not (a.de and a.para):
        sys.exit("Informe --de e --para, ou use --uniformizar.")

    if a.pais and len(a.pais) != 2:
        sys.exit("O pais e o codigo ISO de DUAS letras (US, BR, GB).")
    pais = a.pais.upper() if a.pais else None

    base = bc.ler_base()
    alvo_autor, alvo_tema = bc.normal(a.autor), bc.normal(a.de)

    # O tema que ENTRA tem de ja existir na base. Um tema novo criado por engano
    # de digitacao fica orfao na lista de temas e ninguem percebe.
    todos = {bc.normal(t) for l in base for t in temas(l)}
    if bc.normal(a.para) not in todos:
        print(f"{AMARELO}AVISO{FIM}: \"{a.para}\" ainda nao existe na base. "
              f"Confira a grafia — um tema novo por engano fica orfao.")

    mudadas = []
    for l in base:
        if a.autor and not any(bc.normal(x) == alvo_autor for x in l.autores):
            continue
        atuais = temas(l)
        if not any(bc.normal(t) == alvo_tema for t in atuais):
            continue
        novos, ja_tinha = [], False
        for t in atuais:
            if bc.normal(t) == alvo_tema:
                if bc.normal(a.para) in {bc.normal(x) for x in novos}:
                    ja_tinha = True          # evita "Policial; Americana; Americana"
                    continue
                novos.append(a.para)
            else:
                novos.append(t)
        pais_antes = l.campos[8] if len(l.campos) >= 9 else ""
        mudadas.append((l, atuais, novos, pais_antes, ja_tinha))

    de_quem = f" de \"{a.autor}\"" if a.autor else ""
    if not mudadas:
        print(f"Nenhum livro{de_quem} com o tema \"{a.de}\".")
        return 1

    print(f"{len(mudadas)} livro(s){de_quem}:\n")
    for l, antes, depois, pais_antes, _ in mudadas:
        print(f"  {l.titulo}")
        print(f"     tema: {'; '.join(antes)}")
        print(f"        -> {'; '.join(depois)}")
        if pais:
            print(f"     pais: {pais_antes or '(vazio)'} -> {pais}")

    if not a.gravar:
        print("\nNada foi gravado. Confira e rode de novo com --gravar.")
        return 0

    copia = bc.copia_de_seguranca(bc.BASE, "trocar-tema")
    for l, _, depois, _, _ in mudadas:
        l.campos[2] = "; ".join(depois)
        if pais:
            while len(l.campos) < 9:
                l.campos.append("")
            l.campos[8] = pais
    bc.BASE.write_text("\n".join("\t".join(l.campos) for l in base) + "\n",
                       encoding="utf-8")
    print(f"\n{VERDE}Gravado.{FIM}  copia de seguranca: {copia.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
