#!/usr/bin/env python3
"""As tarefas diarias da Biblioteca, num aplicativo que o macOS deixa trabalhar.

    ./bin/tarefas-diarias.py              roda uma vez, agora
    ./bin/tarefas-diarias.py --instalar   monta o aplicativo e agenda para as 12:00
    ./bin/tarefas-diarias.py --estado     mostra o agendamento, a permissao e o log
    ./bin/tarefas-diarias.py --desinstalar

Faz duas coisas, nesta ordem:

  1. VIGIA DO KINDLE  — sincroniza o Kindle e avisa se ha livro novo para
     cadastrar. Nunca escreve na base: a insercao e pelo botao do aplicativo,
     com a sua conferencia.
  2. ESPELHO PARA AS NUVENS — roda `espelhar.sh`, que e o que leva a base ate
     o Android. Ele tem guarda propria e RECUSA quando o destino tem coisa que
     a origem nao tem; aqui a recusa vira aviso, nao erro.

POR QUE ISTO E UM APLICATIVO, E NAO UM SCRIPT SOLTO (medido em 30/10/2026)

Um programa disparado pelo launchd nao alcanca nem o banco do Kindle nem a
pasta do iCloud:

    banco do Kindle    Operation not permitted
    base no iCloud     Operation not permitted
    ~/Library/CloudStorage   le

A permissao nao aparece em dialogo nenhum — nem para um aplicativo assinado
com Developer ID, nem em primeiro plano. Tem de ser concedida a mao, UMA vez,
em Ajustes do Sistema -> Privacidade e Seguranca -> Acesso Total ao Disco.

E uma permissao e concedida a um APLICATIVO, nao a um arquivo .py. Por isso o
`--instalar` monta `Tarefas da Biblioteca.app` em ~/Library/Application Support
e agenda ELE. Um .py dentro de /usr/bin/python3 nao teria onde ser autorizado
sem dar Acesso Total ao Disco a todo e qualquer Python da maquina.

O `--estado` CONFERE a permissao de verdade, tentando ler. Enquanto ela faltar,
o programa diz isso em voz alta em vez de concluir "nada novo" — ver a licao
`portao-que-nao-olha-passa-verde`.
"""
import argparse, datetime, importlib.util, os, plistlib, shutil, subprocess, sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent
SUPORTE = Path.home() / "Library/Application Support/Biblioteca"
APP = SUPORTE / "Tarefas da Biblioteca.app"
LOG = Path.home() / "Library/Logs/biblioteca-tarefas.log"
AGENDA = Path.home() / "Library/LaunchAgents/larc.biblioteca.tarefas.plist"
ROTULO = "larc.biblioteca.tarefas"
HORA = 12

IDENTIDADE = "Developer ID Application: WILSON VICENTE RUGGIERO (Q87ANATBD3)"

