# Biblioteca 1.9.6

**Clicar no link "Kindle" copia o título do livro.**

## Por quê

O aplicativo Kindle abre na sua biblioteca, nunca no livro — e isso não tem
conserto pelo lado do endereço: o esquema `kindle://` não tem rota de busca.
No pacote do Kindle 7.68 existe uma única cadeia desse esquema, e é um link de
propaganda.

A saída, ideia sua: com o título já na área de transferência, basta um **Ctrl+V
na busca do Kindle** e o livro abre. Vale sobretudo **sem conexão**, quando o
leitor da web não serve de nada e o Kindle instalado no computador é o único
caminho.

## Como se comporta

Ao clicar em **Kindle**, nas quatro plataformas: o título vai para a área de
transferência, um aviso curto confirma o que foi copiado, e o Kindle abre como
antes.

**Só esse link copia.** O link **Ler** abre o livro direto no leitor da Amazon e
não tem por que mexer na sua área de transferência — apagar o que você copiou
sem necessidade seria grosseria do programa.

## Detalhe para quem olha o código

A cópia vai pelo **lado nativo** em todas: `NSPasteboard` no Mac, `Set-Clipboard`
no Windows, `UIPasteboard` no iPhone, `Clipboard.setData` no Android. Dentro dos
aplicativos de mesa a página vem de `file:`, que não é contexto seguro, e o
`navigator.clipboard` simplesmente não existe lá — ele ficou como último recurso,
para quando o motor roda num navegador comum.

No Windows o texto passa por um arquivo em UTF-8 lido com `Get-Content -Encoding
UTF8`, e não por cano para o `clip.exe`: o `clip` interpreta a entrada na página
de código do console, e título brasileiro é cheio de acento — *"A paixão segundo
G. H."* sairia torto.
