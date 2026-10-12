# Biblioteca 1.9.13

**No Mac, o botão Remover volta a perguntar — e a funcionar.**

## O que acontecia

Clicar em **Remover** na lista de resultados não fazia nada no Mac. Nenhuma
pergunta, nenhuma remoção, nenhum erro.

A causa não era a remoção. Era o **diálogo**: o WKWebView, que é a janela onde a
página roda dentro do aplicativo, não tem diálogo nenhum por conta própria.
Quando o programa pergunta "Remover o livro X?", a resposta voltava **"não"**
imediatamente, sem nunca aparecer na tela. O programa obedecia a uma recusa que
você nunca deu.

Não foi uma regressão. Esse diálogo **nunca** existiu no aplicativo do Mac — o
Remover que você viu funcionando foi no Windows ou no navegador, onde o
diálogo é do próprio sistema. E não era só ele: eram **13 perguntas e 5 avisos**
mudos, espalhados pelo programa.

É a quarta vez que a mesma causa aparece aqui. Antes dela, pelos mesmos
motivos, os links dos comentários não abriam, e os dois botões de imprimir não
faziam nada.

## Como ficou

O aplicativo do Mac agora desenha os três diálogos que a página pede —
pergunta, aviso e caixa de texto. O Remover pergunta, você responde, e ele
obedece à **sua** resposta.

## O que mudou por baixo, e que importa mais

Um defeito desses não deveria chegar até você. Esta versão traz duas redes que
não existiam:

**Testes da página.** Catorze casos que exercitam listar, filtrar, cadastrar,
recusar duplicata, emprestar, devolver, editar e remover — mais uma varredura
que aciona todo botão e exige que cada um faça alguma coisa. A página que o Mac
e o Windows usam tinha 4 859 linhas e **nenhum** teste.

**Conferência do contrato.** Essa é a que teria pego o Remover. Um teste comum,
rodando num navegador, passaria com louvor — porque no navegador a pergunta
funciona. A conferência nova compara o que a página pede com o que cada
aplicativo oferece, e acusa quando falta alguém do outro lado. Ela já achou um
segundo problema no primeiro uso.

Rodar tudo é um comando, e ele roda antes de cada versão daqui para frente.

## Também nesta versão

O aviso de carregamento, estreado na 1.9.12, aparecia um pouco mais tarde do que
devia no Mac. Agora aparece desde o primeiro instante.
