# Biblioteca 1.9.4

Esta versão é de conserto. Sete defeitos, e os sete tinham a mesma assinatura:
**o botão estava lá, você clicava, e não acontecia nada — sem erro, sem aviso.**
É o tipo de falha que sobrevive a releases inteiras, porque não aparece em
nenhum teste e quem usa supõe que entendeu errado.

## O que voltou a funcionar

**O link nos comentários, no Mac e no Windows.** Um endereço escrito ali era
sublinhado, parecia clicável e não levava a lugar nenhum nas duas versões de
mesa — só o iPhone e o Android abriam. Agora o endereço é entregue ao sistema:
o navegador abre a página da Amazon, o aplicativo Kindle abre quando o endereço
é um `kindle://`.

**Imprimir.** Os dois botões — o da linha do livro e o "Imprimir resultados" —
não faziam nada no Mac. Agora abrem o diálogo de impressão com a prévia.

**Exportar Excel.** Pior que não funcionar: ele anunciava *"Planilha salva em
~/Downloads"* **sem gravar arquivo nenhum**. Agora o Mac pergunta onde salvar e
só avisa depois de escrever; se você cancelar, ele fica calado.

**A seção "Editar livro".** O seletor "Livro a editar" era preenchido com todos
os livros, mas o botão **Editar selecionado** não tinha nenhum efeito, e o campo
"Filtrar lista" também não. Dava para editar só pela tabela. Agora o filtro
reduz a lista a cada tecla, e o botão (ou o Enter no campo) abre a edição.

**Os filtros "Grupo de literatura" e "Com foto".** Os campos de texto filtravam
ao digitar e o Status ao mudar, mas estes dois só entravam se você clicasse em
Pesquisar — marcar a caixa e olhar a lista dava a impressão de que não faziam
nada. Agora reagem na hora, como os demais.

**Apagar uma capa.** A exclusão não se propagava: a capa voltava na leitura
seguinte do `biblioteca.dat`, porque mesclagem só sabe somar. Agora a exclusão
é registrada e respeitada — e o caminho inverso também existe: ao repor a capa
de um livro, ela volta a viajar entre os aparelhos.

## Por que tantos de uma vez

Porque a causa é comum. No aplicativo do Mac a página roda dentro de um
`WKWebView`, e ali **o que passa pela ponte nativa funciona; o que depende do
navegador falha em silêncio**. `window.open` devolve nulo, `window.print()` não
existe, e download por `blob:` não escreve nada — nenhum dos três reclama. O
Backup e o Exportar sempre funcionaram justamente por irem pela ponte.

Os outros dois — a seção de edição e os dois filtros — eram controles que
ficaram sem ninguém escutando, provavelmente perdidos numa edição antiga. Foram
achados por um levantamento de todos os 76 controles da interface, clicando um
a um e medindo se a página reagia.

## Detalhe para quem olha o código

A impressão agora monta o HTML e o entrega ao `NSPrintOperation` no Mac; no
Windows e no navegador, a um iframe escondido — que de quebra escapa do
bloqueador de pop-up. A planilha viaja em base64 pela ponte e o `NSSavePanel`
escolhe o destino. O registro de exclusões (`biblioteca-removidas.json`) passou
a ser **consultado** na mesclagem, e não só escrito; sete pontos do código
apagavam capa e apenas dois registravam.

## Nada muda nos seus dados

Os 749 livros e as capas continuam onde estavam. Quem usa o Android pelo Google
Drive não precisa fazer nada de diferente.
