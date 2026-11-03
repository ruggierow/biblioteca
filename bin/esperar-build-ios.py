#!/usr/bin/env python3
"""Espera a build do iPhone APARECER processada em App Store Connect.

    ./bin/esperar-build-ios.py 1.9.18 [--teto-min 20]

Chamado por `bin/enviar-testflight.sh` depois de um envio bem-sucedido.

POR QUE ELE EXISTE (03/11/2026)

O `altool` sabe dizer que o ENVIO deu certo; ele nao sabe dizer que a build
CHEGOU. Entre uma coisa e outra ha de 5 a 15 minutos de processamento na Apple,
e nessa janela a build nao aparece em lugar nenhum da API.

Nesse dia eu olhei a lista uma vez, nao achei a 1.9.18, e conclui que o envio
tinha falhado — ele tinha dado `No errors uploading archive`. Mandei um segundo
envio a toa, que a Apple recusou com 409. **Ausencia na lista nao e falha de
envio: e processamento que ainda nao terminou.**

Entao quem afirma "chegou" tem de ter MEDIDO. E se nao conseguir medir, tem de
dizer isso em voz alta — ver a licao `portao-que-nao-olha-passa-verde`.

CODIGOS DE SAIDA

    0   a build esta VALID — afirmacao medida
    2   o teto estourou, ou a Apple a marcou como INVALID
    3   nao da para conferir (sem a chave de API); o envio em si nao e julgado
"""
import argparse
import importlib.util
import sys
import time
from pathlib import Path

AQUI = Path(__file__).resolve().parent
INTERVALO = 45          # segundos entre consultas; a Apple nao gosta de pressa


def api():
    """Importa bin/appstore.py, que ja sabe montar o JWT da chave de API."""
    spec = importlib.util.spec_from_file_location("appstore", AQUI / "appstore.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def builds_da_versao(pegar, app, versao):
    """As builds daquela versao, ou [] enquanto ela nao existir.

    ATENCAO ao caminho: `pegar()` ja embute o `/v1`. Escrever "/v1/apps/..."
    gera "/v1/v1/apps/...", que a Apple TOLERA em caminho de relacionamento e
    RECUSA na raiz da colecao — um 404 que parece app inexistente.
    """
    d = pegar(f"/apps/{app}/preReleaseVersions?limit=200"
              "&fields[preReleaseVersions]=version")
    alvo = [x for x in d["data"] if x["attributes"]["version"] == versao]
    if not alvo:
        return []
    b = pegar(f"/preReleaseVersions/{alvo[0]['id']}/builds"
              "?fields[builds]=version,processingState,uploadedDate")
    return [x["attributes"] for x in b["data"]]


def esperar(pegar, app, versao, teto_seg, dormir=time.sleep, agora=time.monotonic,
            fala=print):
    """Devolve o codigo de saida. Recebe tudo de fora para poder ser exercida."""
    limite = agora() + teto_seg
    while True:
        try:
            achadas = builds_da_versao(pegar, app, versao)
        except Exception as e:                                    # noqa: BLE001
            # Uma consulta que falha nao condena o envio: pode ser a rede. Mas
            # tambem nao pode passar por "ainda processando" em silencio.
            fala(f"   consulta falhou: {str(e)[:120]}")
            achadas = []

        validas = [b for b in achadas if b["processingState"] == "VALID"]
        if validas:
            fala(f"   chegou: {versao} build {validas[0]['version']}, "
                 f"processamento VALID.")
            return 0
        invalidas = [b for b in achadas if b["processingState"] == "INVALID"]
        if invalidas:
            fala(f"   A Apple REJEITOU a build {versao}: processamento INVALID. "
                 "O motivo chega por e-mail e aparece em App Store Connect.")
            return 2
        if achadas:
            fala(f"   ainda processando ({achadas[0]['processingState']})...")
        else:
            fala("   ainda nao apareceu...")

        if agora() >= limite:
            fala(f"   NAO CONSEGUI CONFIRMAR que a build {versao} chegou, depois "
                 f"de {teto_seg // 60} min. O envio pode ter dado certo e o "
                 "processamento estar lento: confira em App Store Connect > "
                 "TestFlight antes de enviar de novo.")
            return 2
        dormir(INTERVALO)


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("versao", help="a versao enviada, como 1.9.18")
    p.add_argument("--teto-min", type=int, default=20,
                   help="minutos de espera antes de desistir (padrao: 20)")
    a = p.parse_args()

    try:
        mod = api()
        apps = mod.pegar("/apps?limit=20")["data"]
    except SystemExit as e:
        print(f"   nao da para conferir se a build chegou: {str(e.code)[:200]}")
        return 3
    if not apps:
        print("   nao da para conferir: nenhum app nesta conta.")
        return 3

    print(f"Conferindo se a build {a.versao} chegou "
          f"(ate {a.teto_min} min, consultando a cada {INTERVALO}s)...")
    return esperar(mod.pegar, apps[0]["id"], a.versao, a.teto_min * 60)


if __name__ == "__main__":
    sys.exit(main())
