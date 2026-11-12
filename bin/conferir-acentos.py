#!/usr/bin/env python3
"""Portao do portugues da tela: acento que falta e acento que varia.

    ./bin/conferir-acentos.py

Em 12/11/2026 o dicionario em portugues do `motor-web/biblioteca.html` tinha
**66 linhas sem acento** — do cabecalho ("Sistema de Gestao de Biblioteca") ao
selo da tabela ("Disponivel") e ao botao da paginacao ("Proxima"). Nasceram
assim e foram envelhecendo ao lado de linhas novas, escritas com acento. O
mesmo texto chegava a existir das duas formas: a faixa do arquivo dizia
"alterações salvas automaticamente" num caminho e "alteracoes salvas
automaticamente" noutro, conforme o arquivo tivesse data e tamanho.

Nenhum teste reprovava, e nao e por descuido da suite: ela afirma o que a tela
FAZ, e a tela fazia certo. Isto aqui olha como ela ESCREVE.

SAO QUATRO REDES, e cada uma pega o que as outras deixam passar:

  1. **inconsistencia** — a mesma palavra escrita das duas formas no mesmo
     dicionario. Nao precisa de lista: a propria pagina e a referencia. Foi
     esta que achou 59 linhas;
  2. **ausencia uniforme** — palavra que o dicionario inteiro escreve sem
     acento, e para a qual a rede 1 e cega por nao haver com que comparar.
     Precisa de lista, e a lista cresce quando aparece uma nova. Foi esta que
     achou "so", "memoria", "relatorio", "conteudo", "Disponivel", "Proxima",
     "valido" e "orfa" DEPOIS de a rede 1 dizer que estava tudo bem.

  3. **terminacao** — palavra terminada em `-cao`, `-sao`, `-coes`, `-vel`,
     `-veis`, `-encia`, `-ancia`, `-ario`, `-orio` ou `-icio` SEMPRE leva
     acento em portugues. Esta nao precisa de
     lista nem de comparacao, e por isso e a unica que pega uma palavra NOVA.
     Foi ela que pegou "sessao" numa mutacao em que as outras duas calaram.

  4. **o padrao x o dicionario** — todo texto do HTML marcado com `data-i18n`
     tem um gemeo no dicionario, e os dois TEM DE SER IGUAIS. Esta nao fala de
     acento: pega qualquer divergencia entre o que esta escrito no corpo da
     pagina e o que a traducao poe por cima. Foi ela que achou que o rotulo do
     formulario dizia "Comentarios (opcional)" no HTML e "Comentários
     (opcional)" no dicionario — a mesma frase, duas grafias, no mesmo
     arquivo.

A excecao e `esta`, que em portugues existe mesmo das duas formas ("esta
pasta" e "o arquivo está"). Toda outra palavra da rede 1 e defeito.
"""
import html.parser
import re
import sys
import unicodedata
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PAGINA = RAIZ / "motor-web" / "biblioteca.html"

# Palavras que em portugues existem COM e SEM acento, as duas corretas.
# Cada entrada aqui e uma renuncia: a rede 1 deixa de olhar essa palavra.
HOMOGRAFAS = {"esta"}          # "esta pasta" x "o arquivo está"

# Grafias que estao SEMPRE erradas em portugues. A rede 2 vive desta lista.
SEMPRE_ERRADAS = """
nao sao voce voces entao tambem alem apos atraves ate ja la so tres
pais paises titulo titulos codigo codigos numero numeros pagina paginas area
memoria historia familia obrigatorio relatorio relatorios conteudo
minimo maximo periodo nivel niveis dificil facil util uteis unico unica
proprio propria ultimo ultima proximo proxima otimo automatico automatica
versao versoes opcao opcoes informacao informacoes selecao secao secoes
edicao edicoes exclusao importacao exportacao recuperacao emergencia
permissao permissoes vinculacao alteracao alteracoes atencao seguranca
referencia referencias experiencia disponivel indisponivel possivel
impossivel responsavel invalido valido incluido concluido construido
atribuido substituida identico orfa orfas estao serao sera ficara ha
""".split()

# Terminacoes que em portugues SEMPRE levam acento, em algum lugar da palavra.
# Sem lista e sem comparacao: e o que faz a rede 3 pegar palavra que ninguem
# previu. A palavra so interessa se NAO tiver acento nenhum — "possível"
# termina em "vel" e esta certa; "possivel" e que nao.
TERMINACOES = re.compile(
    r"(?:[cs]ao|[cs]oes|vel|veis|encia|ancia|ario|arios|orio|orios|icio|icios)$",
    re.I)
# `-aria` fica DE FORA de proposito: em portugues tambem e desinencia de verbo
# ("faria", "diria"), e um portao que acusa verbo correto some do uso.

# Quando uma palavra estrangeira cair numa dessas terminacoes, ela entra aqui —
# com o motivo. Vazio ate hoje.
APESAR_DA_TERMINACAO = set()

falhas = []


def reprova(m):
    falhas.append(m)
    print(f"   FALHOU: {m}")


def passa(m):
    print(f"   ok: {m}")


def sem_acento(p):
    return "".join(c for c in unicodedata.normalize("NFD", p)
                   if not unicodedata.combining(c))


def dicionario(texto, idioma):
    """As linhas `chave: "valor"` de um dos dicionarios da pagina.

    Delimitado por `<idioma>: {` e pelo proximo `<xx>: {`. Ancorar em numero
    de linha seria um portao que envelhece junto com o arquivo que vigia.
    """
    ini = re.search(r"^\s*" + idioma + r":\s*\{", texto, re.M)
    if not ini:
        return None
    resto = texto[ini.end():]
    fim = re.search(r"^\s*[a-z]{2}:\s*\{", resto, re.M)
    corpo = resto[:fim.start()] if fim else resto
    return re.findall(r'^\s*(\w+):\s*"(.*)",?\s*$', corpo, re.M)


