#!/usr/bin/env python3
"""Aponta titulos com erro de digitacao provavel.

SO LE. Nunca altera a base — imprime o relatorio e, com --json, grava a lista
para voce revisar. A correcao e sempre decisao do usuario: ha titulo que PARECE
errado e esta certo.

    ./bin/achar-erros-de-titulo.py              # so os livros sem capa
    ./bin/achar-erros-de-titulo.py --todos      # o catalogo inteiro
    ./bin/achar-erros-de-titulo.py --json saida.json

POR QUE ISSO IMPORTA PARA AS CAPAS: erro de digitacao e capa que falta
disfarcada. Em 09/10/2026, corrigir 26 titulos fez 12 livros acharem capa na
busca seguinte — e um deles ("Suissurro" -> "Sussurro") HERDOU a capa de outra
linha sozinho, porque o fotoId passou a ser o mesmo.

COMO DECIDE: cruza duas evidencias independentes, porque cada uma sozinha erra.

 (a) o corretor do macOS (NSSpellChecker) nao conhece a palavra NEM em pt_BR
     NEM em en_US — a biblioteca e bilingue, e exigir as duas evita acusar
     "Synthesis" de erro. (O hunspell do Homebrew esta instalado SEM dicionario;
     nao serve.)
 (b) a palavra aparece pouco no catalogo e esta a UMA edicao de distancia de
     outra que aparece muito: "Computadres" (1x) x "Computadores" (13x). Essa
     evidencia nao depende de dicionario nenhum.

O falso positivo dominante de (a) e NOME PROPRIO: Verilog, Nexys, Gradiva,
Doisneau, Klintowitz. Por isso o relatorio separa os dois grupos em vez de
misturar, e quem tem as duas evidencias vem primeiro.
"""
import argparse, json, re, sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import biblioteca_comum as bc

PALAVRA = re.compile(r"[A-Za-zÀ-ÿ][A-Za-zÀ-ÿ'-]{2,}")


def distancia1(a, b):
    """True se uma edicao (troca, insercao ou remocao de 1 letra) leva a em b."""
    if a == b or abs(len(a) - len(b)) > 1: return False
    if len(a) == len(b):
        return sum(x != y for x, y in zip(a, b)) == 1
    curto, longo = (a, b) if len(a) < len(b) else (b, a)
    return any(longo[:i] + longo[i+1:] == curto for i in range(len(longo)))


def main():
    p = argparse.ArgumentParser(description="Aponta titulos com erro de digitacao provavel.")
    p.add_argument("--todos", action="store_true", help="varre o catalogo todo, nao so os sem capa")
    p.add_argument("--json", help="grava os suspeitos fortes neste arquivo")
    a = p.parse_args()

    try:
        import Cocoa
    except ImportError:
        sys.exit("Falta o PyObjC (modulo Cocoa) — e ele que da acesso ao corretor do macOS.")

    livros = bc.ler_base()
    alvo = livros if a.todos else [l for l in livros if l.id not in bc.ler_fotos()]
    print(f"catalogo: {len(livros)} livros   a examinar: {len(alvo)}"
          f" ({'todos' if a.todos else 'os sem capa'})")

    vocab = Counter(w.lower() for l in livros for w in PALAVRA.findall(l.titulo))
    corretor = Cocoa.NSSpellChecker.sharedSpellChecker()
    etiqueta = Cocoa.NSSpellChecker.uniqueSpellDocumentTag()
    visto = {}

    def erra(palavra, idioma):
        if (palavra, idioma) not in visto:
            r = corretor.checkSpellingOfString_startingAt_language_wrap_inSpellDocumentWithTag_wordCount_(
                palavra, 0, idioma, False, etiqueta, None)
            visto[(palavra, idioma)] = r[0].length > 0
        return visto[(palavra, idioma)]

    def sugestoes(palavra):
        for idioma in ("pt_BR", "en_US"):
            g = corretor.guessesForWordRange_inString_language_inSpellDocumentWithTag_(
                Cocoa.NSMakeRange(0, len(palavra)), palavra, idioma, etiqueta)
            if g: return [str(x) for x in g][:3]
        return []

    fortes, so_corretor = [], []
    for l in alvo:
        for w in PALAVRA.findall(l.titulo):
            b = w.lower()
            if len(b) < 4 or not (erra(w, "pt_BR") and erra(w, "en_US")): continue
            vizinhos = [(v, n) for v, n in vocab.items()
                        if n >= 3 and n > vocab[b] * 2 and distancia1(b, v)]
            reg = {"linha": l.n, "titulo": l.titulo, "palavra": w,
                   "sugestoes": sugestoes(w), "parecidas_no_catalogo": vizinhos}
            (fortes if vizinhos else so_corretor).append(reg)

    print(f"\n=== AS DUAS EVIDENCIAS — erro muito provavel ({len(fortes)}) ===")
    for r in fortes:
        print(f"   linha {r['linha']:4d}  {r['titulo'][:60]}")
        print(f"      '{r['palavra']}' -> no catalogo ha "
              f"{', '.join(f'{v} ({n}x)' for v, n in r['parecidas_no_catalogo'])}"
              f"   corretor sugere: {', '.join(r['sugestoes']) or '—'}")

    print(f"\n=== so o corretor estranhou ({len(so_corretor)}) — espere MUITO nome proprio ===")
    ja = set()
    for r in so_corretor:
        if r["palavra"].lower() in ja or not r["sugestoes"]: continue
        ja.add(r["palavra"].lower())
        print(f"   linha {r['linha']:4d}  {r['palavra']:20s} em {r['titulo'][:40]:42s}"
              f" sugere: {', '.join(r['sugestoes'][:2])}")

    if a.json:
        Path(a.json).write_text(json.dumps(fortes + so_corretor, ensure_ascii=False, indent=1),
                                encoding="utf-8")
        print(f"\ngravado em {a.json}")
    print("\nNada foi alterado na base. Corrigir titulo muda o fotoId: se o livro JA TEM capa,"
          "\nela se desgruda. Conserte o titulo ANTES de buscar capa, nunca depois.")


if __name__ == "__main__":
    main()
