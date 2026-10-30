#!/usr/bin/env python3
"""Vigia diario: olha a biblioteca do Kindle e avisa quando aparece livro novo.

So LE. Nunca escreve em biblioteca.txt — a insercao continua sendo pelo botao
"Atualizar do Kindle" do aplicativo do Mac, com a conferencia do usuario.

    ./bin/vigia-kindle.py              roda uma vez, agora
    ./bin/vigia-kindle.py --sem-abrir  nao abre o Kindle; le o banco como esta
    ./bin/vigia-kindle.py --instalar   agenda para todo dia ao meio-dia
    ./bin/vigia-kindle.py --desinstalar
    ./bin/vigia-kindle.py --estado     mostra o agendamento e as ultimas linhas do log

POR QUE ELE ABRE O KINDLE (medido em 30/10/2026, e e o ponto todo)

O banco do Kindle no Mac NAO se atualiza sozinho: so sincroniza quando o
aplicativo roda. No dia em que escrevi isto o banco estava com 20 dias, e
escondia "Judas", do Amos Oz, comprado em 18/10 — ou seja, uma tarefa diaria
que apenas LESSE o banco responderia "nenhum livro novo" para sempre, com cara
de estar funcionando. Abrir o Kindle escondido (`open -g -j`) atualizou o banco
em menos de 5 segundos, com a janela invisivel, e o livro apareceu.

O PORTAO: IDADE ANTES DE CONCLUSAO

Depois da tentativa de sincronizar, se o banco ainda estiver velho, este
programa avisa "o Kindle nao sincronizou" e **nao** diz que nao ha livro novo.
Silencio tem de significar "conferi e nao ha", nunca "nao consegui olhar" —
ver a licao `portao-que-nao-olha-passa-verde` do projeto.
"""
import argparse, datetime, importlib.util, os, plistlib, subprocess, sys, time
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent
LOG = Path.home() / "Library/Logs/biblioteca-vigia-kindle.log"
AGENDA = Path.home() / "Library/LaunchAgents/larc.biblioteca.vigia-kindle.plist"
ROTULO = "larc.biblioteca.vigia-kindle"
APP = "Amazon Kindle"

# Banco mais velho que isto, DEPOIS da tentativa de sincronizar, e banco que
# nao sincronizou. Um dia e folgado: a tarefa roda todo dia.
LIMITE_DIAS = 1.0
ESPERA_MAX = 120          # segundos esperando o banco mudar
HORA_DA_TAREFA = 12       # meio-dia

SEM_NOVIDADE, COM_NOVIDADE, NAO_OLHEI = 0, 10, 20


def conciliador():
    """Importa bin/conciliar-kindle.py (o hifen impede o `import` normal)."""
    alvo = AQUI / "conciliar-kindle.py"
    spec = importlib.util.spec_from_file_location("conciliar_kindle", alvo)
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


def kindle_rodando():
    r = subprocess.run(["pgrep", "-f", f"/{APP}.app/"], capture_output=True)
    return r.returncode == 0


def sincroniza(idade_antes, idade_de):
    """Abre o Kindle escondido e espera o banco mudar. Devolve se foi ele que abriu."""
    if idade_antes is not None and idade_antes <= LIMITE_DIAS:
        return False                      # banco ja esta fresco; nao incomoda
    ja_estava = kindle_rodando()
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


def fecha_o_kindle():
    subprocess.run(["osascript", "-e", f'tell application "{APP}" to quit'],
                   check=False, capture_output=True)


