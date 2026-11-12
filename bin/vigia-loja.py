#!/usr/bin/env python3
"""Vigia as DUAS lojas: avisa quando o estado da versao em analise MUDA.

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

Se a Play nao responder, a passada inteira sai como `20` — inclusive a parte
da Apple. Nenhuma noticia se perde nisso: a referencia so e gravada quando a
leitura deu certo, entao a mudanca da Apple e relatada na passada seguinte.

O codigo de saida distingue os tres desfechos, e e por ele que a tarefa
decide se fala. Silencio so vale para "conferi e esta igual" — ver a licao
`portao-que-nao-olha-passa-verde` do projeto.

    0   conferi, nada mudou          -> a tarefa fica calada
    10  MUDOU                        -> a tarefa relata a saida
    20  NAO consegui olhar           -> a tarefa relata o erro

O QUE ELE VIGIA

  1. o estado de cada versao iOS na loja (WAITING_FOR_REVIEW, IN_REVIEW,
     READY_FOR_SALE, os rejeitados, e qualquer outro que a Apple invente);
  2. Portugal, que e o unico territorio da UE entre os 6 escolhidos;
  3. as duas faixas FECHADAS da Play, desde 12/11/2026.

E A PLAY NAO SE VIGIA POR MUDANCA

Comparar com ontem resolve a Apple, que muda de estado sozinha. Na Play nao:
em 08/11/2026 a 1.9.20 nao foi publicada, e nos quatro dias seguintes **nada
mudou** la — o codigo 30 (1.9.19) continuou liberado, igualzinho. Um vigia de
mudanca teria ficado calado com razao, todo dia, enquanto o Android ficava
atras. "Nada mudou" nao e "esta certo".

Por isso a Play tem uma pergunta a mais, que nao olha para ontem: **o codigo
que este repositorio diz ser o atual (o `version:` do pubspec.yaml) esta
liberado nas duas faixas fechadas?** Se nao esta, e ATRASO, e atraso e noticia
mesmo quando nada mudou.

Para nao repetir o aviso a cada duas horas, o atraso e relatado **uma vez por
dia** (a data do ultimo aviso fica na referencia). Uma vez por dia e o
intervalo que pega o caso da 1.9.20 na manha seguinte, em vez de por acaso
quatro dias depois.

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
from datetime import date
from pathlib import Path

AQUI = Path(__file__).resolve().parent
APP = "6799312712"
ESTADO = Path.home() / "Library/Application Support/Biblioteca/vigia-loja.json"

SEM_NOVIDADE, COM_NOVIDADE, NAO_OLHEI = 0, 10, 20


def modulo(nome):
    """Um programa vizinho carregado como modulo, pelo CAMINHO.

    Importar pelo caminho, e nao por `sys.path`, para o script funcionar
    chamado de qualquer diretorio — a tarefa agendada nao roda na raiz do
    projeto.
    """
    spec = importlib.util.spec_from_file_location(
        nome.replace("-", "_"), AQUI / f"{nome}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def api():
    """O modulo appstore.py do lado, carregado pelo caminho.

    Importar pelo caminho, e nao por `sys.path`, para o script funcionar
    chamado de qualquer diretorio — a tarefa agendada nao roda na raiz do
    projeto.
    """
    return modulo("appstore")


def olhar_a_play():
    """{faixa fechada: codigo liberado}, mais o que o repositorio espera.

    Tudo vem do `publicar-play.py`: as faixas, a leitura e o numero esperado.
    Repetir aqui a lista de faixas ou o roteiro do edit criaria duas verdades
    sobre a mesma coisa — e a que o vigia usasse seria a que ninguem corrige.
    """
    play = modulo("publicar-play")
    edit = play.abrir_edit()
    try:
        atual = play.faixas_de(edit)
    finally:
        play.descartar(edit)

    faixas = {}
    for faixa in play.FAIXAS:
        liberados = [c for c, estado, _ in atual.get(faixa, [])
                     if estado == "completed"]
        faixas[faixa] = max(liberados) if liberados else None

    _, esperado = play.pubspec()
    return {"faixas": faixas, "esperado": esperado, "versao": play.versao()}


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
            "portugal": {"contentStatus": status, "lookup": lookup("pt")},
            "play": olhar_a_play()}


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

    fa = (antes.get("play") or {}).get("faixas", {})
    fb = agora["play"]["faixas"]
    for faixa, codigo in fb.items():
        velho = fa.get(faixa)
        if velho != codigo:
            mudou.append(f"Play, faixa {faixa!r}: "
                         f"{velho if velho is not None else 'nada'} -> "
                         f"{codigo if codigo is not None else 'nada'}")

    return mudou


def atraso(agora):
    """O Android esta atras do que o repositorio diz ser a versao atual?

    Esta pergunta NAO olha para ontem, de proposito. Ver o cabecalho: na Play
    o defeito e a imobilidade, nao a mudanca.
    """
    play = agora["play"]
    esperado, v = play["esperado"], play["versao"]
    atrasadas = []
    for faixa, codigo in play["faixas"].items():
        if codigo != esperado:
            atrasadas.append(f"Play, faixa {faixa!r}: esta liberado o codigo "
                             f"{codigo if codigo is not None else 'nada'}, e a "
                             f"{v} deste repositorio e o codigo {esperado}")
    return atrasadas


def imprimir(agora):
    print("  versoes iOS:")
    for versao, estado in agora["versoes"].items():
        print(f"     {versao:8s} {estado}")
    p = agora["portugal"]
    print(f"  Portugal: contentStatus={p['contentStatus']}  lookup={p['lookup']}")
    play = agora.get("play")
    if play:
        print(f"  Play (o repositorio esta na {play['versao']}, "
              f"codigo {play['esperado']}):")
        for faixa, codigo in play["faixas"].items():
            marca = "em dia" if codigo == play["esperado"] else "ATRASADA"
            print(f"     {faixa:32s} codigo {codigo or '—':<6} {marca}")


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

    hoje = date.today().isoformat()
    antes = ler_referencia()
    atrasadas = atraso(agora)

    def guardar(avisei):
        """A referencia, com o atraso e a data em que ele foi dito.

        Grava SEMPRE, inclusive quando nada mudou. A versao anterior so
        gravava na mudanca, e com isso uma referencia velha (sem a Play, por
        exemplo) ficava velha para sempre: a primeira mudanca de verdade
        passaria por "chave que faltava" e nao seria relatada.
        """
        gravar_referencia({**agora, "atraso": atrasadas,
                           "atraso_avisado_em":
                               hoje if avisei
                               else (antes or {}).get("atraso_avisado_em")})

    if antes is None:
        # Primeira passada: nao ha com que comparar. Mas o ATRASO nao depende
        # de comparacao, e dize-lo ja aqui e o que impede a referencia de
        # nascer com o defeito dentro e nunca o contar.
        guardar(bool(atrasadas))
        print("Primeira passada: nao havia referencia, gravei a de agora.")
        if atrasadas:
            print("ATRASO:")
            for linha in atrasadas:
                print(f"  - {linha}")
        imprimir(agora)
        return COM_NOVIDADE if atrasadas else SEM_NOVIDADE

    # Referencia gravada antes de 12/11/2026 nao tem a Play. Completa-la com a
    # de agora evita anunciar "a faixa passou de nada para 32", que nao
    # aconteceu — e nao abre ponto cego, porque o atraso nao se mede por
    # comparacao.
    if "play" not in antes:
        antes["play"] = agora["play"]

    mudou = diferencas(antes, agora)
    novo_atraso = bool(atrasadas) and (atrasadas != antes.get("atraso")
                                       or antes.get("atraso_avisado_em") != hoje)
    guardar(novo_atraso)

    if not mudou and not novo_atraso:
        return SEM_NOVIDADE

    if mudou:
        print("MUDOU:")
        for linha in mudou:
            print(f"  - {linha}")
    if novo_atraso:
        print("ATRASO (nao e mudanca — e o Android parado atras do "
              "repositorio):")
        for linha in atrasadas:
            print(f"  - {linha}")
    print()
    imprimir(agora)
    return COM_NOVIDADE


if __name__ == "__main__":
    sys.exit(main())
