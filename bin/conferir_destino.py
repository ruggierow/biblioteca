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
  .txt  -> conjunto de LINHAS
  .json / .dat -> conjunto de CHAVES do objeto no topo
"""
import json, shutil, sys, datetime
from pathlib import Path


def linhas(p):
    return [l for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


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
        so_no_destino = [l for l in d if l not in set(o)]
        if not so_no_destino:
            return 0
        print(f"      {len(so_no_destino)} linha(s) existem SO no destino:")
        for l in so_no_destino[:5]:
            print(f"         {l.split(chr(9))[0][:60]}")
        if len(so_no_destino) > 5:
            print(f"         … e mais {len(so_no_destino) - 5}")
        if not trazer:
            return 1
        copia = origem.parent / (f"{origem.stem}_antes-de-trazer-do-destino_"
                                 f"{datetime.datetime.now():%Y%m%d_%H%M}{origem.suffix}")
        shutil.copy2(origem, copia)
        origem.write_text("\n".join(o + so_no_destino) + "\n", encoding="utf-8")
        print(f"      trazidas para a origem ({len(so_no_destino)}). Copia: {copia.name}")
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
