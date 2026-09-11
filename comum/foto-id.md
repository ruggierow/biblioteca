# `fotoId` — a chave que liga um livro à sua capa

Uma foto tirada no iPhone precisa ser encontrada pelo Android e pela web. Como
o `biblioteca.txt` não tem coluna de identificador, a chave é **derivada** do
título e dos autores, com um hash que precisa dar o mesmo resultado nas três
linguagens.

## O algoritmo

FNV-1a duplo, de 32 bits, sobre uma chave normalizada:

1. Título em minúsculas, espaços colapsados para um só, sem espaços nas pontas.
2. Cada autor recebe o mesmo tratamento; autores vazios são descartados; a
   lista resultante é **ordenada** (para que a ordem dos autores não mude a chave).
3. Junta-se `[título] + autores` com o separador `\0`.
4. Dois acumuladores FNV-1a correm sobre a chave: `h1` sobre o code point, `h2`
   sobre o code point somado à posição mais 1.
5. Resultado = `h1` em base 36, concatenado com `h2` em base 36.

```
h1 = 2166136261    h2 = 2246822519    primo = 16777619
h1 = (h1 XOR c) * primo
h2 = (h2 XOR (c + i + 1)) * primo
```

Tudo truncado em 32 bits sem sinal.

## As três implementações

| Plataforma | Arquivo |
|---|---|
| iOS | `motor-movel/ios/Biblioteca.App/Models/Livro.swift` — `var fotoId` |
| Android | `motor-movel/android/lib/models/livro.dart` — `String get fotoId` |
| Web | `motor-web/biblioteca.html` — `function gerarId(titulo, autores)` |

**Cuidado com o overflow.** Swift usa `&*` (multiplicação que ignora estouro) e
`UInt32`. Dart não tem inteiro de 32 bits, então mascara com `& 0xFFFFFFFF` a
cada passo. JavaScript precisa de `>>> 0`. Uma dessas três omitida e a mesma
obra ganha chaves diferentes em plataformas diferentes — a foto some, sem erro.

## Onde as fotos ficam

- iOS e Android: `Documents/capas/<fotoId>.jpg`
- Web: `localStorage`, sob a chave `biblioteca-fotos`, como data URI

## Quando título ou autores mudam

A chave muda junto, e a foto ficaria órfã. Por isso as três implementações têm
`migrar(de:para:)` — ao salvar uma edição que altera título ou autores, a foto
é movida da chave antiga para a nova. Se você acrescentar um campo à chave,
acrescente nos três, e lembre que todas as fotos já salvas mudam de nome.