# O executavel do pacote tem de ser um Mach-O DE VERDADE, e nao pode dar `exec`.
#
# POR QUE (medido em 30/10/2026, e custou duas autorizacoes do usuario)
#
# O TCC nao autoriza o PACOTE, autoriza o binario que faz a leitura. A primeira
# versao deste executavel era um script de duas linhas que dava
# `exec /usr/bin/python3`; depois do exec o processo PASSAVA A SER o python3, da
# Apple, e o Acesso Total ao Disco concedido ao `larc.biblioteca.tarefas` nao
# tinha a quem se aplicar. Negado em silencio, tanto pelo launchd quanto pelo
# LaunchServices. O contraste estava a vista: o `Biblioteca Web.app`, que le
# esse mesmo banco sem reclamar, tem um Mach-O em Contents/MacOS.
#
# Com `posix_spawn` o pai continua vivo sendo o aplicativo autorizado, e o
# python3 filho herda a permissao pelo processo responsavel — e exatamente
# assim que o Terminal empresta o Acesso Total ao Disco ao python3 que roda
# dentro dele.
LANCADOR_C = r"""
/* Lancador do "Tarefas da Biblioteca.app".  GERADO por bin/tarefas-diarias.py
   — nao edite aqui: edite o LANCADOR_C naquele arquivo. */
#include <spawn.h>
#include <stdlib.h>
#include <sys/wait.h>
#include <unistd.h>

extern char **environ;

int main(int argc, char *argv[])
{{
    /* o roteiro e fixo; o resto da linha de comando passa adiante */
    char *fixos[] = {{"/usr/bin/python3", "-I", "{roteiro}"}};
    const int n = 3;
    char **args = malloc(sizeof(char *) * (n + argc));
    if (!args) return 70;
    for (int i = 0; i < n; i++) args[i] = fixos[i];
    for (int i = 1; i < argc; i++) args[n + i - 1] = argv[i];
    args[n + argc - 1] = NULL;

    /* posix_spawn, e NAO execv: o pai tem de continuar vivo, porque e ELE que
       esta autorizado no Acesso Total ao Disco. Ver o comentario no .py. */
    pid_t filho;
    if (posix_spawn(&filho, "/usr/bin/python3", NULL, NULL, args, environ) != 0)
        return 70;

    int estado = 0;
    if (waitpid(filho, &estado, 0) < 0) return 70;
    /* devolve o mesmo codigo do vigia: 0 sem novidade, 10 com, 20 nao olhei */
    if (WIFEXITED(estado)) return WEXITSTATUS(estado);
    return 70;
}}
"""


def anota(texto):
    agora = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(f"{agora}  {texto}\n")
    print(texto)


def avisa(subtitulo, texto):
    roteiro = (f'display notification {texto!r} with title "Biblioteca" '
               f'subtitle {subtitulo!r} sound name "Glass"')
    subprocess.run(["osascript", "-e", roteiro], check=False,
                   capture_output=True, timeout=20)


