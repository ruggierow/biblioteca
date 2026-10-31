#!/usr/bin/env python3
"""Vigia diario: olha a biblioteca do Audible e avisa quando aparece audiolivro.

So LE. Nunca escreve em biblioteca.txt — a insercao continua sendo pelo botao
"Atualizar do Kindle e do Audible" do aplicativo do Mac, com a conferencia do
usuario.

    ./bin/vigia-audible.py              roda uma vez, agora
    ./bin/vigia-audible.py --sem-abrir  nao abre o Audible; le o banco como esta

Nao tem agendamento proprio: quem agenda e `bin/tarefas-diarias.py`, que roda
este vigia, o do Kindle e o espelho no mesmo aplicativo autorizado.

POR QUE ELE ABRE O AUDIBLE (medido em 31/10/2026, e e o ponto todo)

Igualzinho ao Kindle: o banco local SO sincroniza quando o aplicativo roda. No
dia em que escrevi isto o banco estava parado desde a vespera e escondia
"Memórias Póstumas de Brás Cubas", adicionado em 30/10 — uma tarefa diaria que
apenas LESSE o banco responderia "nenhum audiolivro novo" para sempre, com cara
de estar funcionando. Abrir o Audible escondido (`open -g -j`) atualizou o
banco em 2 segundos, com a janela invisivel, e a biblioteca foi de 2 para 3.

O PORTAO: IDADE ANTES DE CONCLUSAO

Depois da tentativa de sincronizar, se o banco ainda estiver velho, este
programa avisa "o Audible nao sincronizou" e **nao** diz que nao ha novidade.
Silencio tem de significar "conferi e nao ha", nunca "nao consegui olhar" —
ver a licao `portao-que-nao-olha-passa-verde` do projeto.
"""
import argparse, datetime, importlib.util, subprocess, sys, time
from pathlib import Path

AQUI = Path(__file__).resolve().parent
LOG = Path.home() / "Library/Logs/biblioteca-vigia-audible.log"
APP = "Audible"

# Banco mais velho que isto, DEPOIS da tentativa de sincronizar, e banco que
# nao sincronizou. Um dia e folgado: a tarefa roda todo dia.
LIMITE_DIAS = 1.0
ESPERA_MAX = 120          # segundos esperando o banco mudar

SEM_NOVIDADE, COM_NOVIDADE, NAO_OLHEI = 0, 10, 20


def conciliador():
    """Importa bin/conciliar-audible.py (o hifen impede o `import` normal)."""
    alvo = AQUI / "conciliar-audible.py"
    spec = importlib.util.spec_from_file_location("conciliar_audible", alvo)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def anota(texto):
    agora = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(f"{agora}  {texto}\n")
    print(texto)


def avisa(titulo, texto):
    """Aviso do sistema. Se a notificacao estiver barrada, o log ainda registra."""
    roteiro = (f'display notification {texto!r} with title "Biblioteca" '
               f'subtitle {titulo!r} sound name "Glass"')
    try:
        subprocess.run(["osascript", "-e", roteiro], check=False,
                       capture_output=True, timeout=20)
    except Exception as e:                                  # noqa: BLE001
        anota(f"[!] nao consegui mostrar o aviso: {e}")


def audible_rodando():
    r = subprocess.run(["pgrep", "-f", f"/{APP}.app/"], capture_output=True)
    return r.returncode == 0


def sincroniza(idade_antes, idade_de):
    """Abre o Audible escondido e espera o banco mudar. Devolve se foi ele que abriu."""
    if idade_antes is not None and idade_antes <= LIMITE_DIAS:
        return False                      # banco ja esta fresco; nao incomoda
    ja_estava = audible_rodando()
    if not ja_estava:
        # -g: sem trazer para a frente.  -j: escondido, sem janela na tela.
        subprocess.run(["open", "-g", "-j", "-a", APP], check=False)
    limite = time.time() + ESPERA_MAX
    while time.time() < limite:
        time.sleep(2)
        agora = idade_de()
        if agora is not None and (idade_antes is None or agora < idade_antes):
            return not ja_estava
    return not ja_estava


def fecha_o_audible():
    subprocess.run(["osascript", "-e", f'tell application "{APP}" to quit'],
                   check=False, capture_output=True)


def uma_passada(abrir=True):
    ca = conciliador()
    idade_antes = ca.idade_do_banco()
    if idade_antes is None:
        anota("[!] nao achei a biblioteca do Audible — o aplicativo nunca "
              "entrou na conta neste Mac")
        avisa("Audible", "Nao achei a biblioteca do Audible neste Mac.")
        return NAO_OLHEI

    eu_abri = sincroniza(idade_antes, ca.idade_do_banco) if abrir else False
    try:
        idade = ca.idade_do_banco()
        if idade is None or idade > LIMITE_DIAS:
            dias = "?" if idade is None else f"{idade:.1f}"
            anota(f"[!] o Audible NAO sincronizou — banco com {dias} dias. "
                  "Nao sei dizer se ha audiolivro novo.")
            avisa("Audible nao sincronizou",
                  f"O banco local esta com {dias} dias. Abra o Audible para sincronizar.")
            return NAO_OLHEI

        r = ca.analisar()
        entram = r["entram"]
        if not entram:
            anota(f"[=] nada novo — {len(r['biblioteca'])} na biblioteca do Audible, "
                  f"{len(r['conferidos'])} conferidos (banco de {idade*24:.0f} h)")
            return SEM_NOVIDADE

        anota(f"[+] {len(entram)} audiolivro(s) para cadastrar")
        for i, fonte, ano in entram:
            onde = "sua biblioteca" if i["na_biblioteca"] else "incluso no plano"
            anota(f"      {i['titulo']}  ({onde})")
        plural = "audiolivro novo" if len(entram) == 1 else "audiolivros novos"
        avisa(f"{len(entram)} {plural} no Audible",
              "Abra a Biblioteca no Mac e toque em Atualizar do Kindle e do Audible.")
        return COM_NOVIDADE
    finally:
        if eu_abri:
            fecha_o_audible()


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--sem-abrir", action="store_true",
                   help="nao abre o Audible; le o banco como esta")
    a = p.parse_args()
    sys.exit(uma_passada(abrir=not a.sem_abrir))


if __name__ == "__main__":
    main()
