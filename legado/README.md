# Legado

Código fora de circulação. Nada aqui é compilado, distribuído ou mantido —
mas nada aqui foi apagado.

## `terminal-cpp/`

O app original: um menu de terminal em C++17 sobre o mesmo `biblioteca.txt`.
Abandonado em 3 de setembro de 2026 por decisão do autor — as interfaces web
e móvel cobrem o uso real.

**Vale saber:** é o único código do projeto com testes automatizados — 28 casos
em 6 suítes (Google Test), cobrindo normalização de texto, o parser de TSV, o
round-trip de persistência e a leitura de arquivos legados de 5 a 7 colunas.
Se algum dia o parser do TSV der problema em outra plataforma, os casos de
teste daqui são a especificação escrita do formato.

```bash
cmake -S . -B build && cmake --build build && ./build/tests/testes_biblioteca
```

## `web-tauri/`

Empacotamento do motor web como app desktop via Tauri v2 (Rust) com frontend
PWA e um servidor HTTP local em PowerShell para Windows.

Parado em 1º de julho de 2026 na tag `v0.5.8`. Substituído por
`motor-web/macos/` (app Swift nativo, assinado) e `motor-web/windows/`
(atalhos, que já bastavam). Era a terceira embalagem do mesmo `biblioteca.html`.

Tem repositório próprio no GitHub — `ruggierow/biblioteca-app` — e é o único
código do projeto que chegou a ter CI configurado.

**Pegadinha registrada:** o `src-tauri/tauri.conf.json` ficou defasado, declarando
0.4.9 enquanto o frontend e as tags do git diziam 0.5.6 a 0.5.8. Se alguém
retomar, comece conferindo isso.
