# `biblioteca.txt` — o formato de dados

Um arquivo de texto, uma linha por livro, campos separados por TAB. É o único
ponto de encontro entre as cinco entregas: todas leem e escrevem este arquivo.

## As 8 colunas, nesta ordem

```
titulo <TAB> autor <TAB> tema <TAB> ano <TAB> emprestado <TAB> comentarios <TAB> local <TAB> grupoLiteratura
```

- `emprestado` e `grupoLiteratura` são `1` ou `0`
- `tema` aceita vários, separados por `; ` (ponto e vírgula mais espaço)
- os demais são texto livre

## Compatibilidade retroativa

Arquivos antigos com 5, 6 ou 7 colunas continuam sendo lidos: as colunas
faltantes assumem o valor padrão. Isso não é um acidente — é comportamento
testado, e há casos para ele em `legado/terminal-cpp/tests/test_biblioteca.cpp`
(suíte `CompatibilidadeTest`). Se um dia o parser for reescrito, esses testes
são a especificação.

## A divergência conhecida do campo `autor`

Não é um defeito de gravação — os dois lados leem o arquivo do outro sem
corromper nada — mas é uma diferença de significado que vale conhecer:

- A **web** e o **terminal** tratam `autor` como um texto livre único.
- O **iOS** e o **Android** tratam como uma lista separada por `;`.

Na prática: um livro com "Fulano e Beltrano" gravado pela web aparece como um
autor só no celular. Um livro com dois autores gravado no celular chega à web
como o texto "Fulano; Beltrano". Nada se perde, mas a contagem de autores
difere. Se for unificar, unifique nos quatro ao mesmo tempo — e lembre que o
`fotoId` depende da lista de autores, então todas as capas seriam rechaveadas.

## Onde fica o arquivo de verdade

`~/Library/Mobile Documents/com~apple~CloudDocs/Biblioteca/biblioteca.txt`
no iCloud da sua Apple ID.

O iPhone chega nele pelo iCloud Drive; o Android, pelo Google Drive marcado
como disponível offline; o Mac, apontando o app direto para o caminho acima.

**Modelo de conflito: a última gravação vence.** Não há mesclagem. Editar no Mac
e no celular ao mesmo tempo perde um dos dois lados.
