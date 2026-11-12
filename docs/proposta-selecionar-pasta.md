# "Selecionar pasta": o mesmo primeiro uso nas quatro plataformas

Proposta aprovada por ele em **12/11/2026**. Este documento é a referência da
implementação — a ordem dos passos, os textos nos dois idiomas e as decisões
já tomadas ficam aqui, para não viverem só num diálogo.

## Estado: os cinco passos, FEITOS em 12/11/2026

| | |
|---|---|
| 1. Android | `3aab130` (motor-movel/android) |
| 2. iPhone | `cf63096` (motor-movel/ios) |
| 3. Windows | `8ee4d35` (motor-web) |
| 4. Mac | `4056ef1` (motor-web) + `a96ed7f` (raiz, o portão da ponte) |
| 5. Manuais | `01f7001` (raiz) |

Dois achados de fora do roteiro, os dois vistos **na tela**, não por teste: em
inglês o botão do Android dizia *Select folder* enquanto as outras três diziam
*Choose folder*, e a frase de ajuda da faixa falava de "vincular" e de
"navegadores sem suporte" **dentro do aplicativo instalado**, onde nenhuma das
duas coisas existe.

Falta um clique humano: percorrer o seletor de pastas do Mac até outra pasta e
confirmar. O painel do sistema roda em outro processo e não é para contornar.

## O problema que isto resolve

Hoje as quatro plataformas fazem **quatro coisas diferentes** quando alguém
instala o app e ainda não tem um `biblioteca.txt`. Medido em 07, 08 e
12/11/2026:

| | o que acontece hoje |
|---|---|
| **Mac** | mostra a janela "Bem-vindo"; a opção **recomendada não faz nada** (o WebKit não tem `showDirectoryPicker` nem `showOpenFilePicker`); sem arquivo, abre com um alerta de erro cru. Funciona só se o usuário escolher "Decidir depois" — cujo texto diz, falsamente, que os dados ficam só no navegador |
| **Windows** | o melhor dos quatro: a janela nunca aparece e `salvar_tsv` cria pasta e arquivo na primeira gravação. Mas a pasta só se configura **editando `pasta.txt` à mão** |
| **iPhone** | vincula a pasta; o arquivo nasce ao cadastrar o primeiro livro |
| **Android** | desde a 1.9.20, uma linha "Criar biblioteca.txt nesta pasta" na tela de Sincronização |

Quatro histórias para contar nos manuais, e três delas com aresta.

## O alvo

Um botão novo, **com o mesmo nome e o mesmo comportamento nos quatro apps**,
que leva de "acabei de instalar" a "tenho um arquivo vinculado e posso
cadastrar" em um passo — sem perguntar nada que o usuário não tenha como
responder.

O botão de **Sincronização dos celulares fica como está**. O novo é um
botão a mais, não um renomeado: trocar o nome de um botão conforme o estado
deixa o usuário sem referência fixa.

### Onde ele fica

| | lugar |
|---|---|
| **iPhone** | nova linha na tela inicial, acima de *Sincronização* |
| **Android** | idem |
| **Mac** | primeiro botão da faixa *Arquivo biblioteca.txt* |
| **Windows** | idem |

Nos celulares existe "Sincronização" para manter; no Mac e no Windows o
equivalente é a faixa do arquivo.

## O fluxo

**1.** O usuário toca em *Selecionar pasta*.

**2.** Abre o seletor de pastas do sistema, **já posicionado** na pasta que o
app encontraria sozinho (`iCloudDrive/Biblioteca` no Mac e no Windows). No
Mac e no Windows isso vira uma confirmação em vez de uma procura — o acerto
automático de hoje não se perde.

**3.** O app procura `biblioteca.txt` na pasta escolhida.

### Ramo A — achou

Não pergunta às cegas: **lê o arquivo, conta os livros e mostra o que achou.**

> **Encontrei uma biblioteca nesta pasta**
> A pasta "Biblioteca" já tem um biblioteca.txt com **757 livros**.
>
> `[ Escolher outra pasta ]` `[ Usar esta biblioteca ]`

A pergunta fica respondível porque o usuário vê o que está aceitando.

### Ramo B — não achou

Cria `biblioteca.txt`, vincula e avisa. **Sem perguntar** — o usuário acabou
de escolher aquela pasta com essa finalidade.

> Criei o biblioteca.txt em "Biblioteca". Pode começar a cadastrar.

### Ramo C — achou, mas não consegue ler

Diz o que houve e oferece escolher outra pasta. **Nunca cria por cima.**

### Ramo D — troca de pasta com livros abertos

Só acontece depois do primeiro uso: o usuário já tem livros carregados e
escolhe uma pasta **vazia**. Decisão dele em 12/11 — **perguntar**:

> **Esta pasta está vazia.**
> O que fazer com os 757 livros que estão abertos?
>
> `[ Criar uma biblioteca nova e vazia ]` `[ Levar os 757 para esta pasta ]`

### Casos de borda

- **Cancelou o seletor** → nada muda, nada de erro.
- **O arquivo apareceu entre a checagem e a criação** → usa o existente. O
  Kotlin do Android já faz isso, porque alguns provedores renomeiam para
  `biblioteca (1).txt` e o app passaria a gravar no arquivo errado.
- **Android recusa raízes** → aviso antes de abrir o seletor.

