#!/usr/bin/env python3
"""Compara o que a PAGINA usa com o que cada HOSPEDEIRO implementa.

    ./bin/conferir-ponte.py

Sai 0 se todo recurso que o `biblioteca.html` usa tem quem o atenda no Mac
(WKWebView) e no Windows (Tauri/WebView2). Sai 1 e lista o que falta.

POR QUE ESTE TESTE, E NAO UM TESTE DE NAVEGADOR

Em 12/10/2026 o botao Remover da lista nao fazia nada no Mac. Ele chama
`confirm()`; o WKWebView nao tem dialogo nenhum por conta propria e devolve
FALSE na hora, sem erro e sem pista. Um teste funcional rodando num navegador
teria passado com louvor — no navegador `confirm` funciona. O defeito nao esta
na logica da pagina: esta na FRESTA entre o que a pagina supoe e o que o
hospedeiro oferece.

E a quarta vez que a mesma classe de defeito aparece aqui:

    target="_blank"   nao abria nada no Mac        (sem WKUIDelegate)
    window.print()    nao existe no WKWebView
    window.open       devolve nulo sem WKUIDelegate
    confirm()         devolve false sem WKUIDelegate

Todas silenciosas. Nenhuma seria pega por teste de logica. Este arquivo existe
para que a quinta seja pega na mesa, nao pelo usuario.

COMO FUNCIONA: cada recurso abaixo diz (1) como reconhece-lo na pagina e (2) o
que PRECISA existir em cada hospedeiro para atende-lo. A conferencia e textual
de proposito — e barata, roda em qualquer maquina e nao precisa compilar nada.
"""
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PAGINA = RAIZ / "motor-web/biblioteca.html"
MAC = RAIZ / "motor-web/macos/Sources/BibliotecaMacWeb/BibliotecaWebApp.swift"
WINDOWS = RAIZ / "motor-web/tauri/src-tauri/src/lib.rs"

# recurso -> (padrao na pagina, exigencia no Mac, exigencia no Windows, explicacao)
# A exigencia None significa "o hospedeiro atende sem precisar de codigo nosso".
RECURSOS = [
    ("confirm()",
     r"\bconfirm\s*\(",
     r"runJavaScriptConfirmPanelWithMessage",
     None,
     "sem o painel, o WKWebView devolve FALSE na hora e a pagina age como se o usuario tivesse recusado"),

    ("alert()",
     r"(?<![\w.])alert\s*\(",
     r"runJavaScriptAlertPanelWithMessage",
     None,
     "sem o painel, o alerta simplesmente nao aparece"),

    ("prompt()",
     r"(?<![\w.])prompt\s*\(",
     r"runJavaScriptTextInputPanelWithPrompt",
     None,
     "sem o painel, o prompt devolve nulo"),

    # A pagina NAO chama window.print() em si mesma: no Mac ela manda o HTML
    # para o lado nativo, e no Tauri/navegador usa um iframe escondido. Entao o
    # contrato a conferir e o do Mac. Minha primeira versao desta regra procurava
    # "window.print" no texto e acusava um COMENTARIO e o documento gerado —
    # falso positivo, e portao que grita a toa some do radar igual a portao mudo.
    ("imprimir pelo lado nativo",
     r"messageHandlers\.imprimir",
     r"ImpressorDeHTML|NSPrintOperation",
     None,
     "o window.print() nao existe no WKWebView e o window.open devolve nulo"),

    ("abrir endereco externo",
     r'target\s*=\s*"_blank"|href\s*=\s*"https?:',
     r"decidePolicyFor|NSWorkspace",
     r"abrir_endereco",
     "um <a target=_blank> nao navega, nao abre aplicativo e nao reporta erro"),

    ("area de transferencia",
     r"navigator\.clipboard|messageHandlers\.copiar|copiar_texto",
     r'name == "copiar"|case "copiar"',
     r"fn copiar_texto",
     "navigator.clipboard nao existe a partir de file:// no WKWebView"),

    ("salvar arquivo",
     r"messageHandlers\.salvarArquivo|salvar_arquivo",
     r'salvarArquivo',
     r"fn salvar_tsv",
     "blob: + download nao grava nada no WKWebView"),
]


COMENTARIO = re.compile(r"^\s*(//|///|\*|<!--|#)")


def ocorrencias_de(padrao, texto):
    """Conta ocorrencias IGNORANDO as que estao em linha de comentario.

    Duas versoes anteriores disto estavam erradas, e cada erro ensina:

    1. Contar tudo acusava `messageHandlers.salvar` porque EU havia escrito esse
       nome num comentario explicando que ele nao existe. Portao que grita a toa
       some do radar tao rapido quanto portao mudo.

    2. Apagar os comentarios do texto inteiro antes de procurar foi pior: um
       `/*` solto dentro de alguma string engoliu tudo ate o `*/` seguinte, e o
       portao ficou VERDE por ter apagado justamente o que devia conferir —
       `confirm()` caiu de 13 para 6 usos e quatro recursos sumiram.

    Por isso agora a decisao e por LINHA: acha-se a ocorrencia no texto intacto
    e so entao se pergunta se aquela linha e comentario. Nada e removido, logo
    nada pode ser comido por engano.
    """
    n = 0
    for m in re.finditer(padrao, texto):
        inicio_linha = texto.rfind("\n", 0, m.start()) + 1
        fim_linha = texto.find("\n", m.start())
        linha = texto[inicio_linha:fim_linha if fim_linha != -1 else len(texto)]
        if not COMENTARIO.match(linha):
            n += 1
    return n


