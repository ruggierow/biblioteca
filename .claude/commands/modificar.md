# /modificar — Protocolo para Qualquer Edição de Código

Use este protocolo SEMPRE antes de implementar qualquer alteração em código, seja correção de bug, modificação de funcionalidade ou adição de funcionalidade.

## Passos obrigatórios

### 1. Diagnóstico
- Identifique a causa raiz exata do problema ou descreva com precisão o que será adicionado/modificado
- Indique o arquivo e número de linha onde a edição será feita

### 2. Escopo mínimo
- Liste explicitamente quais linhas/funções SERÃO alteradas
- Liste o que NÃO será tocado, especialmente código adjacente
- Se a edição exigir alterar mais de um trecho, justifique cada um

### 3. Proposta (PARAR e aguardar aprovação)
- Mostre o diff planejado (antes → depois) para cada alteração
- Aguarde o usuário aprovar antes de implementar

### 4. Linha de base dos testes (ANTES de tocar no código)

Antes de fazer qualquer alteração, rode a suíte de testes e registre o resultado como linha de base:

1. Consulte o `CLAUDE.md` do projeto para localizar o comando de teste. Padrões comuns:
   - **CMake + Google Test:** `cmake --build build` e depois rode o executável em `build/tests/`
   - **pytest:** `pytest tests/`
   - **Jest / Vitest:** `npm test`
   - **Xcode:** `xcodebuild test`
2. Anote quantos testes passam e quantos falham **antes** da edição.
3. Se já houver falhas antes de começar, informe o usuário — não avance sem entender o estado inicial.

### 5. Implementação
- Faça somente as alterações aprovadas no passo 3
- Não aproveite para "limpar", "refatorar" ou "melhorar" código não relacionado

### 6. Verificação de regressão (DEPOIS de editar)

#### 6a. Testes automatizados
1. Rode a suíte completa com o mesmo comando do passo 4.
2. Compare com a linha de base: o número de testes que passam **não pode diminuir**.
3. Se algum teste que passava antes agora falha: **a edição introduziu uma regressão** — reverta e investigue antes de prosseguir.
4. Se algum teste que já falhava antes continua falhando: registre, mas não bloqueie (não foi você que quebrou).
5. Se algum teste precisou ser atualizado por conta da edição, justifique explicitamente o motivo.

#### 6b. Mudanças de UI / Frontend
Suba o servidor de dev e teste a funcionalidade no navegador, cobrindo o caminho principal e os casos de borda.

#### 6c. Sem testes automatizados
Reproduza o cenário que estava com problema e confirme que agora funciona como esperado. Se não houver forma de reproduzir, diga isso explicitamente em vez de presumir que foi corrigido.

### 7. Verificação de escopo
- Confirme que nenhuma linha fora do escopo aprovado foi alterada
- Se houver mudança não planejada, reverta e explique o que aconteceu

## Regra fundamental

> Qualquer edição de código deve ser mínima e precisa. Não altere código que não tem relação direta com o que foi aprovado. Em caso de dúvida, não altere.
