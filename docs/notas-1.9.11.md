# Biblioteca 1.9.11

**A leitura do código de barras agora guarda o ISBN.**

## O que mudou

A câmera já lia o ISBN da contracapa e preenchia título, autores, temas e ano.
Mas descartava o número depois de usá-lo — e ele é o dado mais útil de todos: é
a única chave **exata** para achar capa e informação do livro mais tarde. Busca
por título erra; busca por ISBN, não.

Agora ele fica, no campo de comentários:

    Editora: Companhia das Letras | ISBN: 9788535902778

Reler o mesmo livro não duplica a marca. Reler com outro número substitui — a
leitura mais recente vence. E o número é guardado **mesmo quando a busca não
encontra o livro**: ali ele vale ainda mais, porque é tudo o que se tem.

Vale nas quatro plataformas: iPhone, Android, Mac e Windows.

## Por que no comentário, e não numa coluna nova

O lugar certo para o ISBN é uma nona coluna no arquivo. Ele não está lá por um
motivo medido:

| plataforma | linha com 9 campos |
|---|---|
| Mac e Windows | **descarta o livro inteiro** |
| Android | lê os 8 primeiros, ignora o 9º |
| iPhone | idem |

O Mac salva sozinho. Gravar uma nona coluna hoje faria os livros sumirem da
lista e, no primeiro salvamento, do arquivo. E as duas plataformas que leem sem
reclamar gravam de volta só 8 colunas, apagando o ISBN em silêncio.

A coluna continua sendo o destino. Chegar lá exige duas versões: uma que apenas
aprende a preservar o campo, instalada nas quatro máquinas, e só depois outra
que escreve. Enquanto isso o comentário faz o serviço, no mesmo padrão
`Rótulo: valor` que já se usa ali para `Editora:`, `Ler:` e `Kindle:`.

## Para que serve, na prática

Dos 750 livros, **204 seguem sem capa**, e as fontes gratuitas já foram
esgotadas por título e autor — duas varreduras. Com o ISBN em mãos, a busca
passa a ser exata, e abrem-se bases que só respondem a ISBN.

O caminho é a estante: ler o código de barras livro a livro. Vale lembrar que
**48 desses 204 são anteriores a 2000**, e livro antigo muitas vezes não tem
código de barras — esses continuam sendo caso de fotografar a capa.
