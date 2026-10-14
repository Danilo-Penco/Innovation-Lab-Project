# Spec Delta

## MODIFIED Requirements

### Requirement: Acesso protegido ao catálogo
O sistema SHALL proteger a página de catálogo no backend Reflex e SHALL permitir sua exibição somente a uma sessão autenticada. O conteúdo do catálogo SHALL seguir a capacidade `game-catalog`.

#### Scenario: Navegação direta sem autenticação
- **WHEN** uma pessoa sem sessão abre diretamente a rota do catálogo
- **THEN** o sistema não apresenta o conteúdo protegido e redireciona a pessoa para a página de login

#### Scenario: Navegação ao catálogo com sessão
- **WHEN** uma pessoa autenticada abre a rota do catálogo
- **THEN** o sistema apresenta o catálogo definido pela capacidade `game-catalog`
