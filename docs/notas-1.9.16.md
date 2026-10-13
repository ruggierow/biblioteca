# Biblioteca 1.9.16

**Agora dá para pôr o país do livro — e para corrigi-lo.**

## O campo de país no formulário

Até aqui o aplicativo sabia **ler** o país (1.9.14) e **desenhar** o mapa
(1.9.15), mas não sabia **escrevê-lo**. Os 280 países da base vieram todos de
um programa auxiliar, rodado por fora. Não havia como pôr país num livro nem,
pior, como corrigir um país errado.

Agora há um campo **País** em Cadastrar e em Editar, nas quatro plataformas,
ao lado de "Local do exemplar". No Mac e no Windows a lista vem agrupada por
continente; no iPhone e no Android, em ordem alfabética.

Três coisas que ele faz de propósito:

- a opção **— sem país —** vem primeiro e continua disponível. Livro sem país é
  o estado normal (470 dos 750), e é assim que se desfaz um país posto por
  engano;
- abrir a edição já mostra o país do livro. Salvar sem mexer não troca nada;
- um código de país que não esteja na lista aparece assim mesmo, marcado. O
  aplicativo nunca descarta calado um dado que você gravou.

## Por que isto precisava ser a mão

O programa que semeou os 280 países **não tem mais o que oferecer**: rodado
hoje, propõe zero. Ele trabalha com duas pistas — o gentílico do tema
("Literatura Japonesa" diz Japão) e o início do ISBN — e os 470 livros
restantes não têm nenhuma das duas. São a biblioteca técnica, sem gentílico no
tema, e nenhum deles tem ISBN gravado. Não há de onde adivinhar.

Vale dizer: para um livro de arquitetura de computadores, "país" é discutível —
do autor? da editora? Pode ser que esses 470 devam mesmo ficar sem país, e que
só valha a pena preencher os que te interessam.

## 22 nomes de país estavam sem acento no Mac e no Windows

Apareceu ao montar a lista: o Mac mostrava **Mocambique**, **Africa do Sul** e
**Ira** onde o iPhone e o Samsung mostravam **Moçambique**, **África do Sul** e
**Irã**. Ninguém tinha notado porque o código interno do país — que é o que o
arquivo guarda e o que o mapa usa — estava certo nos quatro. Agora a grafia é a
mesma em todos, e há conferência automática para que não volte a divergir.

No Android a lista também ordenava pelo código interno da letra, e não pela
letra: "Áustria" e "Índia" iam parar no fim da lista. Corrigido.

## A faixa do alto diz a DATA do arquivo (Windows)

Em 13/10 o mapa "não funcionou no Windows": zero livros com país. Não era
defeito do programa — o iCloud para Windows tinha parado de sincronizar, e o
arquivo daquela pasta era de seis dias antes.

A faixa já mostrava o **caminho** do arquivo, e caminho não conta idade. Agora
mostra também a data de gravação e, quando o arquivo tem três dias ou mais, há
quantos dias ele é. E se a pasta configurada não puder ser lida, um aviso em
amarelo diz que o programa caiu na busca automática — em vez de mostrar uma
biblioteca antiga sem avisar.
