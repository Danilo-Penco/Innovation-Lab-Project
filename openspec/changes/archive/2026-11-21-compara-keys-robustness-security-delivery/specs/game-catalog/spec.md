# Spec Delta

## ADDED Requirements

### Requirement: Responsividade e acessibilidade dos controles do catálogo
O catálogo e o cabeçalho compartilhado SHALL manter seus controles utilizáveis em viewports estreitos, com nome acessível, foco de teclado visível e sem conteúdo cortado ou rolagem horizontal da página. A barra de busca do catálogo SHALL reorganizar o campo e o botão quando não houver largura suficiente para mantê-los lado a lado.

#### Scenario: Busca do catálogo em tela estreita
- **WHEN** uma pessoa abre `/catalogo` em um viewport estreito
- **THEN** o campo “Comparar Preços” e o botão “Buscar” reorganizam-se sem sobreposição, corte ou rolagem horizontal

#### Scenario: Cabeçalho em tela estreita
- **WHEN** uma pessoa abre uma tela com cabeçalho em viewport estreito
- **THEN** a marca e a ação “Entrar” ou “Sair” permanecem visíveis, legíveis e operáveis sem colisão

#### Scenario: Navegação por teclado no catálogo
- **WHEN** uma pessoa navega pelo catálogo usando teclado
- **THEN** os controles interativos têm nome acessível, recebem foco visível e podem ser acionados sem mouse
