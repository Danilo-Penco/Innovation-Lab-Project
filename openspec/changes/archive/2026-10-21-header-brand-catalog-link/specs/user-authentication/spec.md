# Spec Delta

## ADDED Requirements

### Requirement: Navegação pela marca ComparaKeys
A marca visual “ComparaKeys” SHALL navegar para `/catalogo` quando selecionada nas telas que a exibem, incluindo cadastro, catálogo, busca pública e comparação de preços. Na tela de login em `/`, a marca SHALL permanecer como texto e ícone sem link ou ação de navegação. A proteção existente de `/catalogo` SHALL continuar redirecionando para o login uma pessoa sem sessão autenticada.

#### Scenario: Marca sem navegação na tela de login
- **WHEN** uma pessoa abre `/`
- **THEN** a marca ComparaKeys aparece sem link nem ação clicável

#### Scenario: Navegar pelo logo no cadastro
- **WHEN** uma pessoa seleciona a marca ComparaKeys em `/cadastro`
- **THEN** o sistema navega para `/catalogo`

#### Scenario: Navegar pela marca nas telas com cabeçalho
- **WHEN** uma pessoa seleciona a marca ComparaKeys em `/catalogo`, `/buscar` ou na rota de comparação
- **THEN** o sistema navega para `/catalogo`

#### Scenario: Proteção do catálogo ao navegar sem sessão
- **WHEN** uma pessoa sem sessão seleciona a marca ComparaKeys em uma rota pública e chega a `/catalogo`
- **THEN** o sistema não apresenta o catálogo protegido e redireciona a pessoa para `/`
