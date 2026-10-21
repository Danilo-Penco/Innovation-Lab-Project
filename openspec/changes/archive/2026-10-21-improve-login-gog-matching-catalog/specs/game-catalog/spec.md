# Spec Delta

## ADDED Requirements

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
