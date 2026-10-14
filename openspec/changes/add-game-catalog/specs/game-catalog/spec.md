# Spec Delta

## Purpose

Esta capacidade oferece uma página autenticada para descobrir jogos por meio de capas e exemplos visuais e iniciar uma busca Steam pelo título desejado.

## ADDED Requirements

### Requirement: Catálogo visual de jogos de exemplo
O sistema SHALL apresentar em `/catalogo` uma seleção pequena de jogos de exemplo, identificando cada jogo pelo nome e exibindo sua capa com texto alternativo acessível. Os dados SHALL ser fixos nesta etapa e SHALL NOT sugerir que preços, popularidade ou promoções sejam atuais ou verificados.

#### Scenario: Exibição dos jogos de exemplo
- **WHEN** uma pessoa autenticada acessa o catálogo
- **THEN** o sistema apresenta os jogos de exemplo com seus nomes e capas

#### Scenario: Dados de ofertas ainda não disponíveis
- **WHEN** o catálogo apresenta um jogo de exemplo
- **THEN** o sistema não afirma que o jogo está em promoção nem exibe um preço de oferta não verificado

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
