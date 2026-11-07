#!/usr/bin/env python3
"""Portao da pagina do app (docs/index.html).

    ./bin/conferir-pagina.py           so o que da para conferir sem rede
    ./bin/conferir-pagina.py --rede    acrescenta os enderecos de download

REPROVA, e o motivo de existir:

  1. a pagina nao bate com o que o gerador produz HOJE. Isto pega as DUAS
     formas de ela envelhecer: ficou para tras de uma versao nova, ou alguem
     editou o HTML a mao e a proxima release vai jogar a edicao fora;
  2. um arquivo que a pagina oferece nao existe (manual, folha de estilo,
     politica de privacidade) — link quebrado na cara do usuario;
  3. com --rede, um dos enderecos de nome fixo da release nao responde 200.

A pagina ficou dezoito versoes atrasada entre setembro e novembro de 2026 sem
ninguem notar, porque ninguem estava olhando. Este arquivo e quem olha.
"""
import re
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PAGINA = RAIZ / "docs" / "index.html"

falhas = []
oks = []


def reprova(m):
    falhas.append(m)
    print(f"   FALHOU: {m}")


def passa(m):
    oks.append(m)
    print(f"   ok: {m}")


def confere_gerada():
    if not PAGINA.exists():
        reprova("docs/index.html nao existe — rode ./bin/gerar-pagina.py")
        return None
    atual = PAGINA.read_text()
    bruto = subprocess.run([sys.executable, str(RAIZ / "bin" / "gerar-pagina.py"),
                            "--mostrar"], capture_output=True, text=True)
    if bruto.returncode != 0:
        reprova(f"o gerador nao rodou: {bruto.stderr.strip()[:200]}")
        return atual
    if bruto.stdout != atual:
        v = (RAIZ / "VERSION").read_text().strip()
        reprova(f"a pagina NAO e a que o gerador produz para a {v}. "
                "Rode ./bin/gerar-pagina.py (e nao edite o index.html a mao)")
    else:
        passa("a pagina e exatamente o que o gerador produz")
    return atual


def confere_arquivos(html):
    """Todo link relativo tem de existir em docs/."""
    alvos = set(re.findall(r'(?:href|src)="(?!https?:|#|mailto:)([^"]+)"', html))
    for alvo in sorted(alvos):
        if (RAIZ / "docs" / alvo).exists():
            passa(f"existe: docs/{alvo}")
        else:
            reprova(f"a pagina oferece docs/{alvo}, que NAO existe")


def confere_versao(html):
    v = (RAIZ / "VERSION").read_text().strip()
    if f"Versão {v}" in html:
        passa(f"a pagina anuncia a {v}")
    else:
        achado = re.search(r"Versão ([0-9][0-9.]*)", html)
        reprova(f"a pagina anuncia {achado.group(1) if achado else '???'}, "
                f"e o VERSION diz {v}")


def confere_rede(html):
    for url in sorted(set(re.findall(
            r'href="(https://github\.com/[^"]+/releases/latest/download/[^"]+)"', html))):
        nome = url.rsplit("/", 1)[-1]
        try:
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=40) as r:
                codigo = r.status
        except urllib.error.HTTPError as e:
            codigo = e.code
        except Exception as e:
            reprova(f"{nome}: {type(e).__name__}")
            continue
        if codigo == 200:
            passa(f"{nome} responde 200")
        else:
            reprova(f"{nome} responde {codigo}")


def main():
    print("--- a pagina do app ---")
    html = confere_gerada()
    if html:
        confere_versao(html)
        confere_arquivos(html)
        if "--rede" in sys.argv[1:]:
            confere_rede(html)

    print()
    if falhas:
        print(f"REPROVADO: {len(falhas)} problema(s) na pagina.")
        sys.exit(1)
    print(f"A pagina esta em dia ({len(oks)} conferencias).")


if __name__ == "__main__":
    main()
