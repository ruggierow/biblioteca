# Exclusão de fotos entre dispositivos

## O problema que isto resolve

As capas viajam entre aparelhos pelo `biblioteca.dat`, e cada lado **mescla** o
que tem com o que está no arquivo. Mesclagem só sabe somar.

Aconteceu em 10/09/2026: quatro fotos órfãs foram apagadas no Mac (o `.dat` foi
de 12 para 8 capas); o iPhone, que ainda tinha as 12 em `Documents/capas/`,
gravou o `.dat` na sincronização seguinte e **as quatro voltaram**. Quem apaga
sempre perde para quem ainda tem o arquivo.

Pior no caso das órfãs: elas são capas *sem livro*, então não aparecem em tela
nenhuma do iPhone — ficam invisíveis e imortais.

## O registro de exclusões

Um arquivo ao lado dos outros, na mesma pasta:

```
biblioteca-removidas.json
```

Conteúdo — o `fotoId` e quando foi apagado:

```json
{
  "1bget0qipcs1r":     "2026-09-10T23:40:12Z",
  "2ikgof34ngo1u4ga":  "2026-09-10T23:40:12Z"
}
```

**É um arquivo separado de propósito.** Mudar o formato do `.dat` quebraria toda
versão já instalada. Assim, um app antigo simplesmente ignora o registro e se
comporta como hoje — não sincroniza exclusões, mas também não quebra. A
implantação pode ser gradual.

## As regras

**Ao apagar uma capa**, em qualquer plataforma: registrar `fotoId` com a data
de agora, e remover a foto do `.dat` e do armazenamento local.

**Ao mesclar** o local com o `.dat`: pular todo `fotoId` que estiver no
registro, e **apagar o arquivo local correspondente** — senão a foto continua
aparecendo no aparelho mesmo sem estar no `.dat`.

**Exceção — refotografar:** se a capa local for **mais nova** que o carimbo da
exclusão, o usuário tirou a foto de novo depois de apagar. A exclusão está
superada: o `fotoId` sai do registro e a foto vale.

**Limpeza:** entradas com mais de 90 dias saem do registro. Depois desse prazo,
qualquer aparelho que ainda tivesse a foto já teria sincronizado.

## Por que carimbo de tempo, e não só uma lista

Sem a data não há como distinguir "esta foto foi apagada" de "esta foto é nova e
ainda não chegou ao arquivo". O carimbo é o que permite a exceção do
refotografar — sem ele, um `fotoId` apagado uma vez ficaria banido para sempre.

## Onde está implementado

| | Registra exclusões | Honra o registro |
|---|---|---|
| App do Mac | `BibliotecaWebApp.swift` | idem |
| App do Windows | `lib.rs` | idem |
| App do iPhone | `FotoStore.swift` | `escreverDat` e `sincronizarComDat` |
| Motor web (HTML) | avisa a camada nativa ao apagar | — |
| App do Android | — (as capas ainda não sincronizam) | — |

**O HTML avisa explicitamente quais `fotoId` foram apagados** — a camada nativa
não deduz por diferença entre o que recebeu e o que havia no arquivo. Deduzir
seria perigoso: se a memória estivesse incompleta (cota estourada, leitura
falha), a diferença pareceria uma exclusão em massa.
