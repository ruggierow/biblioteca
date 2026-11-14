#!/usr/bin/env python3
"""Escreve docs/index.html — a pagina do app, servida pelo GitHub Pages em
https://ruggierow.github.io/biblioteca/

    ./bin/gerar-pagina.py            gera a pagina para a versao do VERSION
    ./bin/gerar-pagina.py --mostrar  so imprime o que mudaria, sem gravar

POR QUE GERADA, E NAO ESCRITA A MAO: ate 07/11/2026 a pagina era um artifact
do claude.ai, feito a mao na 1.9.1, e em novembro ainda anunciava setembro —
quatro novidades de uma versao dezoito atras, 897 KB para um .dmg que tem 2,1
MB e o iPhone "pelo TestFlight" quando ele ja esta na App Store. Nada disso e
descuido: pagina escrita a mao envelhece sozinha.

AS FONTES SAO AS QUE ELE JA MANTEM, nenhuma nova:

    VERSION                 o numero, uma vez so no projeto inteiro
    docs/notas-<V>.md       o titulo, a chamada e os destaques
    a release no GitHub     os tamanhos REAIS dos arquivos que o usuario baixa

Os destaques sao os cabecalhos `##` das notas, menos os que nao sao novidade
(`Instalacao`). Entao escrever as notas da versao — que ele ja faz sempre —
atualiza a pagina; nao existe um segundo texto para esquecer.

Os enderecos de download usam os NOMES FIXOS da release
(`.../releases/latest/download/Biblioteca-Mac.dmg`), que o publicar-release.sh
sobe de proposito justamente para a pagina nunca precisar ser reeditada.
"""
import json
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
REPO = "ruggierow/biblioteca"
APP_STORE = "https://apps.apple.com/app/biblioteca-pessoal/id6799312712"
# SEM o pais no caminho, de proposito: a Apple manda o visitante para a
# loja DELE. Com `/br/` quem abrisse de fora do Brasil podia cair num "item
# indisponivel" — e o manual em ingles apontava para a loja brasileira.
# Os territorios onde o app iOS esta a venda, em ordem de interesse para quem
# le a pagina. A VERDADE fica no App Store Connect (`appAvailabilityV2`, um
# item por territorio com `contentStatuses`), e quem a vigia e o
# `bin/vigia-loja.py` — mas o gerador nao pode consultar a API, senao o portao
# precisaria de rede e de credencial para regerar a pagina. Se ele acrescentar
# ou tirar um pais la, esta lista tem de mudar aqui a mao.
PAISES_IOS = ("Portugal", "Brasil", "Estados Unidos", "Canadá", "Angola", "Macau")
PLAY_TESTE = "https://play.google.com/apps/testing/com.wilson.biblioteca.biblioteca"
BAIXAR = f"https://github.com/{REPO}/releases/latest/download"

# Cabecalhos das notas que NAO sao novidade da versao.
NAO_E_NOVIDADE = {"instalacao", "instalação"}

MESES = ("janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho",
         "agosto", "setembro", "outubro", "novembro", "dezembro")


def versao():
    return (RAIZ / "VERSION").read_text().strip()


def data_da_versao(v):
    """A data da TAG v<V>, nao a de hoje.

    Carimbar o dia da geracao faria a pagina mudar sozinha a cada execucao, e
    o portao (que compara a pagina com o que o gerador produz) reprovaria no
    dia seguinte sem nada ter acontecido.
    """
    try:
        bruto = subprocess.run(
            ["git", "-C", str(RAIZ), "log", "-1", "--format=%ad",
             "--date=format:%Y-%m-%d", f"v{v}"],
            capture_output=True, text=True, timeout=10)
        if bruto.returncode == 0 and bruto.stdout.strip():
            a, m, d = (int(x) for x in bruto.stdout.strip().split("-"))
            return date(a, m, d)
    except Exception:
        pass
    return date.today()


