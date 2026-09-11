# Biblioteca 1.9.0

## Backup automático (todas as plataformas)

Antes da primeira gravação de cada sessão, o app compara o conteúdo do que vai
gravar com o que está no arquivo. Se mudou, guarda uma cópia em `Backups/`,
ao lado dos arquivos. Ficam as **30 últimas** cópias do `biblioteca.txt` e as
**7 últimas** do `biblioteca.dat` — o `.dat` é muito maior por causa das capas.

No Android o backup fica na área reservada do app, não na pasta escolhida: o
Android dá permissão para o *arquivo* escolhido, não para a pasta dele.

## Capas apagadas não voltam mais

Apagar uma capa valia só no aparelho onde foi apagada. Na sincronização
seguinte, qualquer outro aparelho que ainda a tivesse a devolvia — as capas
viajam pelo `biblioteca.dat` e cada lado **mescla** o que tem com o que está no
arquivo; mesclagem só sabe somar.

Agora existe um `biblioteca-removidas.json` na mesma pasta, registrando o que
foi apagado e quando. Quem lê o arquivo respeita o registro. Se você
refotografar uma capa depois de apagá-la, a foto nova vale — é por isso que o
registro guarda a data, e não só uma lista.

Entradas com mais de 90 dias saem do registro sozinhas.

## Fotos sem livro (Mac e Windows)

Apagar uma capa órfã funcionava só na tela: ela sumia e voltava ao reabrir o
app. As três funções de limpeza gravavam por um caminho que só o navegador
atende. Corrigido.

## Windows virou app nativo

Não abre mais o `biblioteca.html` no Chrome. Some o passo de vincular o arquivo
à mão e a permissão que caducava a cada sessão: o app encontra sozinho
`C:\Users\<você>\iCloudDrive\Biblioteca`. O instalador remove a versão anterior.

## Android: o vínculo com o arquivo mudou

O app passou a usar o seletor de documentos do sistema. **Na primeira abertura
desta versão ele pede para escolher o `biblioteca.txt` de novo** — o vínculo
antigo é descartado de propósito. Não é defeito.

Antes, o que parecia ser o seu arquivo era uma cópia temporária em cache: as
gravações não chegavam ao original.

## As capas não ocupam mais espaço em dobro

No Mac elas ficavam guardadas duas vezes (9,6 MB duplicados) e no Windows
simplesmente não persistiam, por estouro de cota do armazenamento do navegador.
