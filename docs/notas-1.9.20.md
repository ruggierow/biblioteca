# Biblioteca 1.9.20

**Seis rótulos teimavam em português** com o app em inglês, e o Android não
sabia criar o seu arquivo. Esta versão conserta as duas coisas — e os manuais
passam a ensinar o que faltava.

## Os rótulos que ficavam em português

A 1.9.19 trouxe o inglês, mas seis textos escaparam. Eles não estavam no
dicionário: estavam escritos à mão no meio da tela, e por isso nenhum teste de
tradução os via.

- No **iPhone** e no **Android**, na ficha do livro e no cadastro: *Autor(es)*
  e *Tema(s)*, que agora dizem **Author(s)** e **Subject(s)**.
- No **Android**, na ficha: *Comentários*, que agora diz **Notes**.
- No **Mac** e no **Windows**, na janela de edição: os botões *Salvar* e
  *Cancelar*, que agora dizem **Save** e **Cancel**.

Em português nada mudou — nem uma palavra. O que havia era a falta do inglês.

## O Android agora cria o seu biblioteca.txt

Quem instalava o app no Android e ainda não tinha um `biblioteca.txt` ficava
sem saída: era preciso escolher uma pasta, e se a pasta não tivesse o arquivo,
o app avisava que não o encontrou e mandava *"escolher a pasta onde o arquivo
está"*. Sem o arquivo, o **Cadastro** nem abria. Não havia como começar do
zero pelo celular.

Agora, quando a pasta escolhida não tem um `biblioteca.txt`, a tela de
**Sincronização** oferece **Criar biblioteca.txt nesta pasta**. Um toque, e o
arquivo passa a existir.

O app não cria nada sem você pedir: a linha só aparece nesse caso, e a
decisão é sua.

## Os manuais, nas quatro plataformas e em dois idiomas

O Mac, o Windows, o iPhone e o Android têm agora manual próprio, cada um em
**português e em inglês**, para ler na tela ou em PDF, com telas reais do app.

Todos ganharam um capítulo que faltava: **de onde vem o seu arquivo na
primeira vez**. É uma resposta diferente em cada aparelho — o Mac pergunta
numa janela de boas-vindas, o Windows cria sozinho, o iPhone cria ao receber o
primeiro livro, e o Android agora tem o botão acima. Nenhum manual contava
isso.

O capítulo também explica o `biblioteca.dat`, o arquivo das capas: ele **não
nasce** junto do `biblioteca.txt`, e só aparece quando há capas para guardar.

Os manuais estão na página do app, ao lado dos instaladores.

## Instalação

Nada muda. O instalador do Windows substitui a versão anterior, e no Mac basta
arrastar para a pasta Aplicativos. Seu `biblioteca.txt` e seu `biblioteca.dat`
não são tocados.

No Android, **não desinstale a versão antiga**: ela é atualizada por cima e as
capas guardadas no aparelho são preservadas.

O **iPhone** sai pela App Store e depende da análise da Apple, então chega
alguns dias depois — com o mesmo número de versão.
