# Spec Delta

## MODIFIED Requirements

### Requirement: Catálogo visual de jogos de exemplo
O sistema SHALL manter uma lista fixa de pelo menos 12 jogos de exemplo, cada um identificado pelo nome e associado a uma capa com texto alternativo acessível. A cada carregamento de `/catalogo`, o sistema SHALL sortear oito jogos distintos dessa lista e SHALL apresentar um deles, escolhido aleatoriamente entre os oito, em destaque no topo com capa maior e nome; os demais SHALL aparecer em uma grade abaixo. Se a imagem de uma capa falhar, o sistema SHALL apresentar um fallback que identifique o jogo pelo nome. Os exemplos SHALL ser explicitamente ilustrativos e SHALL NOT sugerir preços, popularidade ou promoções atuais ou verificadas.

#### Scenario: Exibição dos jogos de exemplo
- **WHEN** uma pessoa autenticada carrega `/catalogo`
- **THEN** o sistema apresenta oito jogos distintos da lista fixa, com um jogo aleatório em destaque no topo e os outros sete em grade abaixo

#### Scenario: Variação entre carregamentos
- **WHEN** o catálogo é carregado novamente
- **THEN** o sistema sorteia novamente os jogos apresentados e o jogo em destaque, sem exigir que a seleção seja diferente da anterior

#### Scenario: Capa acessível
- **WHEN** o catálogo apresenta a capa de um jogo
- **THEN** a imagem inclui texto alternativo que identifica o jogo

#### Scenario: Falha ao carregar uma capa
- **WHEN** a imagem da capa de um jogo não pode ser carregada
- **THEN** o catálogo apresenta um fallback visível que identifica o jogo pelo nome

#### Scenario: Dados de ofertas ainda não disponíveis
- **WHEN** o catálogo apresenta um jogo de exemplo
- **THEN** o sistema não afirma que o jogo está em promoção, popular ou com preço atual e não exibe preço de oferta não verificado
