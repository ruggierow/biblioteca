# Biblioteca 1.9.10

**No Windows, o link "Ler" agora abre o navegador direto, sem passar pelo
sistema.**

## O que acontecia

A 1.9.9 fez o Windows tentar três caminhos para abrir o endereço — o `start` do
`cmd`, o `Start-Process` do PowerShell, o `rundll32` — e nenhum funcionou. O que
se via era pior que silêncio: o pedido saía da máquina virtual, era desviado
para o macOS, e lá terminava abrindo **o VMware Fusion**, que o usuário tinha
instalado em paralelo ao Parallels.

A medição mostrou que não era associação errada em lugar nenhum. No Windows,
`https` estava no Chrome; no Mac, também. E não havia tratador de URL do VMware
nem do Parallels no registro do Windows. O desvio acontecia na integração de
aplicativos entre a máquina virtual e o Mac — camada que não é nossa para
consertar.

## Como ficou

Para `http` e `https`, o programa agora lê no registro **qual navegador o
usuário escolheu** — `UserChoice` → `ProgId` → `shell\open\command`, que vem
como `chrome.exe --single-argument %1` — põe o endereço no lugar do `%1` e
executa o navegador **direto**. A escolha continua sendo dele; quem sai do
caminho é o intermediário.

Os três caminhos antigos ficam como reserva, e, se todos falharem, o programa
continua dizendo o que cada um respondeu em vez de ficar calado.

O `kindle://` **não** passa por aqui: continua indo pelo sistema, que é quem
sabe achar o aplicativo, e no Windows ele já funcionava.

O endereço nunca passa por interpretador de linha de comando: vai como argumento
ao executável.

## Uma ressalva honesta

O teste que aprovou esta versão mudou duas coisas de uma vez: o usuário instalou
a 1.9.10 **e** desinstalou o VMware. O link passou a funcionar, mas qualquer uma
das duas mudanças explica isso sozinha — então a causa não está provada, só o
resultado.

O conserto fica de qualquer modo, por um motivo que não depende do diagnóstico:
executar o navegador escolhido é um caminho mais curto, e não fica à mercê de
quem se intrometer na cadeia de associações depois.

## Nas outras plataformas

Nada muda. Mac, iPhone e Android seguem iguais à 1.9.9, inclusive o título que
vai para a área de transferência quando o Kindle para na biblioteca em vez de
abrir o livro.
