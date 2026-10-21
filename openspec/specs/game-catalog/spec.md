# Game Catalog Specification

## Purpose

Esta capacidade oferece uma página autenticada para descobrir jogos por meio de capas e exemplos visuais e iniciar uma busca Steam pelo título desejado.

## Requirements

### Requirement: Catálogo visual de jogos de exemplo
O sistema SHALL manter uma lista fixa de pelo menos 12 jogos de exemplo, cada um identificado pelo nome e associado a uma capa com texto alternativo acessível. A cada carregamento de `/catalogo`, o sistema SHALL sortear oito jogos distintos dessa lista e SHALL apresentar um deles, escolhido aleatoriamente entre os oito, em destaque no topo com capa maior e nome; os demais SHALL aparecer em uma grade abaixo. Se a imagem da capa falhar, o sistema SHALL apresentar um fallback que identifique o jogo pelo nome. Os exemplos SHALL ser explicitamente ilustrativos e SHALL NOT sugerir preços, popularidade ou promoções atuais ou verificadas.

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

### Requirement: Pesquisa a partir do catálogo
O sistema SHALL apresentar no topo do catálogo uma barra de pesquisa com o texto de exemplo “Comparar Preços”. Ao submeter um termo não vazio, o sistema SHALL navegar para a busca pública existente em `/buscar` e SHALL encaminhar o termo para ser exibido no campo de pesquisa dessa página. A pesquisa e a consulta de preço SHALL continuar seguindo as ações do fluxo existente em `/buscar`.

#### Scenario: Encaminhar um termo à busca Steam
- **WHEN** a pessoa informa um termo na barra do catálogo e submete a pesquisa
- **THEN** o sistema abre `/buscar` com o termo preenchido no campo de pesquisa

#### Scenario: Submeter pesquisa vazia
- **WHEN** a pessoa tenta submeter a barra do catálogo sem texto ou apenas com espaços
- **THEN** o sistema permanece no catálogo e informa que é necessário preencher um termo

#### Scenario: Abrir busca sem termo encaminhado
- **WHEN** uma pessoa abre `/buscar` sem vir de uma pesquisa do catálogo
- **THEN** a busca Steam mantém seu comportamento existente e inicia sem termo preenchido

### Requirement: Acesso à comparação pelos cards do catálogo
Cada jogo de exemplo do catálogo SHALL ter um App ID Steam válido. Os cards do jogo em destaque e dos demais jogos SHALL ser clicáveis e abrir a rota dedicada de comparação para o App ID Steam correspondente.

#### Scenario: Abrir comparação pelo jogo em destaque
- **WHEN** uma pessoa seleciona o card do jogo em destaque no catálogo
- **THEN** o sistema abre `/comparar?app_id=<id>` usando o App ID Steam daquele jogo

#### Scenario: Abrir comparação pela grade
- **WHEN** uma pessoa seleciona um card da grade do catálogo
- **THEN** o sistema abre `/comparar?app_id=<id>` usando o App ID Steam daquele jogo

### Requirement: Rodapé do catálogo
O catálogo SHALL apresentar, após o jogo em destaque e a grade, um rodapé com um texto institucional curto sobre o ComparaKeys e um link para `/buscar`.

#### Scenario: Exibir o rodapé após o catálogo
- **WHEN** uma pessoa percorre a página do catálogo até o final da grade de jogos
- **THEN** o sistema apresenta o texto institucional do ComparaKeys e um link navegável para `/buscar`
