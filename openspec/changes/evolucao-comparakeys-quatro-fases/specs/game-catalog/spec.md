# Spec Delta

## ADDED Requirements

### Requirement: Atalhos para páginas pessoais no catálogo
O cabeçalho do catálogo autenticado SHALL apresentar links para “Favoritos” (`/favoritos`) e “Histórico” (`/historico`). O catálogo SHALL exibir em cada card um controle de favorito acessível, cujo estado represente a lista do usuário conforme a capacidade `favorites`.

#### Scenario: Navegação pessoal no cabeçalho
- **WHEN** uma pessoa autenticada abre `/catalogo`
- **THEN** o cabeçalho oferece links para `/favoritos` e `/historico`

#### Scenario: Favoritar a partir de um card
- **WHEN** uma pessoa autenticada visualiza um card do catálogo
- **THEN** o card apresenta um coração acessível que permite adicionar ou remover aquele jogo dos favoritos

### Requirement: Jogos buscados recentemente
O catálogo autenticado SHALL apresentar uma seção “Buscados recentemente” com até cinco registros do histórico próprio mais recentes, conforme a capacidade `search-history`. Cada registro SHALL abrir a comparação pelo Steam App ID e o estado vazio SHALL orientar a pessoa a pesquisar um jogo.

#### Scenario: Mostrar itens recentes
- **WHEN** uma pessoa autenticada abre o catálogo e possui itens no histórico
- **THEN** a seção apresenta até cinco jogos recentes e cada um abre `/comparar?app_id=<steam_app_id>`

#### Scenario: Nenhum item recente
- **WHEN** uma pessoa autenticada abre o catálogo sem registros de histórico
- **THEN** a seção orienta a pessoa a pesquisar e comparar um jogo sem apresentar erro