def achados(padrao, texto):
    """Os valores capturados, pelas mesmas regras de `ocorrencias`."""
    fora = set()
    for m in re.finditer(padrao, texto):
        inicio_linha = texto.rfind("\n", 0, m.start()) + 1
        fim_linha = texto.find("\n", m.start())
        linha = texto[inicio_linha:fim_linha if fim_linha != -1 else len(texto)]
        if not COMENTARIO.match(linha):
            fora.add(m.group(1))
    return fora


def main():
    pagina = PAGINA.read_text(encoding="utf-8")
    mac = MAC.read_text(encoding="utf-8")
    win = WINDOWS.read_text(encoding="utf-8")

    print(f"pagina:  {PAGINA.relative_to(RAIZ)}")
    print(f"Mac:     {MAC.relative_to(RAIZ)}")
    print(f"Windows: {WINDOWS.relative_to(RAIZ)}\n")

    faltas = []
    usados = 0
    for nome, na_pagina, no_mac, no_windows, porque in RECURSOS:
        ocorrencias = ocorrencias_de(na_pagina, pagina)
        if ocorrencias == 0:
            print(f"   —  {nome:26s} a pagina nao usa")
            continue
        usados += 1
        linha = f"   ok {nome:26s} {ocorrencias:3d} uso(s)"
        for hosp, exig, fonte in (("Mac", no_mac, mac), ("Windows", no_windows, win)):
            if exig is None:
                continue
            if not re.search(exig, fonte):
                faltas.append((nome, hosp, ocorrencias, porque))
                linha = linha.replace("   ok", "   !!", 1)
        print(linha)

    # ---------------------------------------------------------------
    # Parte B: as pontes, conferidas SOZINHAS.
    #
    # Nao ha lista escrita a mao aqui: tudo que a pagina chama tem de existir do
    # outro lado, e e o proprio codigo que diz o que chama. Assim, renomear um
    # comando no Rust ou tirar um handler do Swift aparece na hora.
    # ---------------------------------------------------------------
    print()
    chamadas_tauri = achados(r'invoke\(\s*["\'`]([a-z_]+)["\'`]', pagina)
    comandos_rust = set(re.findall(r'#\[tauri::command\]\s*(?:pub\s+)?fn\s+([a-z_]+)', win))
    orfas_tauri = sorted(chamadas_tauri - comandos_rust)
    print(f"   ponte do Windows: a pagina chama {len(chamadas_tauri)} comando(s); "
          f"o Rust expoe {len(comandos_rust)}")
    for c in orfas_tauri:
        faltas.append((f'invoke("{c}")', "Windows", 1, "a pagina chama, o Rust nao expoe esse comando"))

    chamadas_mac = achados(r'messageHandlers\.([A-Za-z]+)', pagina)
    handlers_mac = set(re.findall(r'add\(self,\s*name:\s*"([A-Za-z]+)"', mac))
    handlers_mac |= set(re.findall(r'case\s+"([A-Za-z]+)"', mac))
    orfas_mac = sorted(chamadas_mac - handlers_mac)
    print(f"   ponte do Mac:     a pagina chama {len(chamadas_mac)} handler(es); "
          f"o Swift registra {len(handlers_mac)}")
    for c in orfas_mac:
        faltas.append((f"messageHandlers.{c}", "Mac", 1, "a pagina chama, o Swift nao registra esse handler"))

    if chamadas_tauri and not comandos_rust:
        print("   ABORTADO: nao reconheci comando nenhum no Rust — a conferencia nao olhou nada.")
        return 1
    if chamadas_mac and not handlers_mac:
        print("   ABORTADO: nao reconheci handler nenhum no Swift — a conferencia nao olhou nada.")
        return 1

    print()
    if not faltas:
        # Recusar o zero: se nenhum recurso foi reconhecido, o teste nao
        # conferiu nada e estar verde nao significa coisa alguma.
        if usados == 0:
            print("ABORTADO: nenhum recurso reconhecido na pagina — o portao nao olhou nada.")
            return 1
        print(f"Tudo atendido. {usados} recurso(s) conferido(s) nos dois hospedeiros.")
        return 0

    print(f"FALTAM {len(faltas)} atendimento(s):\n")
    for nome, hosp, n, porque in faltas:
        print(f"   {nome} — a pagina usa {n} vez(es), o {hosp} NAO atende")
        print(f"      {porque}\n")
    return 1


if __name__ == "__main__":
    sys.exit(main())
