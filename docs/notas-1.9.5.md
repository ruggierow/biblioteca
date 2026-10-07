# Biblioteca 1.9.5

Uma correção só, de leitura: **na tabela, o comentário mostra o rótulo do link
em vez do endereço.**

## O que mudava

A coluna de comentários tem 220px e recorte de duas linhas. Um endereço longo
consome as duas sozinho — com dois links no mesmo comentário, como os livros do
Kindle passaram a ter, aparecia metade do primeiro e mais nada. Na prática,
dava para ver que havia um link, mas não para escolher qual.

## Como ficou

Quando o comentário traz `Rótulo: endereço`, a tabela mostra o **rótulo** como
texto do link e esconde o endereço, que continua acessível ao parar o mouse em
cima. Os livros do Kindle, que têm dois endereços, passam a aparecer assim, numa
linha só:

    Ler | Kindle

O primeiro abre o livro no leitor da Amazon; o segundo abre o aplicativo Kindle.
Sem rótulo, o link aparece com o nome do servidor (`exemplo.com.br`), ou como
"app Kindle" quando é um `kindle://`.

**No detalhe do livro e na impressão nada muda:** lá o texto continua inteiro,
com os endereços à vista.

## Detalhe para quem olha o código

A função nova (`comLinksCompacto`) é usada só pela tabela; o detalhe segue com
`comLinks`. O rótulo é reconhecido olhando para trás a partir do endereço e
**pára em pontuação de frase** — sem isso, um comentário como
*"…pressentimento funesto. Ler o livro: https://…"* virava um rótulo de trinta
letras e deixava um pedaço da palavra solto na tela.
