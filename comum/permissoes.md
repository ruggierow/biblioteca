# Permissões — o comportamento que vale em todas as plataformas

Os apps móveis usam a câmera em **dois** lugares: o scanner de código de barras
e a captura da foto de capa. Antes desta especificação, cada um dos dois tratava
a negação de permissão de um jeito, e a captura de capa não tratava de jeito
nenhum — no iOS ficava uma tela preta, no Android o seletor voltava vazio e nada
acontecia.

Este documento define um comportamento só. Vale para os dois usos da câmera,
nas duas plataformas.

## Os quatro estados

| Estado | O que fazer |
|---|---|
| **Concedida** | Abrir a câmera. |
| **Nunca perguntada** | Pedir. Se conceder, abrir; se negar, cair no estado abaixo. |
| **Negada** | Mostrar a tela de permissão negada (abaixo). Nunca falhar em silêncio. |
| **Restrita** (controle parental, política de dispositivo) | Mesma tela, sem o botão de Configurações — não adianta, o usuário não pode mudar. |

## A tela de permissão negada

Fundo preto, conteúdo centralizado, e sempre estes mesmos elementos:

- **Ícone:** câmera cortada (`no_photography_outlined` no Flutter, `camera.fill.badge.ellipsis` no iOS)
- **Título:** `Acesso à câmera negado`
- **Texto, no scanner:** `Para escanear o código de barras, permita o acesso à câmera nas configurações do dispositivo.`
- **Texto, na captura de capa:** `Para fotografar a capa, permita o acesso à câmera nas configurações do dispositivo.`
- **Texto, se restrita:** `O acesso à câmera está bloqueado neste dispositivo.`

Botões, nesta ordem:

1. **Abrir Configurações** — botão preenchido, azul `#2B5FB3`. Ausente se restrita.
2. **Digitar ISBN** — só no scanner, onde existe alternativa sem câmera.
3. **Cancelar** — texto simples, fecha a tela.

## Ao voltar das Configurações

Se o usuário sai para as Configurações e volta, o app **reconsulta** o estado da
permissão. Se agora está concedida, a câmera abre sozinha — sem exigir que ele
navegue de novo até a tela. É o ponto que mais frustra quando falta.

## Galeria de fotos — a exceção

A galeria **não** passa por este fluxo, e isso é deliberado.

A partir do Android 13, escolher uma imagem usa o seletor do sistema, que roda
fora do app e não exige permissão nenhuma. Pedir `READ_MEDIA_IMAGES` ali só
criaria uma recusa falsa: o usuário nega, e o app mostra uma tela de permissão
negada para uma operação que teria funcionado. Por isso a checagem em
`cadastro_view.dart` cobre apenas `ImageSource.camera`.

No iOS não há caso: o app nunca lê a galeria, só a câmera. Por isso o
`Info.plist` declara apenas `NSCameraUsageDescription` — e deve continuar assim.
Se um dia a galeria for usada, `NSPhotoLibraryUsageDescription` passa a ser
obrigatória, ou o app é rejeitado na revisão da App Store.

## Onde está implementado

| | iOS | Android (Flutter) |
|---|---|---|
| Consulta e pedido | `Servicos/Permissoes.swift` | `lib/services/permissoes.dart` |
| Tela | `Views/PermissaoNegadaView.swift` | `lib/views/permissao_negada_view.dart` |
| Usada pelo scanner | `Views/ScannerView.swift` | `lib/views/scanner_view.dart` |
| Usada pela capa | `Views/CapaCameraView.swift` | `lib/views/cadastro_view.dart` |

Mexeu em um, confira o outro.