def notas(v):
    """Titulo, chamada e destaques, lidos de docs/notas-<v>.md."""
    arq = RAIZ / "docs" / f"notas-{v}.md"
    if not arq.exists():
        sys.exit(f"Nao achei {arq.relative_to(RAIZ)} — escreva as notas antes.")
    linhas = arq.read_text().splitlines()

    chamada, destaques = [], []
    for i, l in enumerate(linhas):
        if l.startswith("## "):
            titulo = l[3:].strip()
            if titulo.lower() not in NAO_E_NOVIDADE:
                destaques.append(titulo)
        elif not chamada and l.strip() and not l.startswith("#"):
            # a chamada e o primeiro paragrafo, que pode ter mais de uma linha
            j = i
            while j < len(linhas) and linhas[j].strip():
                chamada.append(linhas[j].strip())
                j += 1
    if not chamada:
        sys.exit(f"As notas da {v} nao tem um paragrafo de abertura.")
    return " ".join(chamada), destaques


def tamanhos(v):
    """Os tamanhos dos arquivos que o usuario baixa.

    Da release no GitHub quando ela existe — e o que ele realmente recebe. Da
    dist/ local quando ainda nao, para dar para gerar a pagina ANTES de
    publicar.
    """
    por_nome = {}
    try:
        bruto = subprocess.run(
            ["gh", "api", f"repos/{REPO}/releases/tags/v{v}"],
            capture_output=True, text=True, timeout=30)
        if bruto.returncode == 0:
            for a in json.loads(bruto.stdout).get("assets", []):
                por_nome[a["name"]] = a["size"]
    except Exception:
        pass

    locais = {"Biblioteca-Mac.dmg": f"dist/Biblioteca-Mac-v{v}.dmg",
              "Biblioteca-Windows-setup.exe": f"dist/Biblioteca-{v}-setup.exe",
              "Biblioteca-Android.apk": f"dist/Biblioteca-Android-v{v}.apk"}
    for nome, rel in locais.items():
        if nome not in por_nome:
            p = RAIZ / rel
            if p.exists():
                por_nome[nome] = p.stat().st_size
    return por_nome


def legivel(n):
    if n is None:
        return None
    if n >= 10 * 1024 * 1024:
        return f"{round(n / 1024 / 1024)} MB"
    if n >= 1024 * 1024:
        return f"{n / 1024 / 1024:.1f} MB".replace(".", ",")
    return f"{round(n / 1024)} KB"


def manuais():
    """Os manuais que EXISTEM — a pagina nao oferece link para o que falta.

    Cada plataforma pode ter o manual em portugues (`manual-<p>.html`) e em
    ingles (`manual-<p>-en.html`); a pagina so cita a lingua que ja existe.
    """
    achados = []
    for arq, rotulo in (("manual-mac", "Mac"), ("manual-windows", "Windows"),
                        ("manual-ios", "iPhone"), ("manual-android", "Android")):
        linguas = []
        for sufixo, lingua in (("", "Português"), ("-en", "English")):
            formatos = [(f"{arq}{sufixo}.{e}", e.upper()) for e in ("html", "pdf")
                        if (RAIZ / "docs" / f"{arq}{sufixo}.{e}").exists()]
            if formatos:
                linguas.append((lingua, formatos))
        if linguas:
            achados.append((rotulo, linguas))
    return achados


def esc(t):
    return (t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def marcado(t):
    """O pouco de Markdown que as notas usam, virado em HTML.

    Sem isto o `**O app fala ingles.**` da primeira linha das notas sai na
    pagina com os asteriscos a mostra — foi o que apareceu na primeira
    geracao, em 07/11/2026.
    """
    t = esc(t)
    t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
    t = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"(?<![*\w])\*([^*]+)\*(?!\w)", r"<em>\1</em>", t)
    return t


def baixar(nome, tam, rotulo="Baixar"):
    peso = f" · {legivel(tam)}" if tam else ""
    return (f'    <div class="baixar">\n'
            f'      <a href="{BAIXAR}/{nome}">{rotulo}</a>\n'
            f'      <span class="arquivo">{nome}{peso}</span>\n'
            f'    </div>\n')


CSS = (RAIZ / "docs" / "pagina.css")


