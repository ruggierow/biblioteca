#!/usr/bin/env python3
"""Portao da espera pela build do iPhone: "chegou" tem de ser coisa MEDIDA.

A familia de defeito e a de sempre neste projeto — afirmar sem olhar. Aqui ela
tem duas caras, e as duas custaram caro em 03/11/2026:

  DIZER QUE CHEGOU sem ter visto a build VALID.
  DIZER QUE FALHOU porque a build ainda nao apareceu. Foi esta que me pegou:
  o envio tinha dado certo, a Apple ainda processava, eu li a ausencia como
  falha e mandei um segundo pacote — recusado com 409.

Roda sem rede e sem a Apple: a consulta e um duble, e o relogio e o sono tambem,
para o caso do teto nao levar vinte minutos de verdade.
"""
import importlib.util, sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
falhas = []


def carrega(nome):
    spec = importlib.util.spec_from_file_location(
        nome.replace("-", "_"), AQUI / f"{nome}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


e = carrega("esperar-build-ios")


def duble(roteiro, versao="1.9.18"):
    """Uma consulta de mentira: devolve, a cada chamada, o proximo do roteiro.

    Cada item e a lista de estados de processamento daquela rodada; `None`
    significa "a versao ainda nao existe"; uma string significa estourar.
    """
    estado = {"n": 0}

    def pegar(caminho):
        if "preReleaseVersions" in caminho and "builds" not in caminho:
            i = min(estado["n"], len(roteiro) - 1)
            atual = roteiro[i]
            estado["n"] += 1
            if isinstance(atual, str):
                raise RuntimeError(atual)
            if atual is None:
                return {"data": []}
            return {"data": [{"id": "pre1", "attributes": {"version": versao}}]}
        i = min(estado["n"] - 1, len(roteiro) - 1)
        atual = roteiro[i] or []
        return {"data": [{"id": f"b{k}", "attributes":
                          {"version": "1", "processingState": s,
                           "uploadedDate": "2026-11-03T12:03:10-08:00"}}
                         for k, s in enumerate(atual)]}

    return pegar, estado


def caso(titulo, roteiro, esperado, teto_seg=10 * 60, versao="1.9.18",
         espera_dormidas=None, frase=None):
    pegar, estado = duble(roteiro, versao)
    dormidas, relogio = [], {"t": 0.0}

    def dormir(s):
        dormidas.append(s)
        relogio["t"] += s

    ditos = []
    obtido = e.esperar(pegar, "123", "1.9.18", teto_seg,
                       dormir=dormir, agora=lambda: relogio["t"],
                       fala=ditos.append)
    texto = " | ".join(ditos)
    if obtido != esperado:
        falhas.append(f"{titulo}: esperava codigo {esperado}, veio {obtido} ({texto[:90]})")
    elif espera_dormidas is not None and len(dormidas) != espera_dormidas:
        falhas.append(f"{titulo}: dormiu {len(dormidas)} vez(es), devia dormir "
                      f"{espera_dormidas}")
    elif frase and frase.lower() not in texto.lower():
        falhas.append(f"{titulo}: nao disse {frase!r} — disse {texto[:120]!r}")
    else:
        print(f"   ok   {titulo}")


print("Portao da espera pela build do iPhone")

caso("build ja VALID: confirma na primeira consulta",
     [["VALID"]], 0, espera_dormidas=0, frase="chegou")

caso("processando duas vezes e entao VALID",
     [["PROCESSING"], ["PROCESSING"], ["VALID"]], 0, espera_dormidas=2)

# O caso que da nome ao portao: ausencia NAO e falha de envio.
caso("ausente e depois presente: espera, nao desiste",
     [None, None, ["VALID"]], 0, espera_dormidas=2, frase="ainda nao apareceu")

caso("nunca aparece: sai 2 e DIZ que nao confirmou",
     [None], 2, teto_seg=90, frase="NAO CONSEGUI CONFIRMAR")

caso("INVALID nao fica esperando o teto",
     [["INVALID"]], 2, espera_dormidas=0, frase="REJEITOU")

caso("consulta que estoura nao vira silencio",
     ["rede caiu", ["VALID"]], 0, espera_dormidas=1, frase="consulta falhou")

caso("versao DIFERENTE nao e confundida com a procurada",
     [["VALID"]], 2, teto_seg=90, versao="1.9.1", frase="NAO CONSEGUI CONFIRMAR")

# E o teto tem de ser o que o chamador pediu, nao um embutido.
pegar, _ = duble([None])
dormidas = []
rel = {"t": 0.0}
e.esperar(pegar, "123", "1.9.18", 0,
          dormir=lambda s: (dormidas.append(s), rel.__setitem__("t", rel["t"] + s)),
          agora=lambda: rel["t"], fala=lambda *a: None)
if dormidas:
    falhas.append(f"teto zero ainda dormiu {len(dormidas)} vez(es)")
else:
    print("   ok   teto zero: uma consulta so, sem dormir")

# O chamador tem de pedir os 20 minutos que o usuario escolheu.
sh = (AQUI / "enviar-testflight.sh").read_text(encoding="utf-8")
if "esperar-build-ios.py" not in sh:
    falhas.append("enviar-testflight.sh nao chama a espera")
elif "--teto-min 20" not in sh:
    falhas.append("enviar-testflight.sh nao pede o teto de 20 min")
elif 'exit 2' not in sh:
    falhas.append("enviar-testflight.sh nao propaga a falta de confirmacao")
else:
    print("   ok   enviar-testflight.sh chama a espera, com teto 20 e saida 2")

if falhas:
    print("\nFALHOU:")
    for f in falhas:
        print(f"   {f}")
    sys.exit(1)
print("\nPortao da espera: tudo verde.")
