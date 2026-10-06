# Biblioteca 1.9.2

## Endereços nos comentários viram links

Um endereço escrito no campo de comentários era texto morto no Mac e no
Windows, e no Android só funcionava se começasse com `http`. Agora as quatro
plataformas se comportam igual: o endereço aparece sublinhado e o toque abre.

E há uma conversão por trás disso. Quando o endereço carrega um **ASIN** — o
identificador que a Amazon dá a cada livro, reconhecido tanto num link de loja
(`/dp/`, `/gp/`, `/product/`) quanto num `kindle://` — o link passa a apontar
para o **aplicativo Kindle**, embora continue mostrando o endereço original.

Na prática: um livro do Kindle cadastrado com o endereço da Amazon nos
comentários abre direto na leitura, sem passar pelo navegador.

O iPhone já fazia isso desde setembro. Esta versão leva o mesmo comportamento
para as outras três.

## O que isso tem a ver com a sua biblioteca

Se você cadastrar livros do Kindle, basta pôr o endereço da Amazon nos
comentários — nada mais. O identificador fica guardado dentro dele, visível e
localizável pela busca, sem precisar de campo novo.

## Detalhe para quem olha o código

No Mac e no Windows o texto dos comentários continua sendo escapado antes de
ir para a tela — a proteção contra conteúdo malicioso não foi afrouxada para
criar os links. O texto comum é escapado pedaço por pedaço e só os trechos
reconhecidos como endereço viram link.

No Android foi preciso declarar o esquema `kindle` no manifesto: desde o
Android 11 um aplicativo só "enxerga" outro se o declarar, e sem isso o toque
no link simplesmente não fazia nada — sem erro, sem aviso.
