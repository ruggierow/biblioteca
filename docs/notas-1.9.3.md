# Biblioteca 1.9.3

## O link dos comentários agora leva ao endereço escrito

A 1.9.2 fazia uma conversão silenciosa: quando o endereço nos comentários
carregava um **ASIN** — o identificador que a Amazon dá a cada livro — o toque
não ia para o endereço escrito, e sim para um `kindle://` montado a partir
dele, na expectativa de abrir o livro direto na leitura.

Não abre. O aplicativo Kindle 7.x pára na sua biblioteca, qualquer que seja a
forma do `kindle://` — foi testado no iPhone e no Android com as duas grafias
(`kindle://book?action=open&asin=…` e `kindle://book/?action=open&book_id=…`).
A conversão existia desde setembro no iPhone, nunca tinha sido verificada, e
a 1.9.2 a espalhou para as outras três plataformas.

Nesta versão a conversão saiu do Mac, do Windows, do iPhone e do Android. O
link faz o que o endereço diz: o endereço da Amazon abre a **página do livro**
na loja, e de lá o próprio botão da Amazon leva à leitura. Um `kindle://`
escrito à mão nos comentários continua sendo entregue ao aplicativo Kindle,
sem reescrita.

## O que muda para você

Nada no cadastro. Os 123 livros do Kindle continuam com o endereço da Amazon
nos comentários, o ASIN continua visível e localizável pela busca, e o link
continua sublinhado e clicável nas quatro plataformas. Só o destino mudou — e
mudou para um que funciona.

## Detalhe para quem olha o código

O reconhecimento do endereço e o escape do texto comum ficaram como estavam:
`comLinks()` no motor-web, `ComentariosComLinksView` no iOS e `reEndereco` no
Android. O que saiu foram as três funções de conversão (`asinDoEndereco` e
companhia) — o destino do link passou a ser o endereço encontrado, com a única
normalização de prefixar `https://` num `www.` solto.
