#!/usr/bin/env python3
"""Portao do vigia das lojas, na parte da Play: silencio tem de ser conclusao.

A Apple muda de estado sozinha, entao compara-la com ontem basta. **A Play
nao.** Em 08/11/2026 a 1.9.20 nao chegou a ser enviada, e nos quatro dias
seguintes nada mudou lá: o codigo 30 (1.9.19) continuou liberado, igualzinho.
Um vigia de mudanca teria ficado calado — com razao e inutilmente.

Por isso o vigia ganhou uma pergunta que NAO olha para ontem: o codigo que o
`pubspec.yaml` diz ser o atual esta liberado nas duas faixas fechadas? Este
portao exercita exatamente essa pergunta, nos casos em que ela e facil de
estragar:

    a linha do Mac some da ficha   -> 10, e DIZ se o controle tambem sumiu
    atraso aparece                 -> 10 (fala)
    o MESMO atraso, no mesmo dia   ->  0 (cala: a tarefa roda a cada 2 horas)
    o MESMO atraso, no dia seguinte-> 10 (volta a falar)
    o atraso MUDOU no mesmo dia    -> 10 (nao espera o dia virar)
    atraso na PRIMEIRA passada     -> 10 (nao nasce com o defeito dentro)
    referencia velha, sem a Play   ->  0, e a referencia e COMPLETADA
    nao consegui olhar             -> 20, nunca 0

Roda sem rede, sem credencial e sem tocar na referencia de verdade: a leitura
da loja e um dublê, o relogio e de mentira e o arquivo de estado fica no /tmp.
"""
import importlib.util
import io
import json
import sys
import tempfile
from contextlib import redirect_stdout
from pathlib import Path

AQUI = Path(__file__).resolve().parent
falhas = []


