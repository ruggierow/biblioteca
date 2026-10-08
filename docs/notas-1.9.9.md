# Biblioteca 1.9.9

**No Windows, o link "Ler" não abria o navegador.**

## O que acontecia

Nos comentários dos livros do Kindle há dois links. No Windows, o **Kindle**
funcionava — abria o aplicativo, e o título copiado achava o livro com um
Ctrl+V. Já o **Ler**, que leva ao leitor da Amazon, não fazia nada: nem abria o
navegador, nem avisava.

Não era falta de navegador padrão — o Windows do usuário tem o Chrome associado
a `https`, lido direto do registro da conta dele.

Era o mecanismo. O programa entregava o endereço ao sistema com
`rundll32 url.dll,FileProtocolHandler`, que dá conta de um esquema de aplicativo
como `kindle://` mas se perde com `?` e `&` — e o endereço do leitor é
`read.amazon.com/?asin=…`, que tem os dois.

## Como ficou

Agora o Windows tenta três caminhos, em ordem: o `start` do próprio `cmd` (as
aspas protegem o `&`), o `Start-Process` do PowerShell, e o `rundll32` como
último recurso. Se os três falharem, o programa **diz o que cada um respondeu**,
em vez de ficar calado — foi o silêncio que custou a ida e volta anterior.

O endereço nunca é interpolado em comando: vai por variável de ambiente, e
endereço com aspas ou caractere de controle é recusado antes de qualquer
tentativa.

## O que o link do Kindle faz em cada plataforma

Com esta versão, o levantamento fica completo:

| plataforma | o rótulo **Kindle** | o rótulo **Ler** |
|---|---|---|
| Android | abre **o livro** | abre o navegador |
| iPhone | abre a biblioteca | abre o navegador |
| Mac | abre a biblioteca | abre o navegador |
| Windows | abre a biblioteca | **corrigido nesta versão** |

Onde o aplicativo para na biblioteca, o título já vai para a área de
transferência no clique: basta colar na busca do Kindle.
