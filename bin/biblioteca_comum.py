"""Peças comuns aos comandos da Biblioteca. Não é para rodar sozinho.

Reúne o que mais dói errar: o identificador da capa, a leitura da base e a
cópia de segurança antes de qualquer escrita.
"""
import json, re, shutil, datetime, unicodedata
from pathlib import Path

NUVEM = Path.home() / "Library/Mobile Documents/com~apple~CloudDocs/Biblioteca"
BASE = NUVEM / "biblioteca.txt"
FOTOS = NUVEM / "biblioteca.dat"
SEP_AUTORES = ";"


def gerar_id(titulo, autores):
    """Mesmo cálculo do gerarId() em motor-web/biblioteca.html: FNV-1a duplo
    sobre titulo\\x00autor1\\x00autor2..., minúsculo, espaços colapsados e os
    autores ORDENADOS. Qualquer divergência aqui grava a capa num livro que não
    existe — e capa órfã é invisível, ninguém percebe."""
    partes = [re.sub(r"\s+", " ", (titulo or "").lower()).strip()]
    partes += sorted(filter(None, (re.sub(r"\s+", " ", (a or "").lower()).strip() for a in autores)))
    chave = "\x00".join(partes)
    h1, h2 = 2166136261, 2246822519
    for i, ch in enumerate(chave):
        c = ord(ch)
        h1 = ((h1 ^ c) * 16777619) & 0xFFFFFFFF
        h2 = ((h2 ^ (c + i + 1)) * 16777619) & 0xFFFFFFFF
    def b36(n):
        if n == 0: return "0"
        d, s = "0123456789abcdefghijklmnopqrstuvwxyz", ""
        while n:
            n, r = divmod(n, 36); s = d[r] + s
        return s
    return b36(h1) + b36(h2)


class Livro:
    __slots__ = ("n", "campos")
    def __init__(self, n, campos): self.n, self.campos = n, campos
    @property
    def titulo(self): return self.campos[0]
    @property
    def autores(self): return [a.strip() for a in self.campos[1].split(SEP_AUTORES) if a.strip()]
    @property
    def local(self): return self.campos[6] if len(self.campos) > 6 else ""
    @property
    def id(self): return gerar_id(self.titulo, self.autores)


def ler_base(caminho=BASE):
    return [Livro(n, l.split("\t"))
            for n, l in enumerate(caminho.read_text(encoding="utf-8").splitlines(), 1) if l.strip()]


def ler_fotos(caminho=FOTOS):
    return json.loads(caminho.read_text(encoding="utf-8"))


def copia_de_seguranca(arquivo, motivo):
    destino = arquivo.parent / f"{arquivo.stem}_antes-de-{motivo}_{datetime.datetime.now():%Y%m%d_%H%M}{arquivo.suffix}"
    shutil.copy2(arquivo, destino)
    return destino


def gravar_fotos(novas, motivo):
    """Grava capas com TRÊS portões: cópia antes; todo id tem de corresponder a
    um livro que existe agora (se alguém editou título ou autor desde a
    varredura, a chave mudou e a capa entraria órfã); e as capas SUBSTITUÍDAS
    são contadas e devolvidas.

    A contagem de substituídas existe porque em 10/10/2026 gravei a capa de um
    livro que JÁ TINHA capa sem perceber: o total de chaves não mudou e nada na
    saída disse que uma imagem fora trocada. Deu certo por acaso — a capa velha
    era de outra edição —, mas quem grava precisa saber que apagou algo."""
    vivos = {l.id for l in ler_base()}
    orfas = [i for i in novas if i not in vivos]
    if orfas:
        raise SystemExit(f"ABORTADO: {len(orfas)} capa(s) nao casam com livro nenhum: {orfas[:5]}")
    copia = copia_de_seguranca(FOTOS, motivo)
    fotos = ler_fotos()
    antes = len(fotos)
    substituidas = [i for i in novas if i in fotos]
    fotos.update(novas)
    tmp = FOTOS.with_suffix(".dat.novo")
    tmp.write_text(json.dumps(fotos, ensure_ascii=False), encoding="utf-8")
    tmp.replace(FOTOS)
    return copia, antes, len(ler_fotos()), substituidas


def normal(s):
    s = unicodedata.normalize("NFD", (s or "").lower())
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]+", " ", s)).strip()


def censo():
    fotos = ler_fotos()
    livros = ler_base()
    com = sum(1 for l in livros if l.id in fotos)
    return len(livros), com, len(livros) - com