def rede_da_inconsistencia(rotulos):
    """A mesma palavra escrita das duas formas — a pagina como referencia."""
    formas = {}
    for _, valor in rotulos:
        for p in re.findall(r"[A-Za-zÀ-ÿ]{2,}", valor):
            formas.setdefault(sem_acento(p.lower()), set()).add(p.lower())
    duplas = {nu: fs for nu, fs in formas.items()
              if len(fs) > 1 and nu not in HOMOGRAFAS}
    if not duplas:
        passa(f"nenhuma palavra escrita das duas formas ({len(rotulos)} rotulos)")
        return
    for nu, fs in sorted(duplas.items()):
        onde = [c for c, v in rotulos
                if re.search(r"\b" + nu + r"\b", v, re.I)][:4]
        reprova(f"{' x '.join(sorted(fs))} — as duas no mesmo dicionario, em "
                f"{', '.join(onde)}")


def rede_da_ausencia(rotulos):
    """Grafia que esta sempre errada, mesmo que o dicionario inteiro a use."""
    achados = {}
    for chave, valor in rotulos:
        for p in SEMPRE_ERRADAS:
            if re.search(r"\b" + p + r"\b", valor, re.I):
                achados.setdefault(p, []).append(chave)
    if not achados:
        passa(f"nenhuma das {len(SEMPRE_ERRADAS)} grafias sem acento da lista")
        return
    for p, chaves in sorted(achados.items()):
        reprova(f"{p!r} sem acento em {len(chaves)}: {', '.join(chaves[:4])}")


def rede_da_terminacao(rotulos):
    """-cao, -sao, -vel, -encia: terminacao que nao existe sem acento."""
    achados = {}
    for chave, valor in rotulos:
        # fora do que nao e prosa: ${0}, <tags>, &entidades;, codigo
        prosa = re.sub(r"\$\{\d+\}|<[^>]+>|&[a-z]+;", " ", valor)
        for m in re.finditer(r"\b[A-Za-zÀ-ÿ]{4,}\b", prosa):
            p = m.group(0)
            if sem_acento(p) != p:          # ja tem acento: nao e com ela
                continue
            if TERMINACOES.search(p) and p.lower() not in APESAR_DA_TERMINACAO:
                achados.setdefault(p.lower(), []).append(chave)
    if not achados:
        passa("nenhuma terminacao -cao/-sao/-vel/-encia sem acento")
        return
    for p, chaves in sorted(achados.items()):
        reprova(f"{p!r} termina em algo que em portugues sempre leva acento, "
                f"em {len(chaves)}: {', '.join(chaves[:4])}")


class ColhePadroes(html.parser.HTMLParser):
    """O texto que cada elemento `data-i18n` traz escrito no corpo da pagina.

    Com um analisador de verdade, e nao com expressao regular: estes rotulos
    tem `<code>` e `<b>` dentro, e varios atravessam mais de uma linha.
    """

    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.achados = {}          # chave -> texto
        self.pilha = []

    def handle_starttag(self, tag, atributos):
        d = dict(atributos)
        chave = d.get("data-i18n") or d.get("data-i18n-html")
        if tag in ("input", "img", "br", "hr", "meta"):
            return
        self.pilha.append([chave, []])

    def handle_data(self, dados):
        for quadro in self.pilha:
            quadro[1].append(dados)

    def handle_entityref(self, nome):
        for quadro in self.pilha:
            quadro[1].append(f"&{nome};")

    def handle_charref(self, nome):
        # `&#128438;` e referencia NUMERICA, e nao passa por handle_entityref.
        # Sem isto o icone some do lado do HTML e o portao acusa divergencia
        # onde nao ha — falso positivo medido em 12/11/2026.
        for quadro in self.pilha:
            quadro[1].append(f"&#{nome};")

    def handle_endtag(self, tag):
        if not self.pilha:
            return
        chave, pedacos = self.pilha.pop()
        if chave and chave not in self.achados:
            self.achados[chave] = "".join(pedacos)


def rede_do_padrao(texto, rotulos):
    """O texto escrito no corpo da pagina x o do dicionario."""
    dicio = dict(rotulos)
    colhe = ColhePadroes()
    colhe.feed(texto)
    conferidos = divergentes = 0
    for chave, padrao in colhe.achados.items():
        if chave not in dicio:
            continue
        # o dicionario guarda o HTML interno; aqui comparamos so o texto visivel
        limpa = lambda s: re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", s)).strip()
        conferidos += 1
        if limpa(padrao) != limpa(dicio[chave]):
            divergentes += 1
            reprova(f"{chave}: o HTML diz {limpa(padrao)[:40]!r} e o dicionario "
                    f"diz {limpa(dicio[chave])[:40]!r}")
    if not divergentes:
        passa(f"os {conferidos} textos padrao do HTML batem com o dicionario")


def main():
    print("--- o portugues da tela ---")
    texto = PAGINA.read_text()
    rotulos = dicionario(texto, "pt")
    if not rotulos:
        reprova("nao achei o dicionario `pt:` em motor-web/biblioteca.html")
    else:
        rede_da_inconsistencia(rotulos)
        rede_da_ausencia(rotulos)
        rede_da_terminacao(rotulos)
        rede_do_padrao(texto, rotulos)

    print()
    if falhas:
        print(f"REPROVADO: {len(falhas)} problema(s) no portugues da tela.")
        return 1
    print("O portugues da tela esta acentuado.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
