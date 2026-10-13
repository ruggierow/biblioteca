#!/usr/bin/env python3
"""Diz o que o DESTINO tem e a ORIGEM nao — antes de a copia apagar.

Usado pelo `espelhar.sh`. Sozinho nao serve para muita coisa.

    conferir_destino.py <origem> <destino>          # so informa
    conferir_destino.py <origem> <destino> --trazer # traz para a origem

Sai com 0 quando o destino nao tem nada exclusivo (pode copiar por cima), e com
1 quando tem (copiar apagaria). Com `--trazer`, acrescenta o que falta na
ORIGEM — com copia de seguranca antes — e ai sai com 0.

POR QUE EXISTE: o espelho e de mao unica, iCloud -> nuvens, mas o Android
ESCREVE na copia do Drive, que e a pasta que ele tem vinculada. Entao tudo que
o usuario cadastra no celular vive so la ate alguem trazer. Em 10/10/2026 ele
leu um codigo de barras no Samsung e a linha nova existia so no Drive: espelhar
naquele momento a teria apagado, em silencio.

Duas formas de arquivo, duas comparacoes:
  .txt  -> por LIVRO, identificado por titulo+autores
  .json / .dat -> conjunto de CHAVES do objeto no topo

NAO BASTA COMPARAR LINHAS, e por duas razoes que custaram caro em 13/10/2026:

  FALSO ALARME. Um livro EDITADO na origem vira, na comparacao por linha, "uma
  linha sumiu e outra apareceu" — e o guarda recusava o espelho inteiro. Quem
  edita na mesa ve "RECUSADO" toda vez e aprende a rodar --forcar sem olhar.
  Guarda que grita a toa deixa de ser guarda.

  E PIOR: com --trazer, a linha VELHA do destino era acrescentada de volta a
  origem. O livro passava a existir DUAS vezes, um com a edicao e outro sem.

Entao a comparacao e por LIVRO, e separa dois casos bem diferentes:

  AUSENTE   o destino tem um livro que a origem nao tem de forma nenhuma.
            E o caso real: alguem cadastrou no celular. Copiar APAGARIA.
  ALTERADO  o mesmo livro existe dos dois lados, com campos diferentes.
            Nenhum livro some; o que se perde e a versao de um dos lados.

Os dois recusam a copia — nao da para saber daqui quem editou por ultimo —, mas
dizem coisas diferentes, e so o AUSENTE e trazido pelo --trazer.
"""
import json, shutil, sys, datetime, unicodedata
from pathlib import Path


def linhas(p):
    return [l for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


def normal(s):
    s = unicodedata.normalize("NFKD", s.strip().lower())
    return " ".join("".join(c for c in s if not unicodedata.combining(c)).split())


def identidade(linha):
    """Titulo + autores — a mesma identidade que gera o id da capa."""
    campos = linha.split("\t")
    titulo = normal(campos[0]) if campos else ""
    autores = tuple(sorted(normal(a) for a in (campos[1] if len(campos) > 1 else "").split(";") if a.strip()))
    return (titulo, autores)


def chaves(p):
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None            # ilegivel: nao da para comparar, e melhor dizer isso
    return d if isinstance(d, dict) else None


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    origem, destino = Path(sys.argv[1]), Path(sys.argv[2])
    trazer = "--trazer" in sys.argv[3:]
    if not destino.exists() or not origem.exists():
        return 0               # nada a perder

    if origem.suffix == ".txt":
        o, d = linhas(origem), linhas(destino)
        na_origem = {identidade(l) for l in o}
        iguais = set(o)
        ausentes  = [l for l in d if l not in iguais and identidade(l) not in na_origem]
        alterados = [l for l in d if l not in iguais and identidade(l) in na_origem]
        if not ausentes and not alterados:
            return 0

        def listar(rotulo, quais):
            print(f"      {len(quais)} {rotulo}:")
            for l in quais[:5]:
                print(f"         {l.split(chr(9))[0][:60]}")
            if len(quais) > 5:
                print(f"         … e mais {len(quais) - 5}")

        if ausentes:
            listar("livro(s) existem SO no destino", ausentes)
        if alterados:
            listar("livro(s) estao DIFERENTES dos dois lados (nenhum sumiria)", alterados)

        if not trazer:
            return 1
        if not ausentes:
            print("      nada a trazer: os livros acima existem na origem, so com "
                  "campos diferentes.")
            print("      Decida qual lado vale e rode com --forcar; trazer de volta a "
                  "versao do destino criaria o livro DUAS vezes.")
            return 1
        copia = origem.parent / (f"{origem.stem}_antes-de-trazer-do-destino_"
                                 f"{datetime.datetime.now():%Y%m%d_%H%M}{origem.suffix}")
        shutil.copy2(origem, copia)
        origem.write_text("\n".join(o + ausentes) + "\n", encoding="utf-8")
        print(f"      trazidos para a origem ({len(ausentes)}). Copia: {copia.name}")
        if alterados:
            print(f"      {len(alterados)} alterado(s) NAO foram trazidos — ver acima.")
            return 1
        return 0

    o, d = chaves(origem), chaves(destino)
    if o is None or d is None:
        print("      nao consegui ler como JSON — nao vou copiar por cima no escuro")
        return 1
    faltam = [k for k in d if k not in o]
    if not faltam:
        return 0
    print(f"      {len(faltam)} chave(s) existem SO no destino: {', '.join(faltam[:4])}"
          + (" …" if len(faltam) > 4 else ""))
    if not trazer:
        return 1
    copia = origem.parent / (f"{origem.stem}_antes-de-trazer-do-destino_"
                             f"{datetime.datetime.now():%Y%m%d_%H%M}{origem.suffix}")
    shutil.copy2(origem, copia)
    for k in faltam:
        o[k] = d[k]
    origem.write_text(json.dumps(o, ensure_ascii=False), encoding="utf-8")
    print(f"      trazidas para a origem ({len(faltam)}). Copia: {copia.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