def monta(v, chamada, destaques, tam, hoje):
    hd = f"{hoje.day} de {MESES[hoje.month - 1]} de {hoje.year}"

    blocos = []
    for i, d in enumerate(destaques, 1):
        blocos.append(f'      <div class="novidade"><b>{i:02d}</b>'
                      f'<span>{marcado(d)}</span></div>')
    novidades = "\n".join(blocos)

    links_manuais = []
    for rotulo, linguas in manuais():
        partes = []
        for lingua, formatos in linguas:
            ligacoes = " ".join(f'<a href="{arq}">{fmt}</a>' for arq, fmt in formatos)
            partes.append(f"{lingua}: {ligacoes}")
        links_manuais.append(f'      <li><strong>{rotulo}</strong> — '
                             + " · ".join(partes) + "</li>")
    manuais_html = "\n".join(links_manuais)

    return f"""<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Biblioteca</title>
<meta name="description" content="Biblioteca {v} — catálogo dos seus livros no Mac, no Windows, no iPhone e no Android.">
<!-- PAGINA GERADA por bin/gerar-pagina.py. Nao edite a mao: a proxima release
     sobrescreve. Para mudar o texto das novidades, edite docs/notas-<v>.md. -->
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,600;1,6..72,400&amp;family=Source+Sans+3:ital,wght@0,400;0,600;1,400&amp;family=IBM+Plex+Mono:wght@400;500&amp;display=swap">
<link rel="stylesheet" href="pagina.css">
</head>
<body>

<div class="folha">

  <header class="capa">
    <div class="selo">Versão {v} · {hd}</div>
    <h1>Biblioteca</h1>
    <p class="subtitulo">O catálogo dos seus livros, no computador e no celular. Abaixo está como instalá-lo em cada aparelho.</p>
  </header>

  <div class="novidades">
    <h2>O que mudou na {v}</h2>
    <p class="chamada">{marcado(chamada)}</p>
{novidades}
  </div>

  <nav class="escolha">
    <p>Leia só a parte do seu aparelho:</p>
    <div class="atalhos">
      <a class="atalho" href="#iphone"><strong>iPhone</strong><small>pela App Store</small></a>
      <a class="atalho" href="#android"><strong>Android</strong><small>pela Play Store</small></a>
      <a class="atalho" href="#mac"><strong>Mac</strong><small>macOS 13 ou mais novo</small></a>
      <a class="atalho" href="#windows"><strong>Windows</strong><small>10 ou 11</small></a>
    </div>
  </nav>

  <section class="plataforma" id="iphone">
    <h2>No iPhone</h2>
    <div class="ficha"><span>iOS 17.6 ou mais novo</span><span>App Store</span><span>grátis</span></div>

    <div class="baixar">
      <a href="{APP_STORE}">Abrir na App Store</a>
      <span class="arquivo">Biblioteca Pessoal</span>
    </div>

    <ol class="passos">
      <li><div><p>Abra o link acima <strong>no próprio iPhone</strong> e toque em <strong>Obter</strong>.</p></div></li>
      <li><div><p>Se você já tem o app, toque em <strong>Atualizar</strong>. Seus livros e capas continuam onde estão.</p></div></li>
    </ol>

    <p class="nota">O app está nas lojas de <strong>{PAISES_IOS[0]}</strong>, {", ".join(PAISES_IOS[1:-1])} e {PAISES_IOS[-1]}. Em outros países ele ainda não aparece.</p>

    <div class="aviso">
      <span class="rotulo">A versão nova do iPhone chega alguns dias depois</span>
      <p>Cada versão do iPhone passa pela análise da Apple antes de entrar na loja. Então a App Store pode ainda estar oferecendo a versão anterior por alguns dias — é normal, e não há nada a fazer além de esperar.</p>
    </div>
  </section>

  <section class="plataforma" id="android">
    <h2>No Android</h2>
    <div class="ficha"><span>Android 7 ou mais novo</span><span>teste fechado da Play Store</span></div>

    <div class="aviso bom solto">
      <span class="rotulo">Sem aceitar o convite, o app não aparece</span>
      <p>A Biblioteca está num <strong>teste fechado da Play Store</strong>. Procurar por “Biblioteca” na loja não encontra nada — ela só existe para quem abriu o link abaixo e aceitou.</p>
      <p>Aceite com a <strong>mesma conta Google que a Play Store do seu celular usa</strong>. Se você tem mais de uma conta no aparelho, essa é a parte que mais dá errado: o convite vale para um endereço só.</p>
    </div>

    <div class="baixar">
      <a href="{PLAY_TESTE}">Aceitar o convite</a>
      <span class="arquivo">play.google.com/apps/testing</span>
    </div>

    <ol class="passos">
      <li><div>
        <p>Abra o link acima e toque em <strong>Tornar-se testador</strong>.</p>
        <p>Se aparecer “App not available”, quase sempre é a conta errada: toque no avatar redondo no canto superior direito e troque para a conta que está no convite.</p>
      </div></li>
      <li><div><p>Na mesma página, depois de aceitar, toque no link que leva à <strong>Play Store</strong>.</p></div></li>
      <li><div><p>Toque em <strong>Instalar</strong>, como em qualquer outro app.</p></div></li>
    </ol>

    <div class="aviso">
      <span class="rotulo">O convite pode demorar a valer</span>
      <p>Depois de aceitar, a Play Store às vezes leva <strong>algumas horas</strong> para mostrar o app. Se não aparecer de imediato, tente de novo mais tarde antes de achar que deu errado.</p>
    </div>

    <h3>Se a Play Store não funcionar para você</h3>
    <p class="nota">O teste fechado exige uma conta Google. Se o seu endereço não for um, ou se o convite simplesmente não abrir, instale o arquivo direto — é a mesma versão.</p>

{baixar("Biblioteca-Android.apk", tam.get("Biblioteca-Android.apk"))}
    <ol class="passos">
      <li><div><p>Baixe o arquivo pelo link acima.</p></div></li>
      <li><div><p>O Chrome avisa que esse tipo de arquivo pode ser perigoso. Toque em <strong>Baixar mesmo assim</strong>.</p></div></li>
      <li><div><p>Toque no arquivo baixado — pela notificação, ou em <strong>Meus Arquivos › Downloads</strong>.</p></div></li>
      <li><div><p>O Android vai dizer que <strong>não pode instalar apps de fontes desconhecidas</strong> e oferecer um botão de Configurações — toque nele e autorize.</p></div></li>
      <li><div><p>Volte e toque em <strong>Instalar</strong>.</p></div></li>
    </ol>

    <div class="aviso">
      <span class="rotulo">Samsung: o Bloqueio automático atrapalha antes disso</span>
      <p>Nos Galaxy mais novos existe um recurso chamado <strong>Bloqueio automático</strong> que impede instalar qualquer app de fora da loja — e ele <strong>não</strong> oferece o atalho de Configurações descrito acima. A instalação simplesmente não vai adiante.</p>
      <p>Para passar: <strong>Configurações › Segurança e privacidade › Bloqueio automático</strong>, e desligue. Depois toque no arquivo baixado outra vez.</p>
    </div>

    <div class="aviso">
      <span class="rotulo">Não desinstale a versão antiga</span>
      <p>Se você já tem a Biblioteca, ela é atualizada por cima e tudo é preservado. Desinstalar primeiro <strong>apaga as capas guardadas no aparelho</strong>.</p>
    </div>
  </section>

  <section class="plataforma" id="mac">
    <h2>No Mac</h2>
    <div class="ficha"><span>macOS 13 Ventura ou mais novo</span><span>{legivel(tam.get("Biblioteca-Mac.dmg")) or "—"}</span><span>reconhecido pela Apple</span></div>

{baixar("Biblioteca-Mac.dmg", tam.get("Biblioteca-Mac.dmg"))}
    <ol class="passos">
      <li><div><p>Baixe o arquivo e dê um duplo clique nele.</p></div></li>
      <li><div><p>Arraste o <strong>Biblioteca Web</strong> para a pasta <strong>Aplicativos</strong>, como de costume.</p></div></li>
      <li><div><p>Se você já tinha a versão anterior, confirme a substituição.</p></div></li>
    </ol>

    <p class="nota">O app é reconhecido pela Apple, então abre direto, sem aviso de segurança. Seu <code>biblioteca.txt</code> e seu <code>biblioteca.dat</code> não são tocados.</p>

    <p class="nota">Esta é a versão <strong>feita para o Mac</strong>, e é por aqui que ela se instala — não pela App Store. O app do <strong>iPhone</strong> já pôde ser instalado em Macs com Apple Silicon; não pode mais. No Mac, a Biblioteca é esta.</p>
  </section>

  <section class="plataforma" id="windows">
    <h2>No Windows</h2>
    <div class="ficha"><span>Windows 10 ou 11</span><span>{legivel(tam.get("Biblioteca-Windows-setup.exe")) or "—"}</span></div>

{baixar("Biblioteca-Windows-setup.exe", tam.get("Biblioteca-Windows-setup.exe"))}
    <ol class="passos">
      <li><div><p>Baixe o arquivo e dê um duplo clique.</p></div></li>
      <li><div><p>Vai aparecer uma <strong>tela azul dizendo “O Windows protegeu o seu PC”</strong>. Clique em <strong>Mais informações</strong> e depois em <strong>Executar assim mesmo</strong>.</p></div></li>
      <li><div><p>Siga o instalador. Ele remove a versão anterior sozinho.</p></div></li>
    </ol>

    <div class="aviso">
      <span class="rotulo">Sobre aquela tela azul</span>
      <p><strong>Não é vírus.</strong> O aviso aparece porque o instalador não tem um certificado digital pago, e o Windows desconfia de todo programa que não tenha um. É o mesmo aviso que apareceria em qualquer programa feito em casa.</p>
    </div>
  </section>

  <section class="plataforma" id="primeira-vez">
    <h2>Na primeira vez que abrir</h2>
    <p class="nota">O app precisa saber onde fica o seu <code>biblioteca.txt</code> — o arquivo onde os seus livros ficam guardados. É a única coisa que ele pergunta, e a resposta é a mesma nos quatro aparelhos.</p>

    <ol class="passos">
      <li><div><p>Clique em <strong>Selecionar pasta</strong>. No <strong>Mac</strong> e no <strong>Windows</strong> ele fica na faixa de cima da tela; no <strong>iPhone</strong> e no <strong>Android</strong>, no menu da tela inicial.</p></div></li>
      <li><div><p>Escolha a pasta onde o seu <code>biblioteca.txt</code> está — ou onde você quer que ele passe a ficar.</p></div></li>
      <li><div><p>Se já houver uma biblioteca na pasta, o app diz <strong>quantos livros achou</strong> lá dentro e pede confirmação antes de usar. Se a pasta estiver vazia, ele <strong>cria o arquivo</strong> e avisa onde.</p></div></li>
    </ol>

    <div class="aviso bom">
      <span class="rotulo">Ele nunca escreve por cima</span>
      <p>Se a pasta tiver um arquivo que o app <strong>não conseguiu ler</strong> — porque ainda está baixando da nuvem, por exemplo — ele não grava nada e oferece escolher outra pasta.</p>
    </div>

    <p class="nota">Se você <strong>já usa</strong> a Biblioteca, nada disso aparece: o app segue na pasta de sempre. O botão fica ali para quando você quiser trocar.</p>
  </section>

  <section class="manuais">
    <h2>Os manuais</h2>
    <p class="nota">Um para cada aparelho.</p>
    <ul class="lista-manuais">
{manuais_html}
    </ul>
  </section>

  <section class="fecho-secao">
    <h2>Se algo der errado</h2>
    <p class="fecho">Me conte <strong>o que aconteceu</strong>, <strong>em que aparelho</strong> e <strong>o que você estava fazendo na hora</strong>. Mesmo “achei estranho isso aqui” ajuda.</p>
    <p class="nota">Todas as versões, com o que mudou em cada uma, estão em <a href="https://github.com/{REPO}/releases">github.com/{REPO}/releases</a>. A política de privacidade está <a href="privacidade.html">aqui</a>.</p>
  </section>

</div>

</body>
</html>
"""


def main():
    v = versao()
    chamada, destaques = notas(v)
    tam = tamanhos(v)
    html = monta(v, chamada, destaques, tam, data_da_versao(v))

    if "--mostrar" in sys.argv[1:]:
        # write, nao print: o print acrescenta uma quebra de linha que o
        # arquivo gravado nao tem, e o portao acusaria diferenca sempre.
        sys.stdout.write(html)
        return

    destino = RAIZ / "docs" / "index.html"
    antes = destino.read_text() if destino.exists() else ""
    destino.write_text(html)
    print(f"docs/index.html  versao {v}, {len(destaques)} destaques, "
          f"{len(manuais())} manuais"
          + ("  (sem mudanca)" if antes == html else ""))
    for nome in ("Biblioteca-Mac.dmg", "Biblioteca-Windows-setup.exe",
                 "Biblioteca-Android.apk"):
        t = tam.get(nome)
        print(f"  {legivel(t) or 'TAMANHO DESCONHECIDO':>8}  {nome}")


if __name__ == "__main__":
    main()