def carrega():
    spec = importlib.util.spec_from_file_location("vigia_loja",
                                                  AQUI / "vigia-loja.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class RelogioFalso:
    """`date.today().isoformat()` devolvendo o dia que o caso pede."""

    def __init__(self, dia):
        self.dia = dia

    def today(self):
        return self

    def isoformat(self):
        return self.dia


def estado(faixas, esperado=32, versao="1.9.21", ios="READY_FOR_SALE",
           noMac=False, controle=True):
    return {"versoes": {"1.9.21": ios},
            "portugal": {"contentStatus": "OK", "lookup": 1},
            "play": {"faixas": faixas, "esperado": esperado, "versao": versao},
            "mac": {"noMac": noMac, "controleNoMac": controle,
                    "versaoNaLoja": "1.9.20"}}


EM_DIA = {"alpha": 32, "Teste inical do Biblioteca": 32}
ATRASADA = {"alpha": 30, "Teste inical do Biblioteca": 30}


def rodar(olhado, referencia=None, dia="2026-11-12"):
    """Uma passada do vigia. Devolve (codigo de saida, o que ele imprimiu)."""
    mod = carrega()
    with tempfile.TemporaryDirectory() as pasta:
        mod.ESTADO = Path(pasta) / "vigia-loja.json"
        if referencia is not None:
            mod.ESTADO.write_text(json.dumps(referencia))
        mod.date = RelogioFalso(dia)
        mod.olhar = ((lambda: (_ for _ in ()).throw(olhado))
                     if isinstance(olhado, Exception) else (lambda: olhado))
        argv = sys.argv
        sys.argv = ["vigia-loja.py"]
        tela = io.StringIO()
        try:
            with redirect_stdout(tela):
                codigo = mod.main()
        finally:
            sys.argv = argv
        guardado = (json.loads(mod.ESTADO.read_text())
                    if mod.ESTADO.exists() else None)
    return codigo, tela.getvalue(), guardado


def caso(titulo, codigo_esperado, dizendo=(), calando=(), **kw):
    codigo, tela, guardado = rodar(**kw)
    problemas = []
    if codigo != codigo_esperado:
        problemas.append(f"saiu {codigo}, esperado {codigo_esperado}")
    for pedaco in dizendo:
        if pedaco not in tela:
            problemas.append(f"nao disse {pedaco!r}")
    for pedaco in calando:
        if pedaco in tela:
            problemas.append(f"disse {pedaco!r}, e devia calar")
    if problemas:
        falhas.append(titulo)
        print(f"   FALHOU: {titulo} — {'; '.join(problemas)}")
        if tela.strip():
            print("      disse: " + tela.strip().replace("\n", " | ")[:200])
    else:
        print(f"   ok: {titulo}")
    return guardado


def main():
    print("--- a Play no vigia das lojas ---")

    caso("em dia e nada mudou: cala", 0,
         olhado=estado(EM_DIA), referencia=estado(EM_DIA))

    caso("atraso na PRIMEIRA passada: fala, nao nasce com o defeito dentro",
         10, dizendo=("ATRASO", "codigo 30", "codigo 32"),
         olhado=estado(ATRASADA), referencia=None)

    # O caso da 1.9.20: a referencia JA sabe do atraso e nada mudou desde
    # ontem. Um vigia de mudanca calaria; este fala uma vez por dia.
    ontem = {**estado(ATRASADA),
             "atraso": ["Play, faixa 'alpha': esta liberado o codigo 30, e a "
                        "1.9.21 deste repositorio e o codigo 32",
                        "Play, faixa 'Teste inical do Biblioteca': esta "
                        "liberado o codigo 30, e a 1.9.21 deste repositorio "
                        "e o codigo 32"],
             "atraso_avisado_em": "2026-11-11"}
    caso("o MESMO atraso, no dia seguinte: volta a falar",
         10, dizendo=("ATRASO",),
         olhado=estado(ATRASADA), referencia=ontem, dia="2026-11-12")

    hoje = {**ontem, "atraso_avisado_em": "2026-11-12"}
    caso("o MESMO atraso, no MESMO dia: cala (a tarefa roda a cada 2 horas)",
         0, olhado=estado(ATRASADA), referencia=hoje, dia="2026-11-12")

    caso("o atraso MUDOU no mesmo dia: fala sem esperar o dia virar",
         10, dizendo=("codigo 31",),
         olhado=estado({"alpha": 31, "Teste inical do Biblioteca": 31}),
         referencia=hoje, dia="2026-11-12")

    caso("a faixa andou para a versao certa: fala, e nao e atraso",
         10, dizendo=("Play, faixa",), calando=("ATRASO",),
         olhado=estado(EM_DIA), referencia=estado(ATRASADA))

    # O ponto cego que a gravacao condicional criava: referencia velha sem a
    # chave `play`. Ela nao pode gerar aviso falso AGORA, e tem de ficar
    # completa — senao a proxima mudanca de verdade passa por "chave que
    # faltava" e nao e relatada.
    velha = {"versoes": {"1.9.21": "READY_FOR_SALE"},
             "portugal": {"contentStatus": "OK", "lookup": 1}}   # sem `play` nem `mac`
    guardado = caso("referencia velha, sem a Play nem a ficha: nao inventa mudanca",
                    0, calando=("Play", "ATRASO", "App Store"),
                    olhado=estado(EM_DIA), referencia=velha)
    if guardado is None or "play" not in (guardado or {}) or "mac" not in guardado:
        falhas.append("a referencia nao foi completada")
        print("   FALHOU: a referencia velha nao ganhou as chaves `play`/`mac` — "
              "a proxima mudanca de verdade passaria em silencio")
    else:
        print("   ok: a referencia velha ganhou as chaves `play` e `mac`")
        caso("e a mudanca SEGUINTE ja e relatada (ponto cego fechado)",
             10, dizendo=("Play, faixa",),
             olhado=estado({"alpha": 33, "Teste inical do Biblioteca": 33},
                           esperado=33),
             referencia=guardado)

    # --- a ficha do Mac, com o controle do lado -------------------------
    caso("a linha do Mac sumiu da nossa ficha e o controle continua: propagou",
         10, dizendo=("NAO e mais oferecido para Mac", "propagou"),
         olhado=estado(EM_DIA, noMac=False, controle=True),
         referencia=estado(EM_DIA, noMac=True, controle=True))

    caso("sumiu das DUAS fichas: desconfia do medidor, nao comemora",
         10, dizendo=("parece mudanca no texto", "Confira"),
         calando=("propagou",),
         olhado=estado(EM_DIA, noMac=False, controle=False),
         referencia=estado(EM_DIA, noMac=True, controle=True))

    caso("voltou a ser oferecido para Mac: fala",
         10, dizendo=("voltou a ser oferecido",),
         olhado=estado(EM_DIA, noMac=True, controle=True),
         referencia=estado(EM_DIA, noMac=False, controle=True))

    caso("continua oferecido, como ontem: cala",
         0, olhado=estado(EM_DIA, noMac=True, controle=True),
         referencia=estado(EM_DIA, noMac=True, controle=True))

    caso("nao consegui olhar: 20, nunca 0",
         20, dizendo=("NAO CONSEGUI OLHAR",),
         olhado=RuntimeError("rede caiu"), referencia=estado(EM_DIA))

    print()
    if falhas:
        print(f"REPROVADO: {len(falhas)} caso(s).")
        return 1
    print("O vigia olha a Play, e silencio ali e conclusao.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