## O nome do arquivo NÃO é escolhido pelo usuário

Na proposta original havia um ramo: se a pasta já tivesse um
`biblioteca.txt` e o usuário dissesse "não", o app criaria outro arquivo com
um nome fornecido por ele. **Isso foi descartado em 12/11**, e a razão é
importante o bastante para ficar escrita.

Os quatro apps procuram o arquivo **pelo nome fixo**:

| | |
|---|---|
| Mac | `.../Biblioteca/biblioteca.txt`, cravado em `BibliotecaWebApp.swift:31` |
| Windows | `localizar("biblioteca.txt")` |
| iPhone | `pasta.appendingPathComponent("biblioteca.txt")` |
| Android | `arquivoPadrao = 'biblioteca.txt'` |

Um `meus-livros.txt` existiria **só no aparelho onde foi criado**. O usuário
abriria o iPhone e veria a biblioteca vazia, sem erro e sem aviso — a família
de falha que este projeto mais combate.

Além disso, pedir a um usuário recém-chegado que **invente um nome de
arquivo** no primeiro minuto é uma decisão sem informação para apoiá-la. E
pense em quando ele diria "não": ou o arquivo é dele (a resposta é sim), ou
ele errou a pasta (a resposta certa é *escolher outra pasta*), ou quer duas
bibliotecas na mesma pasta (raro, e melhor resolvido com duas pastas). Em
dois dos três casos o "não" faz algo pior que a alternativa.

**Uma biblioteca por pasta, com nome fixo.** Ter várias é "trocar de pasta",
que este mesmo botão já faz.

## Os textos

Chaves novas para os três dicionários (`TEXTOS` do `biblioteca.html`,
`Idioma.swift`, `idioma.dart`):

| chave | português | english |
|---|---|---|
| `selecionarPasta` | Selecionar pasta | Choose folder |
| `selecionarPastaDica` | Onde o seu biblioteca.txt está — ou vai ficar | Where your biblioteca.txt is — or will be |
| `achouBiblioteca` | Encontrei uma biblioteca nesta pasta | Found a library in this folder |
| `achouBibliotecaCorpo` | A pasta "${0}" já tem um biblioteca.txt com ${1} livro(s). | The folder "${0}" already has a biblioteca.txt with ${1} book(s). |
| `usarEstaBiblioteca` | Usar esta biblioteca | Use this library |
| `escolherOutraPasta` | Escolher outra pasta | Choose another folder |
| `criouArquivo` | Criei o biblioteca.txt em "${0}". Pode começar a cadastrar. | Created biblioteca.txt in "${0}". You can start adding books. |
| `naoConsegueLer` | Há um biblioteca.txt nesta pasta, mas não consegui lê-lo: ${0} | There is a biblioteca.txt in this folder, but it could not be read: ${0} |
| `escolhaSubpasta` | Escolha uma subpasta. O Android não deixa escolher "Meu Drive" nem a memória do telefone. | Choose a subfolder. Android does not allow picking "My Drive" or the phone's storage. |
| `pastaVaziaComLivros` | Esta pasta está vazia. O que fazer com os ${0} livros que estão abertos? | This folder is empty. What should happen to the ${0} books you have open? |
| `comecarVazia` | Criar uma biblioteca nova e vazia | Start a new, empty library |
| `levarParaPasta` | Levar os ${0} para esta pasta | Move the ${0} here |

Acentuado nos três. O motor-web tem 51 entradas de 322 sem acento —
divergência antiga, ainda não mandada corrigir; as novas nascem certas.

## Ordem de implementação

Do menor risco ao maior, cada passo entregável sozinho.

**1. Android** — está a 80% do alvo. Sai a linha "Criar biblioteca.txt nesta
pasta", entram a criação sem pergunta e a confirmação do ramo A. Serve de
prova do fluxo antes de mexer no resto.

**2. iPhone** — mesma forma. Já escolhe pasta; faltam a confirmação com a
contagem e a criação automática.

**3. Windows** — a pasta configurável já existe (`pasta_configurada`), falta
a interface que a escreve. De quebra mata o `pasta.txt` editado à mão —
aquele que em 03/11 saiu do Bloco de Notas **com BOM**, invalidou o caminho e
fez o app servir calado a biblioteca de um mês antes.

**4. Mac** — o maior. Não existe seletor nenhum: o caminho é cravado.
Precisa de `NSOpenPanel` novo no Swift e de guardar a escolha. Fecha com a
**morte da janela "Bem-vindo"**.

**5. Manuais e notas** — o capítulo "primeira vez" dos quatro manuais conta
hoje quatro histórias. Vira uma só, o que encurta os quatro.

## O que NÃO se toca

A leitura e a gravação do TSV, o `biblioteca.dat`, o backup automático, a
sincronização existente, e o caminho automático do iCloud — que continua
sendo o padrão do seletor.

## Como se prova

Um teste por plataforma para os ramos A, B e C — **são todos caminhos de
escrita**, e o erro aqui custa a biblioteca de alguém. No Android e no
iPhone, medir no emulador: pasta vazia, toca, confere o arquivo no disco.

E **suíte verde não basta**. Os seis rótulos em português dentro do app em
inglês passaram por todos os testes; quem os achou foi fotografar as telas.
As três telas têm de ser vistas rodando nos quatro apps.
