#!/usr/bin/env python3
"""Vigia a App Store: avisa quando o estado da versao em analise MUDA.

So LE. Nunca submete, nunca publica, nunca carimba versao.

    ./bin/vigia-loja.py            compara com a ultima vez e diz o que mudou
    ./bin/vigia-loja.py --estado   mostra o que esta na loja agora, sem comparar
    ./bin/vigia-loja.py --semear   grava o estado de agora como referencia

POR QUE ELE EXISTE (medido em 08/11/2026, e e o ponto todo)

A tarefa agendada que fazia isto rodou **35 vezes sem olhar nada**. Ela pedia
DOIS comandos ao agente — o `appstore.py` e um `curl ... | python3 -c ...` —
e so o primeiro estava na lista de permissoes. Sem ninguem para aprovar o
segundo, a sessao abortava inteira, e mesmo assim o painel marcava
"succeeded". Trinta e cinco vezes.

Juntar tudo aqui troca duas permissoes por UMA, e tira o julgamento da prosa
da tarefa (que o agente tem de seguir) para dentro de um programa (que da
para rodar e conferir).

O PORTAO: NAO OLHEI != NAO MUDOU

O codigo de saida distingue os tres desfechos, e e por ele que a tarefa
decide se fala. Silencio so vale para "conferi e esta igual" — ver a licao
`portao-que-nao-olha-passa-verde` do projeto.

    0   conferi, nada mudou          -> a tarefa fica calada
    10  MUDOU                        -> a tarefa relata a saida
    20  NAO consegui olhar           -> a tarefa relata o erro

O QUE ELE VIGIA

  1. o estado de cada versao iOS na loja (WAITING_FOR_REVIEW, IN_REVIEW,
     READY_FOR_SALE, os rejeitados, e qualquer outro que a Apple invente);
  2. Portugal, que e o unico territorio da UE entre os 6 escolhidos.

ARMADILHA DE PORTUGAL, ja caida uma vez

O `appAvailabilityV2` devolve `TRADER_STATUS_NOT_PROVIDED` tanto para "nao
declarou" quanto para "declarou e a Apple ainda nao verificou". Em 04/11 ele
declarou; a tela de Business mostra `In Review`. A API nao distingue os dois
casos — entao este programa NUNCA sugere declarar de novo. Ele so informa.
"""
import argparse
import base64
import importlib.util
import json
import sys
import urllib.request
from pathlib import Path

AQUI = Path(__file__).resolve().parent
APP = "6799312712"
ESTADO = Path.home() / "Library/Application Support/Biblioteca/vigia-loja.json"

SEM_NOVIDADE, COM_NOVIDADE, NAO_OLHEI = 0, 10, 20