def uma_passada(abrir=True):
    ck = conciliador()
    idade_antes = ck.idade_do_banco()
    if idade_antes is None:
        anota("[!] nao achei o banco do Kindle — o aplicativo nunca sincronizou neste Mac")
        avisa("Kindle", "Nao achei a biblioteca do Kindle neste Mac.")
        return NAO_OLHEI

    eu_abri = sincroniza(idade_antes, ck.idade_do_banco) if abrir else False
    try:
        idade = ck.idade_do_banco()
        if idade is None or idade > LIMITE_DIAS:
            dias = "?" if idade is None else f"{idade:.1f}"
            anota(f"[!] o Kindle NAO sincronizou — banco com {dias} dias. "
                  "Nao sei dizer se ha livro novo.")
            avisa("Kindle nao sincronizou",
                  f"O banco local esta com {dias} dias. Abra o Kindle para sincronizar.")
            return NAO_OLHEI

        r = ck.analisar()
        novos, outra, completar = r["novos"], r["outra_edicao"], r["completar"]
        quantos = len(novos) + len(outra) + len(completar)
        if not quantos:
            anota(f"[=] nada novo — {len(r['livros'])} livros no Kindle, "
                  f"{len(r['conferidos'])} conferidos (banco de {idade*24:.0f} h)")
            return SEM_NOVIDADE

        anota(f"[+] {quantos} para cadastrar — "
              f"{len(novos)} novo(s), {len(outra)} edicao Kindle de impresso, "
              f"{len(completar)} sem link")
        for i, _ in novos + outra:
            anota(f"      {i['compra']}  {i['titulo']}  — {i['autor']}")
        for _, l in completar:
            anota(f"      linha {l['n']}  {l['titulo']}  (falta o link)")
        plural = "livro novo" if quantos == 1 else "livros novos"
        avisa(f"{quantos} {plural} no Kindle",
              "Abra a Biblioteca no Mac e toque em Atualizar do Kindle.")
        return COM_NOVIDADE
    finally:
        if eu_abri:
            fecha_o_kindle()


def plist():
    return {
        "Label": ROTULO,
        # O python do SISTEMA, de proposito: `sys.executable` aqui seria o do
        # anaconda, e a tarefa morreria calada no dia em que ele mudasse de
        # lugar. Este programa so usa a biblioteca padrao.
        "ProgramArguments": ["/usr/bin/python3", "-I", str(AQUI / "vigia-kindle.py")],
        "WorkingDirectory": str(RAIZ),
        "StartCalendarInterval": [{"Hour": HORA_DA_TAREFA, "Minute": 0}],
        "StandardErrorPath": str(LOG.with_suffix(".erro.log")),
        "RunAtLoad": False,
        "ProcessType": "Background",
    }


def instala():
    AGENDA.parent.mkdir(parents=True, exist_ok=True)
    with AGENDA.open("wb") as f:
        plistlib.dump(plist(), f)
    alvo = f"gui/{os.getuid()}/{ROTULO}"
    subprocess.run(["launchctl", "bootout", alvo], capture_output=True)
    r = subprocess.run(["launchctl", "bootstrap", f"gui/{os.getuid()}", str(AGENDA)],
                       capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"launchctl recusou: {r.stderr.strip() or r.returncode}")
    print(f"agendado: todo dia as {HORA_DA_TAREFA:02d}:00  ({AGENDA})")
    print(f"log em {LOG}")


def desinstala():
    subprocess.run(["launchctl", "bootout", f"gui/{os.getuid()}/{ROTULO}"],
                   capture_output=True)
    if AGENDA.exists():
        AGENDA.unlink()
    print("agendamento removido")


def estado():
    r = subprocess.run(["launchctl", "print", f"gui/{os.getuid()}/{ROTULO}"],
                       capture_output=True, text=True)
    if r.returncode:
        print("NAO esta agendado (rode --instalar)")
    else:
        for ln in r.stdout.splitlines():
            if any(c in ln for c in ("state =", "runs =", "last exit", "program =")):
                print(ln.strip())
    print(f"\n--- ultimas linhas de {LOG}")
    if LOG.exists():
        for ln in LOG.read_text(encoding="utf-8").splitlines()[-12:]:
            print(ln)
    else:
        print("(ainda nao rodou)")


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--instalar", action="store_true")
    p.add_argument("--desinstalar", action="store_true")
    p.add_argument("--estado", action="store_true")
    p.add_argument("--sem-abrir", action="store_true",
                   help="nao abre o Kindle; le o banco como esta")
    a = p.parse_args()
    if a.instalar:
        return instala()
    if a.desinstalar:
        return desinstala()
    if a.estado:
        return estado()
    sys.exit(uma_passada(abrir=not a.sem_abrir))


if __name__ == "__main__":
    main()
