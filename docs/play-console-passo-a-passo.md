# Publicar a Biblioteca no Teste Fechado da Play Store

Objetivo: os testadores instalarem pela própria Play Store, sem o aviso de
"fontes desconhecidas" e sem o Play Protect. É o equivalente ao TestFlight.

## O que já está pronto

| | |
|---|---|
| Pacote `.aab` | `~/Desktop/Biblioteca-Web/Biblioteca-Android-1.9.0-b4.aab` (58 MB) |
| Assinatura | a mesma chave da APK que os testadores já têm (`5F:18:B7:…:54:D1`) |
| Política de privacidade | https://github.com/ruggierow/biblioteca/blob/main/docs/privacidade.md |
| Nome do pacote | `com.wilson.biblioteca.biblioteca` |
| versionCode | 4 |
| API alvo | 36 |

## O que só você pode fazer

1. **Criar a conta** em play.google.com/console — US$ 25, uma vez só.
2. **Verificação de identidade**: o Google pede documento com foto e endereço.
   Costuma levar de algumas horas a poucos dias.
3. **Enviar a chave de assinatura** (ver abaixo) — exige a senha do keystore.
4. **Aceitar os termos** do programa de desenvolvedor.

## A decisão que não dá para desfazer

Ao criar o app, o Google oferece gerar uma chave de assinatura nova.

**Não aceite. Envie a chave existente** — `_biblioteca-keystore/biblioteca-release.jks`.

Se o Google gerar uma chave nova, a assinatura do app muda, e **quem já tem a
APK instalada não consegue atualizar pela Play**: o Android recusa, e a pessoa
teria que desinstalar antes. Desinstalar **apaga as capas guardadas no
aparelho**. Com a chave enviada, a atualização acontece por cima e nada se perde.

O nome do pacote, `com.wilson.biblioteca.biblioteca`, também é **permanente**
depois da primeira publicação. Ele é redundante, mas trocá-lo agora criaria um
app diferente aos olhos do Android — os testadores atuais ficariam com duas
cópias. Não vale a pena; fica como está.

## Respostas do formulário de Segurança de Dados

O Google pergunta, item a item, o que o app coleta. Para a Biblioteca:

- **Coleta algum dado?** Não.
- **Compartilha algum dado?** Não.
- **Os dados são criptografados em trânsito?** As consultas de ISBN usam HTTPS.
- **O usuário pode pedir a exclusão dos dados?** Não se aplica: nada sai do
  aparelho. Os arquivos são dele e ele os apaga quando quiser.

Sobre as consultas de ISBN, se houver campo de observação: é enviado apenas o
número do ISBN, para BrasilAPI, Open Library e Google Books. Nenhum dado do
usuário ou do aparelho acompanha a consulta.

**Classificação de conteúdo:** o questionário vai perguntar sobre violência,
sexo, jogos de azar e afins — tudo "não". O resultado deve ser Livre.

## O caminho no Console

1. **Criar app** → nome "Biblioteca", português (Brasil), aplicativo, gratuito.

   **ATENÇÃO ao campo do nome de pacote nessa tela.** O Console passou a pedi-lo
   já na criação (antes ele só era definido no primeiro envio) e o preenche
   sozinho com uma sugestão montada a partir do nome do app — em 13/09/2026 ele
   propôs `com.biblioteca_myapp`, que passou despercebido. O valor tem de ser,
   exatamente:

       com.wilson.biblioteca.biblioteca

   Se errar: enquanto o app não tiver nenhuma versão publicada dá para
   **excluí-lo** (Configurações DO APP, no fim do menu da esquerda › Avançado ›
   Excluir app) e criar de novo. Depois da primeira publicação, não há volta.
2. **Assinatura de apps**, ANTES de enviar qualquer pacote — ver a seção
   anterior. Fica em *Testar e lançar › Configuração › Assinatura de apps*
   (o menu "Integridade do app" virou "Protegido com o Google Play" e NÃO é
   ali que a assinatura mora).

3. **Teste fechado** → criar uma faixa → criar uma lista de e-mails com os seus
   testadores.
4. **Enviar o `.aab`** na faixa de teste fechado.
5. Preencher: política de privacidade (URL acima), segurança de dados,
   classificação de conteúdo, público-alvo.
6. **Ficha da loja**: precisa de ícone 512×512, uma imagem de destaque
   1024×500 e ao menos duas capturas de tela do app. Texto sugerido abaixo.
7. Enviar para revisão. O teste fechado costuma sair em algumas horas a poucos
   dias.
8. Os testadores recebem um **link de aceite** — precisam abri-lo e aceitar
   antes de o app aparecer para eles na Play Store.

**Confira as regras vigentes de teste antes de contar prazos.** O Google passou
a exigir, para contas pessoais, um período mínimo de teste com um número mínimo
de testadores antes de liberar o app ao público. Isso vale para a publicação
aberta, não para o teste fechado — mas a regra muda, e a página do Console é a
fonte confiável.

## Texto sugerido para a ficha

**Nome:** Biblioteca

**Descrição curta** (até 80 caracteres):

    Catálogo dos seus livros, com capa e busca, sincronizado entre aparelhos.

**Descrição completa:**

    Biblioteca é um catálogo pessoal dos livros que você tem em casa.

    Cadastre um livro escaneando o código de barras da contracapa: o app
    procura título, autor, editora e ano sozinho. Fotografe a capa e ela fica
    junto do registro.

    Busque por título, autor, tema ou editora. O catálogo inteiro fica no seu
    aparelho, num arquivo que você escolhe — se esse arquivo estiver numa pasta
    do Google Drive ou do iCloud, os seus outros aparelhos veem o mesmo acervo.

    O app faz cópias de segurança sozinho, antes de gravar, guardando as
    últimas versões do seu catálogo.

    Sem cadastro, sem anúncios, sem rastreamento. Nada sai do seu aparelho,
    exceto o número do ISBN quando você pede para buscar os dados de um livro.

## Quando a conta estiver criada

Me avise que eu gero o `.aab` da versão vigente, confiro a assinatura contra a
que os testadores já têm e preparo as capturas de tela.