def api():
    """O modulo appstore.py do lado, carregado pelo caminho.

    Importar pelo caminho, e nao por `sys.path`, para o script funcionar
    chamado de qualquer diretorio — a tarefa agendada nao roda na raiz do
    projeto.
    """
    spec = importlib.util.spec_from_file_location("appstore", AQUI / "appstore.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def territorio_de(disponibilidade):
    """O codigo ISO ("PRT") de um item de territoryAvailabilities.

    A Apple nao devolve "PRT" num campo: o `id` do item e o base64 de
    `{"s":"<app>","t":"PRT"}`, e a relacao `territory` so traz o codigo se a
    chamada pedir `include=...territory`. Decodificar o id e o caminho curto
    e nao depende de um include a mais.
    """
    t = (disponibilidade.get("relationships", {})
         .get("territory", {}).get("data") or {})
    if t.get("id"):
        return t["id"]
    try:
        ident = disponibilidade["id"]
        falta = "=" * (-len(ident) % 4)          # base64 sem o enchimento
        return json.loads(base64.b64decode(ident + falta))["t"]
    except Exception:
        return None


def lookup(pais):
    """Quantos registros a loja publica daquele pais devolve (0 ou 1).

    E a prova de que o app esta mesmo NA LOJA daquele territorio — a API de
    gestao pode dizer "disponivel" antes de a loja servir.
    """
    url = (f"https://itunes.apple.com/lookup?id={APP}&country={pais}")
    with urllib.request.urlopen(url, timeout=30) as r:
        return int(json.load(r)["resultCount"])


def olhar():
    """O estado de agora. Levanta excecao se nao der para olhar."""
    A = api()

    versoes = {}
    for v in A.pegar(f"/apps/{APP}/appStoreVersions?limit=10")["data"]:
        a = v["attributes"]
        versoes[a["versionString"]] = a["appStoreState"]

    # Portugal: o carimbo da API e a loja publica, que sao coisas diferentes.
    disp = A.pegar(f"/apps/{APP}/appAvailabilityV2"
                   f"?include=territoryAvailabilities"
                   f"&limit[territoryAvailabilities]=50")
    status = None
    for x in disp.get("included", []):
        if territorio_de(x) == "PRT":
            status = ",".join(x["attributes"].get("contentStatuses") or [])
            break
    if status is None:
        # Nao achar Portugal e "nao olhei", nao "nada mudou". Devolver None
        # aqui faria o programa comparar None com None para sempre e ficar
        # calado — o defeito que ele existe para evitar.
        raise LookupError("Portugal (PRT) nao veio no appAvailabilityV2")

    return {"versoes": versoes,
            "portugal": {"contentStatus": status, "lookup": lookup("pt")}}


def ler_referencia():
    try:
        return json.loads(ESTADO.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None
    except (json.JSONDecodeError, OSError):
        return None


def gravar_referencia(agora):
    ESTADO.parent.mkdir(parents=True, exist_ok=True)
    ESTADO.write_text(json.dumps(agora, ensure_ascii=False, indent=2),
                      encoding="utf-8")


def diferencas(antes, agora):
    """As mudancas, em portugues. Lista vazia quer dizer: conferi, esta igual."""
    mudou = []

    va, vb = antes["versoes"], agora["versoes"]
    for versao, estado in vb.items():
        if versao not in va:
            mudou.append(f"versao {versao}: apareceu na loja, em {estado}")
        elif va[versao] != estado:
            mudou.append(f"versao {versao}: {va[versao]} -> {estado}")
    for versao in va:
        if versao not in vb:
            mudou.append(f"versao {versao}: sumiu da loja (estava {va[versao]})")

    pa, pb = antes["portugal"], agora["portugal"]
    if pa.get("contentStatus") != pb.get("contentStatus"):
        mudou.append(f"Portugal: {pa.get('contentStatus')} -> {pb.get('contentStatus')}")
    if pa.get("lookup") != pb.get("lookup"):
        onde = "ENTROU na loja portuguesa" if pb["lookup"] else "saiu da loja portuguesa"
        mudou.append(f"Portugal: {onde} (lookup {pa.get('lookup')} -> {pb['lookup']})")

    return mudou


def imprimir(agora):
    print("  versoes iOS:")
    for versao, estado in agora["versoes"].items():
        print(f"     {versao:8s} {estado}")
    p = agora["portugal"]
    print(f"  Portugal: contentStatus={p['contentStatus']}  lookup={p['lookup']}")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--estado", action="store_true",
                   help="mostra o que esta na loja agora, sem comparar")
    p.add_argument("--semear", action="store_true",
                   help="grava o estado de agora como referencia")
    a = p.parse_args()

    try:
        agora = olhar()
    except SystemExit as e:
        # O `appstore.py` chama `sys.exit("A Apple recusou (...)")` em erro de
        # HTTP, e SystemExit NAO e Exception — sem esta clausula o erro
        # atravessaria daqui e sairia com codigo 1, que a tarefa nao sabe ler.
        # Medido em 08/11/2026, com um id de app inexistente.
        print(f"NAO CONSEGUI OLHAR: {e}")
        return NAO_OLHEI
    except Exception as e:                      # rede, credencial, Portugal ausente
        print(f"NAO CONSEGUI OLHAR: {type(e).__name__}: {e}")
        return NAO_OLHEI

    if a.estado:
        imprimir(agora)
        return SEM_NOVIDADE

    if a.semear:
        gravar_referencia(agora)
        print(f"referencia gravada em {ESTADO}")
        imprimir(agora)
        return SEM_NOVIDADE

    antes = ler_referencia()
    if antes is None:
        gravar_referencia(agora)
        print("Primeira passada: nao havia referencia, gravei a de agora.")
        imprimir(agora)
        return SEM_NOVIDADE

    mudou = diferencas(antes, agora)
    if not mudou:
        return SEM_NOVIDADE

    gravar_referencia(agora)
    print("MUDOU:")
    for linha in mudou:
        print(f"  - {linha}")
    print()
    imprimir(agora)
    return COM_NOVIDADE


if __name__ == "__main__":
    sys.exit(main())
