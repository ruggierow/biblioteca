# Biblioteca 1.9.21

**A primeira vez agora é igual nos quatro aparelhos.** Em todos existe um
botão **Selecionar pasta**, e em todos ele responde do mesmo jeito: se a pasta
já tem uma biblioteca, o app diz quantos livros achou e pergunta antes de
usar; se está vazia, cria o arquivo; se há um arquivo que ele não conseguiu
ler, não escreve nada e oferece outra pasta. No Mac, de quebra, a pasta deixa
de ser cravada no iCloud.

## O mesmo Selecionar pasta nos quatro aparelhos

Até agora cada aparelho resolvia a primeira vez à sua maneira — e duas delas
não resolviam. O Windows criava o arquivo em silêncio, numa pasta que você não
escolheu. O Mac abria uma janela de boas-vindas cuja opção recomendada **não
fazia nada**.

Agora é um fluxo só, com as mesmas quatro respostas em todos:

- **A pasta já tem um `biblioteca.txt`** — o app diz **quantos livros achou**
  lá dentro e pergunta se é essa que você quer. A contagem está ali de
  propósito: "quer usar este arquivo?" sem dizer o que há dentro é pedir um
  palpite.
- **A pasta está vazia** — ele cria o `biblioteca.txt` e avisa onde.
- **Há um arquivo e ele não conseguiu ler** — diz o que houve e oferece
  escolher outra pasta. **Nunca escreve por cima**: pode ser a biblioteca de
  alguém, ou um arquivo ainda baixando da nuvem.
- **A pasta está vazia e você já tem livros abertos** — aí ele pergunta, e é a
  única pergunta com algo a perder: levar os livros para a pasta nova, ou
  começar vazia.

Fechar a pergunta sem responder não vale por "não": nada é escrito.

## No Mac, a pasta deixa de ser cravada no iCloud

Até a 1.9.20 o app do Mac só olhava uma pasta, dentro do iCloud Drive. Quem
guarda os livros em outro lugar — no Dropbox, num disco externo, na própria
Mesa — simplesmente não tinha aplicativo.

Agora a pasta é sua escolha, e ela é lembrada. Se a pasta escolhida
desaparecer, o app volta sozinho para a do iCloud em vez de ficar sem rumo.

A janela de boas-vindas saiu. Ela oferecia duas opções: a recomendada chamava
um recurso que o app do Mac não tem, e não fazia nada; a outra dizia que os
dados ficariam "apenas no navegador", o que nunca foi verdade dentro do
aplicativo. Quem abre a Biblioteca pelo navegador continua vendo essa janela,
onde ela faz sentido.

## Dois textos em inglês que estavam errados

O botão da pasta dizia *Select folder* no Android e *Choose folder* nas outras
três — justamente a diferença que esta versão existe para acabar. Agora é
**Choose folder** em todas.

E a frase de ajuda embaixo da faixa falava de "vincular" um arquivo e de
"navegadores sem suporte", dentro do aplicativo instalado, onde não existe nem
um nem outro. Agora ela diz o que o app faz de fato.

## Instalação

Nada muda. O instalador do Windows substitui a versão anterior, e no Mac basta
arrastar para a pasta Aplicativos. Seu `biblioteca.txt` e seu `biblioteca.dat`
não são tocados.

No Mac, se você já usava o app, **nada é perguntado**: ele continua na pasta
do iCloud que já usava. O botão está lá para quando você quiser mudar.

No Android, **não desinstale a versão antiga**: ela é atualizada por cima e as
capas guardadas no aparelho são preservadas.

O **iPhone** sai pela App Store e depende da análise da Apple, então chega
alguns dias depois — com o mesmo número de versão.
