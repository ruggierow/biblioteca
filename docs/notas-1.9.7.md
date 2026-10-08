# Biblioteca 1.9.7

**Os links do comentário aparecem só pelo rótulo, nas quatro plataformas.**

## O que mudava

Os livros do Kindle têm dois endereços no comentário — um abre o livro no leitor
da Amazon, o outro abre o aplicativo Kindle. Escritos por extenso, eles ocupam
várias linhas.

No Mac e no Windows a tabela já mostrava só o rótulo desde a 1.9.5. No celular
não: o iPhone exibia os dois endereços inteiros, e no **Android a seção aparecia
pela metade** — cada endereço é desenhado como um bloco que não quebra linha, e
a URL longa empurrava o resto da seção para fora da tela. Na prática, no Samsung
não dava para chegar ao link do Kindle.

## Como ficou

Nas quatro, o comentário de um livro do Kindle mostra:

    Ler | Kindle

Cada um é tocável e leva ao seu destino. Quando o comentário traz
`Rótulo: endereço`, o rótulo vira o texto do link e o endereço sai de cena — no
Mac e no Windows ele continua aparecendo ao parar o mouse em cima. Sem rótulo, o
link aparece com o nome do servidor, ou como "app Kindle" quando é um
`kindle://`.

**Na impressão nada muda:** lá o endereço continua por extenso, porque é papel e
não se clica.

## Detalhe para quem olha o código

A regra é a mesma nas três implementações (JavaScript, Dart e Swift) e tem uma
sutileza: o rótulo **para em pontuação de frase**. Sem isso, um comentário como
*"…pressentimento funesto. Ler: https://…"* viraria um rótulo de trinta letras e
deixaria um pedaço de palavra solto na tela. Há teste para esse caso nos três
lados — 25 no Android, 26 no iPhone.
