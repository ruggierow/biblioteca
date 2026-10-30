#!/usr/bin/env python3
"""Portao do guarda do espelho: contar as edicoes, nao so reconhece-las.

O `conferir_destino.py` e a unica coisa entre o `espelhar.sh` e a perda do que
o usuario cadastrou no celular. Ele nao tinha teste nenhum, e por isso um
defeito de duas semanas so apareceu quando um livro de verdade caiu nele.

O CASO QUE DA NOME AO PORTAO (30/10/2026, o Judas de Amos Oz)

O projeto permite o MESMO titulo e autor duas vezes: a edicao impressa e a do
Kindle, que diferem no local. A classificacao usava um CONJUNTO de identidades,
entao as duas colapsavam numa so. Resultado, com o impresso na origem e
impresso + Kindle no destino:

    "1 livro esta DIFERENTE dos dois lados (nenhum sumiria)"   <- as duas falsas
    e o --trazer RECUSAVA, alegando que criaria o livro duas vezes

Duas vezes era o certo. E a mensagem empurrava para o `--forcar`, que apagaria
o livro novo em silencio.

Roda sobre arquivos temporarios. NUNCA toca na base.
"""
import subprocess, sys, tempfile
from pathlib import Path

AQUI = Path(__file__).resolve().parent
GUARDA = AQUI / "conferir_destino.py"
falhas = []

AUSENTE  = "existem SO no destino"
ALTERADO = "estao DIFERENTES dos dois lados"

# campos: titulo, autores, temas, ano, emprestado, comentarios, local, grupos, pais
def livro(titulo, autores="Oz, Amós", local="Estante", ano="2014", temas=""):
    return f"{titulo}\t{autores}\t{temas}\t{ano}\t\t\t{local}\t\tIL"


def roda(origem, destino, trazer=False):
    with tempfile.TemporaryDirectory() as tmp:
        o, d = Path(tmp) / "origem.txt", Path(tmp) / "destino.txt"
        o.write_text("\n".join(origem) + "\n", encoding="utf-8")
        d.write_text("\n".join(destino) + "\n", encoding="utf-8")
        cmd = [sys.executable, "-I", str(GUARDA), str(o), str(d)]
        if trazer:
            cmd.append("--trazer")
        r = subprocess.run(cmd, capture_output=True, text=True)
        depois = [l for l in o.read_text(encoding="utf-8").splitlines() if l.strip()]
        copias = [p.name for p in Path(tmp).glob("*antes-de-trazer-do-destino*")]
        return r.returncode, r.stdout, depois, copias


def caso(titulo, origem, destino, *, saida, contem=(), ausente_de=(), origem_fica=None,
         trazer=False, copia=None):
    cod, texto, depois, copias = roda(origem, destino, trazer)
    erros = []
    if cod != saida:
        erros.append(f"saida {cod}, esperava {saida}")
    for t in contem:
        if t not in texto:
            erros.append(f"nao disse {t!r}")
    for t in ausente_de:
        if t in texto:
            erros.append(f"disse {t!r} e nao devia")
    if origem_fica is not None and len(depois) != origem_fica:
        erros.append(f"origem com {len(depois)} linha(s), esperava {origem_fica}")
    if copia is not None and bool(copias) != copia:
        erros.append("copia de seguranca " + ("nao foi gravada" if copia else "foi gravada a toa"))
    if erros:
        falhas.append(f"{titulo}: " + "; ".join(erros))
    else:
        print(f"   ok   {titulo}")


print("Portao do guarda do espelho")

impresso = livro("Judas", local="Estante")
kindle   = livro("Judas", local="Kindle")
outro    = livro("A Caixa Preta", local="Estante")

caso("destino identico: pode copiar",
     [impresso, outro], [impresso, outro], saida=0, origem_fica=2)

caso("livro so no destino e AUSENTE",
     [impresso], [impresso, outro],
     saida=1, contem=[AUSENTE], ausente_de=[ALTERADO])

caso("livro so no destino e TRAZIDO",
     [impresso], [impresso, outro],
     trazer=True, saida=0, origem_fica=2, copia=True)

caso("livro editado e ALTERADO, e NAO e trazido",
     [impresso], [livro("Judas", local="Caixa 3")],
     trazer=True, saida=1, contem=[ALTERADO], ausente_de=[AUSENTE], origem_fica=1)

# O caso do Judas. Antes de 30/10/2026 este dizia ALTERADO e nao trazia nada.
caso("edicao Kindle de livro que a origem ja tem impresso e AUSENTE",
     [impresso], [impresso, kindle],
     saida=1, contem=[AUSENTE], ausente_de=[ALTERADO])

caso("e ela e TRAZIDA, ficando o titulo duas vezes",
     [impresso], [impresso, kindle],
     trazer=True, saida=0, origem_fica=2, copia=True)

caso("as duas edicoes ja nos dois lados: silencio",
     [impresso, kindle], [impresso, kindle], saida=0, origem_fica=2)

caso("uma edicao E um livro novo: um de cada, classificados certo",
     [impresso, kindle],
     [impresso, livro("Judas", local="Caixa 3"), outro],
     saida=1, contem=[AUSENTE, ALTERADO])

# Sem --trazer o guarda NUNCA escreve: so informa.
caso("sem --trazer a origem fica intacta",
     [impresso], [impresso, outro], saida=1, origem_fica=1, copia=False)

# E a regra de forma: o portao nao pode apontar para a base de verdade.
#
# O alvo e montado em PEDACOS de proposito. Escrito inteiro, ele casaria com
# esta propria linha e o portao reprovaria a si mesmo — foi o que aconteceu na
# primeira versao, e e o mesmo tropeco que o conferir-vigia.py ja tinha dado:
# um padrao que procura por si mesmo nao mede nada.
proibidos = ["Mobile " + "Documents", "biblioteca" + ".txt"]
fonte = Path(__file__).read_text(encoding="utf-8")
if any(x in fonte for x in proibidos):
    falhas.append("este portao alcanca a base de verdade; ele roda em temporarios")
else:
    print("   ok   o portao roda em arquivos temporarios, nunca na base")

if falhas:
    print("\nFALHOU:")
    for f in falhas:
        print(f"   {f}")
    sys.exit(1)
print("\nPortao do espelho: tudo verde.")
