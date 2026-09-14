# Biblioteca 1.9.1

## Pesquisa completa no iPhone e no Android

A pesquisa do celular tinha uma caixa de texto e dois botões; o Mac e o Windows
têm quatro campos, dois seletores e um "Limpar filtros". O buraco que mais doía:
no celular não dava para escolher **qual** grupo de literatura — só "está em
algum" ou "não está".

Agora há uma **folha de filtros**, aberta pelo ícone na barra:

- **Status** — Todos, Disponíveis, Emprestados;
- **Grupo de literatura** — Todos os livros, Qualquer grupo, ou **cada grupo,
  um a um**;
- **Só livros com foto**.

Acima da lista aparece o resumo do que está ligado, com um "Limpar" ao lado.

A caixa de busca continua uma só, e procura em título, autor, tema, local e ano.
Quatro caixas lado a lado é idioma de tela grande; no polegar uma caixa é melhor.

## Um livro pode estar em vários grupos (celular)

O cadastro do iPhone e do Android tinha um interruptor de sim/não. Agora tem
seleção múltipla, que é como o Mac e o Windows sempre guardaram. A tela de
detalhe passou a mostrar os nomes dos grupos em vez de "Sim".

## Os nomes dos grupos agora viajam

Os nomes que você dá aos grupos ("Clube da Tarde") viviam só no navegador e não
saíam dele — nem do Mac para o Windows. O arquivo `biblioteca.txt` guarda apenas
os números.

O Mac passa a gravar um `grupos.json` ao lado do `biblioteca.txt`. Quem vincula
a pasta lê esse arquivo e mostra os nomes. Quem não o encontra vê "Grupo 1",
"Grupo 2" — o filtro funciona igual, só o rótulo muda.

## Vincular a PASTA, não cada arquivo

O Mac e o iPhone sempre vincularam a pasta. O Android e o Windows pediam um
"vincular" para o `biblioteca.txt` e outro para o `biblioteca.dat` — e assim não
alcançavam nenhum arquivo vizinho.

Agora é uma escolha só, e dela saem os três arquivos.

**No Android**, ao atualizar, o app pede a pasta uma vez. Atenção: o Android
**recusa raízes** — "Meu Drive" e o armazenamento interno voltam com o botão
"Usar esta pasta" apagado. É preciso escolher uma subpasta, por exemplo
`Meu Drive/Biblioteca`.

**No Windows**, vale para quem abre o `biblioteca.html` no Chrome. O aplicativo
instalado continua gerenciando o arquivo sozinho, como antes.

## Correção: gravar pelo celular apagava grupos em silêncio

A interface web guarda na coluna 8 do arquivo uma **lista** de grupos ("1;3").
O celular lia só o "1" e, ao gravar, escrevia "0" — apagando a participação em
qualquer grupo que não fosse o primeiro, sem erro e sem aviso.

Nenhum arquivo foi perdido: até aqui só existia um grupo. O estrago começaria no
primeiro livro posto num segundo grupo. Agora o celular preserva a coluna
exatamente como a leu.