def vigia():
    """Importa bin/vigia-kindle.py (o hifen impede o `import` normal)."""
    spec = importlib.util.spec_from_file_location("vigia_kindle", AQUI / "vigia-kindle.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def tenho_permissao():
    """Leitura de VERDADE, nao suposicao: o metadado e legivel mesmo sem ela."""
    alvos = [
        Path.home() / "Library/Containers/com.amazon.Lassen/Data/Library/Protected/BookData.sqlite",
        Path.home() / "Library/Mobile Documents/com~apple~CloudDocs/Biblioteca/biblioteca.txt",
    ]
    for a in alvos:
        if not a.exists():
            continue
        try:
            with a.open("rb") as f:
                f.read(16)
        except OSError:
            return False, a
    return True, None


def espelhar():
    r = subprocess.run([str(AQUI / "espelhar.sh")], cwd=RAIZ,
                       capture_output=True, text=True, timeout=600)
    saida = (r.stdout or "") + (r.returncode and (r.stderr or "") or "")
    if "RECUSADO" in saida:
        pendentes = [l.strip() for l in saida.splitlines() if "RECUSADO" in l]
        anota(f"[!] espelho RECUSOU: {len(pendentes)} arquivo(s) — o destino tem coisa "
              "que a base nao tem. Rode ./bin/espelhar.sh e decida.")
        avisa("Espelho recusado", "O Drive tem coisa que a base nao tem. Confira no Mac.")
        return False
    copiados = sum(1 for l in saida.splitlines() if ": copiado" in l)
    anota(f"[=] espelho: {copiados} arquivo(s) copiado(s) para as nuvens")
    return True


def uma_passada():
    ok, barrado = tenho_permissao()
    if not ok:
        anota(f"[!] SEM PERMISSAO para ler {barrado.name} — nao sei dizer se ha livro novo. "
              "Ajustes do Sistema -> Privacidade -> Acesso Total ao Disco -> Tarefas da Biblioteca")
        avisa("Falta permissao",
              "Autorize 'Tarefas da Biblioteca' em Acesso Total ao Disco.")
        return 20

    v = vigia()
    codigo = v.uma_passada(abrir=True)     # o vigia tem o portao da idade dele
    espelhar()
    return codigo


def monta_app():
    """Monta o .app em volta deste mesmo .py. O codigo continua sendo o do repo."""
    if APP.exists():
        shutil.rmtree(APP)
    (APP / "Contents/MacOS").mkdir(parents=True)
    executavel = APP / "Contents/MacOS/tarefas"
    # O .c fica FORA do pacote: arquivo solto em Contents/MacOS quebra o selo.
    fonte_c = SUPORTE / "tarefas.c"
    fonte_c.write_text(LANCADOR_C.format(roteiro=AQUI / "tarefas-diarias.py"),
                       encoding="utf-8")
    r = subprocess.run(["cc", "-O2", "-Wall", "-o", str(executavel), str(fonte_c)],
                       capture_output=True, text=True)
    fonte_c.unlink(missing_ok=True)
    if r.returncode or not executavel.exists():
        # Cair para o script de shell aqui seria refazer o defeito de 30/10 em
        # silencio: o pacote montaria, autorizaria e NUNCA leria o banco.
        sys.exit("nao consegui compilar o lancador do pacote "
                 f"(`cc` respondeu {r.returncode}):\n{r.stderr.strip()[:400]}\n"
                 "sem ele o aplicativo NAO consegue ler a biblioteca do Kindle, "
                 "por mais que voce o autorize.")
    executavel.chmod(0o755)
    with (APP / "Contents/Info.plist").open("wb") as f:
        plistlib.dump({
            "CFBundleIdentifier": "larc.biblioteca.tarefas",
            "CFBundleExecutable": "tarefas",
            "CFBundleName": "Tarefas da Biblioteca",
            "CFBundlePackageType": "APPL",
            "CFBundleShortVersionString": (RAIZ / "VERSION").read_text().strip(),
            "LSBackgroundOnly": True,
        }, f)
    # Com Developer ID a assinatura e ESTAVEL: a autorizacao do Acesso Total ao
    # Disco sobrevive a uma remontagem. Com ad-hoc o selo muda a cada vez e voce
    # teria de reautorizar. Mas o `codesign` PENDURA esperando o chaveiro quando
    # ele esta trancado — travou aqui em 30/10/2026 e so morreu no `kill`. Por
    # isso o limite de tempo: melhor cair no ad-hoc do que ficar parado.
    try:
        r = subprocess.run(["codesign", "--force", "--sign", IDENTIDADE, str(APP)],
                           capture_output=True, timeout=25)
        if r.returncode == 0:
            return APP
        motivo = (r.stderr or b"").decode(errors="replace").strip()[:120]
    except subprocess.TimeoutExpired:
        motivo = "o chaveiro nao respondeu em 25 s (esta trancado?)"
    subprocess.run(["codesign", "--force", "--sign", "-", str(APP)], capture_output=True)
    print(f"   assinado AD-HOC — {motivo}")
    print("   (funciona, mas remontar o aplicativo exigira autorizar de novo)")
    return APP


def instala():
    monta_app()
    AGENDA.parent.mkdir(parents=True, exist_ok=True)
    with AGENDA.open("wb") as f:
        plistlib.dump({
            "Label": ROTULO,
            "ProgramArguments": [str(APP / "Contents/MacOS/tarefas")],
            "WorkingDirectory": str(RAIZ),
            "StartCalendarInterval": [{"Hour": HORA, "Minute": 0}],
            "StandardErrorPath": str(LOG.with_suffix(".erro.log")),
            "RunAtLoad": False,
            "ProcessType": "Background",
        }, f)
    alvo = f"gui/{os.getuid()}"
    subprocess.run(["launchctl", "bootout", f"{alvo}/{ROTULO}"], capture_output=True)
    r = subprocess.run(["launchctl", "bootstrap", alvo, str(AGENDA)],
                       capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"launchctl recusou: {r.stderr.strip() or r.returncode}")
    print(f"aplicativo: {APP}")
    print(f"agendado:   todo dia as {HORA:02d}:00")
    print(f"log:        {LOG}")
    print("\nFALTA UM PASSO, QUE SO VOCE PODE DAR:")
    print("   Ajustes do Sistema -> Privacidade e Seguranca -> Acesso Total ao Disco")
    print(f"   acrescente '{APP.name}' (o + abre o seletor; a pasta e")
    print(f"   {APP.parent})")
    print("\nDepois rode:  ./bin/tarefas-diarias.py --estado")


def desinstala():
    subprocess.run(["launchctl", "bootout", f"gui/{os.getuid()}/{ROTULO}"], capture_output=True)
    AGENDA.unlink(missing_ok=True)
    if APP.exists():
        shutil.rmtree(APP)
    print("agendamento e aplicativo removidos")
    print("Lembre de tirar 'Tarefas da Biblioteca' do Acesso Total ao Disco.")


def estado():
    r = subprocess.run(["launchctl", "print", f"gui/{os.getuid()}/{ROTULO}"],
                       capture_output=True, text=True)
    print("agendamento:", "ATIVO" if not r.returncode else "nao instalado")
    for ln in r.stdout.splitlines():
        if any(c in ln for c in ("state =", "runs =", "last exit")):
            print("   ", ln.strip())
    print("aplicativo: ", APP if APP.exists() else "nao montado")

    # A permissao NAO e conferida aqui de proposito. Rodando no terminal, este
    # programa herda a permissao de quem o chamou — em 30/10/2026 ele imprimiu
    # "OK" enquanto o aplicativo, pelo launchd, era NEGADO. Estado tem de ser o
    # que o APLICATIVO mediu, nao o que o terminal consegue.
    ultimo = ""
    if LOG.exists():
        for ln in reversed(LOG.read_text(encoding="utf-8").splitlines()):
            if "[" in ln:
                ultimo = ln
                break
    if not ultimo:
        print("permissao:   nao sei — o aplicativo ainda nao rodou. Use --conferir")
    elif "SEM PERMISSAO" in ultimo:
        print(f"permissao:   FALTA — foi o que o aplicativo viu em {ultimo[:16]}")
        print("             Ajustes do Sistema -> Privacidade e Seguranca ->")
        print("             Acesso Total ao Disco -> + -> Tarefas da Biblioteca")
    else:
        print(f"permissao:   OK — o aplicativo leu em {ultimo[:16]}")

    print(f"\n--- ultimas linhas de {LOG}")
    if LOG.exists():
        for ln in LOG.read_text(encoding="utf-8").splitlines()[-10:]:
            print(ln)
    else:
        print("(ainda nao rodou)")


def confere():
    """Dispara pelo launchd e mostra o resultado. E a unica medida fiel: rodar
    este .py direto mede a permissao de QUEM CHAMA, nao a do aplicativo."""
    antes = LOG.stat().st_mtime if LOG.exists() else 0
    r = subprocess.run(["launchctl", "kickstart", "-p", f"gui/{os.getuid()}/{ROTULO}"],
                       capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"nao consegui disparar: {r.stderr.strip()} (instalado?)")
    print("disparado pelo launchd; esperando o aplicativo responder…")
    import time
    for _ in range(60):
        time.sleep(2)
        if LOG.exists() and LOG.stat().st_mtime > antes:
            break
    else:
        print("o aplicativo nao escreveu nada em 2 min.")
        return
    for ln in LOG.read_text(encoding="utf-8").splitlines()[-8:]:
        print("   ", ln)


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--instalar", action="store_true")
    p.add_argument("--desinstalar", action="store_true")
    p.add_argument("--estado", action="store_true")
    p.add_argument("--conferir", action="store_true",
                   help="manda o launchd rodar AGORA e mostra o que o aplicativo viu")
    a = p.parse_args()
    if a.conferir:
        return confere()
    if a.instalar:
        return instala()
    if a.desinstalar:
        return desinstala()
    if a.estado:
        return estado()
    sys.exit(uma_passada())


if __name__ == "__main__":
    main()
