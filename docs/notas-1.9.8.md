# Biblioteca 1.9.8

Dois consertos no Android, achados com o aparelho do usuário na mão.

## A seção de comentários ficava fora de alcance

No Galaxy A57 os links do comentário apareciam, mas numa faixa da tela que não
aceita toque — e a tela **não rolava**. Era possível ver o link e impossível
usá-lo.

A causa: desde o Android 15 o sistema impõe o modo **borda a borda** para
aplicativos que miram o SDK 35 ou maior. O programa passa a desenhar por baixo
da barra de navegação e cabe a ele reservar esse espaço. As telas de **detalhe,
cadastro e sincronização** não reservavam, então a última seção ficava sob a
barra — e a lista nem rolava, porque para ela o conteúdo cabia na tela.

Agora as três reservam. Medido no próprio aparelho, antes e depois.

## Sobrava um pedaço do rótulo

Na mesma tela aparecia `Le Ler | Ki Kindle`: o corte do rótulo usava o tamanho
dele em vez do ponto onde ele começa, e comia o fim deixando o começo. Agora sai
`Ler | Kindle`, como nas outras plataformas.

## O que se descobriu testando

Aproveitando o aparelho conectado, mediu-se o que o link do Kindle faz em cada
plataforma — e a resposta não é a mesma:

| plataforma | o rótulo **Kindle** |
|---|---|
| Android | abre **o livro** |
| iPhone | abre a biblioteca |
| Mac | abre a biblioteca |

Isso corrige o que se registrou em 6 de outubro, quando se concluiu que o
endereço `kindle://` nunca abria o livro. Era verdade no Mac — o aplicativo de
lá não tem rota nenhuma — e é falso no Android.

Onde ele só abre a biblioteca, vale o que a 1.9.6 trouxe: o título do livro vai
para a área de transferência no toque, e basta colar na busca do Kindle.

## Detalhe para quem olha o código

O teste de widget que deveria ter pego o rótulo cortado comparava com
`contains('Ler')` — e `"Le Ler"` contém `"Ler"`. Agora ele compara os rótulos e
o parágrafo externo por inteiro. São 28 testes no Android.
