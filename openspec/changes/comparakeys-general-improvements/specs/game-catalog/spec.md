# Spec Delta

## ADDED Requirements

### Requirement: Cards padronizados para catálogo e busca
Os cards de jogos exibidos no catálogo e nos resultados de busca SHALL manter uma hierarquia visual consistente para capa, nome e ação de navegação. Cada card SHALL identificar o jogo por nome acessível, preservar o Steam App ID correto e permitir abrir a comparação correspondente sem exigir precisão em um alvo pequeno. A capa SHALL ter texto alternativo e fallback que identifique o jogo pelo nome.

#### Scenario: Card do catálogo
- **WHEN** uma pessoa visualiza um jogo de exemplo no catálogo
- **THEN** o card mantém nome, capa acessível e destino de comparação identificável, seguindo o estilo visual comum dos outros cards

#### Scenario: Resultado de busca
- **WHEN** a busca apresenta vários jogos correspondentes
- **THEN** cada resultado mostra informações identificáveis e mantém seu próprio App ID ao abrir a comparação

#### Scenario: Falha de imagem
- **WHEN** a capa de um card falha ao carregar
- **THEN** o nome do jogo continua visível e identificável

### Requirement: Navegação consistente entre catálogo e recursos da conta
O catálogo e o cabeçalho autenticado SHALL oferecer caminhos claros entre catálogo, busca, comparação, histórico e favoritos, preservando as rotas existentes e sem iniciar chamadas a APIs externas apenas por renderizar um card. A busca SHALL continuar direcionando à rota pública `/buscar`; a seleção de jogo SHALL continuar abrindo `/comparar?app_id=<id>`.

#### Scenario: Navegar do catálogo à busca
- **WHEN** uma pessoa submete um termo válido no catálogo
- **THEN** o sistema abre `/buscar` com o termo encaminhado

#### Scenario: Abrir comparação a partir de um card
- **WHEN** uma pessoa seleciona um card de jogo
- **THEN** o sistema abre a comparação do Steam App ID associado ao card

#### Scenario: Atalhos da conta autenticada
- **WHEN** uma pessoa autenticada visualiza o catálogo ou cabeçalho
- **THEN** ela encontra links acessíveis para `/historico` e `/favoritos`

#### Scenario: Layout responsivo
- **WHEN** o catálogo ou os resultados são exibidos em desktop, tablet ou celular
- **THEN** cards e navegação permanecem legíveis e operáveis sem sobreposição ou rolagem horizontal
