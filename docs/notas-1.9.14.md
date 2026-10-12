# Biblioteca 1.9.14

**A fundação do mapa por país. Nada muda na tela — e isso é de propósito.**

## O que esta versão faz

O arquivo da biblioteca tem oito colunas. O mapa precisa de uma nona, com o
país de cada livro. Esta versão ensina as **quatro** plataformas a ler, guardar
e devolver essa coluna — sem ainda mostrar nada, sem ainda preencher nada.

## Por que em duas etapas, e não de uma vez

Porque fazer de uma vez destruiria a sua biblioteca.

Até a 1.9.13, o Mac e o Windows **descartavam em silêncio** qualquer linha com
nove colunas. E como o Mac grava sozinho, bastaria um arquivo com a coluna nova
para a biblioteca abrir **vazia** — e o vazio ser gravado por cima do seu
acervo. Sem erro na tela, sem aviso.

Então: primeiro todos aprendem a preservar; depois, e só depois, o dado entra.
É por isso que esta versão precisa estar instalada **nas quatro máquinas** antes
da próxima. Um aparelho que ficar para trás apaga o dado dos outros.

## O que foi decidido

- **Um país por livro**, não três eixos. O mapa fica legível e o filtro sem
  ambiguidade; os critérios (literatura, autor, editora) viram maneiras de
  decidir qual é o país.
- **Mapa no Mac e no Windows**; nos celulares, uma tabela por país. Mapa
  clicável com 22 países num polegar não funciona.
- A coluna guarda o código de duas letras (`BR`, `JP`), não o nome — acento e
  grafia divergem entre plataformas. Na tela você continuará vendo "Brasil".

## De onde virá o país

Duas fontes, nenhuma delas pedindo trabalho seu:

- **O tema.** "Literatura Brasileira" diz Brasil. Hoje isso cobre **257 dos 750
  livros**, em 22 países.
- **O ISBN**, que a câmera já guarda desde a 1.9.11. O começo do número é o país
  do editor: `978-85` é Brasil, `978-2` França, `978-4` Japão. Ou seja, a
  varredura da estante que você vai fazer pelas capas traz o país junto.

## O cuidado que quase passou

Preservar ao abrir e ao salvar não basta. Se **editar** um livro reconstruísse o
registro, o país sumiria no primeiro conserto de título.

O Mac, o Windows e o iPhone já alteravam o livro campo a campo, e estavam
salvos. O Android reconstruía o registro inteiro: ali, qualquer edição teria
apagado o país em silêncio. Corrigido, e com teste nas três.
