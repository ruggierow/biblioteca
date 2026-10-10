# Biblioteca 1.9.12

**O aplicativo passa a dizer que está carregando — e para de travar enquanto
grava.**

## O problema, descrito por você

"Como o arquivo `.dat` está ficando grande, o app demora para entrar no início e
fica com a tela inicial aparente, porém ele está bloqueado carregando o arquivo
e não existe nenhuma sinalização indicando este fato."

Exato. E a causa não era a mesma nas quatro plataformas:

| plataforma | o que travava |
|---|---|
| Mac | lia os 39 MB e fazia **três** passagens de escape sobre a string inteira, na linha principal, antes de o JavaScript ainda fazer `JSON.parse` dos mesmos 39 MB |
| Windows | o `JSON.parse` dos 39 MB |
| iPhone | a leitura do `biblioteca.txt` era **síncrona** na criação da tela, e podia esperar o iCloud baixar o arquivo |
| Android | a leitura do mesmo arquivo pela nuvem |

E nos dois celulares havia algo pior que a falta de aviso: a lista dizia
**"Nenhum livro cadastrado"** enquanto carregava — afirmando que a biblioteca
está vazia quando ela apenas ainda não chegou.

## O aviso

No Mac e no Windows, um aviso em tela cheia com o giro de carregamento. Ele vem
dentro do próprio HTML e é visível por padrão: aparece no **primeiro quadro**,
antes de qualquer programa rodar. E como a página é desenhada por outro
processo, ele continua na tela enquanto o lado nativo está ocupado.

O Mac ainda diz **o tamanho do arquivo** antes de começar a ler — ler o tamanho
é instantâneo, e troca uma espera muda por uma espera explicada:

> Carregando as capas dos livros — 39,1 MB. Isto leva alguns segundos.

Há um prazo de 45 segundos para o aviso nunca ficar eterno, e num navegador
comum ele sai sozinho, porque ali não há nada a esperar.

No iPhone e no Android, a lista mostra "Carregando a biblioteca…" enquanto o
arquivo não chega.

## E o travamento em si

Avisar é metade. A outra metade é não travar.

No **iPhone**, a leitura inicial saiu da linha principal. E o backup automático
do `.dat` — que lê o arquivo inteiro, lê o backup anterior, compara os dois e
pode gravar outra cópia — saiu também: ele rodava na linha principal um segundo
depois de abrir, toda vez.

No **Mac** era pior, e isso só apareceu porque fui olhar: lá não havia segundo
plano nenhum. O backup e a gravação dos 39 MB aconteciam na linha principal, um
segundo depois de **cada mudança de capa**.

Nos dois, agora há uma fila dedicada ao `.dat`. Ela é **serial** de propósito:
antes, duas gravações do mesmo arquivo podiam se cruzar. Nunca deu problema,
mas podia.

No Windows não havia o que mover — ali esse trabalho já acontece fora da parte
que desenha a tela.

## Também nesta versão

A captura de ISBN pela câmera, estreada na 1.9.11, foi confirmada funcionando no
Android.
