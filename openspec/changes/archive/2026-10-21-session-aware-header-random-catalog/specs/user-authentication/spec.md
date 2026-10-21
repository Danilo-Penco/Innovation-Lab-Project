# Spec Delta

## ADDED Requirements

### Requirement: Ações da sessão no cabeçalho
O cabeçalho SHALL mostrar “Entrar” somente quando não houver sessão autenticada e SHALL mostrar “Sair” quando houver uma sessão autenticada. Essa regra SHALL ser respeitada também nas rotas públicas que exibem o cabeçalho, incluindo `/buscar`. A ação “Sair” SHALL encerrar a sessão no backend e retornar a pessoa à página de login.

#### Scenario: Cabeçalho sem sessão
- **WHEN** uma pessoa sem sessão autenticada abre uma tela que apresenta o cabeçalho
- **THEN** o cabeçalho mostra “Entrar” e não mostra “Sair”

#### Scenario: Cabeçalho com sessão
- **WHEN** uma pessoa autenticada abre uma tela que apresenta o cabeçalho, inclusive `/buscar`
- **THEN** o cabeçalho mostra “Sair” e não mostra “Entrar”

#### Scenario: Encerrar sessão pelo cabeçalho
- **WHEN** uma pessoa autenticada seleciona “Sair”
- **THEN** o sistema invalida a identidade autenticada e retorna à tela de login

#### Scenario: Encerrar sessão em rota pública
- **WHEN** uma pessoa autenticada seleciona “Sair” enquanto está em `/buscar`
- **THEN** o sistema encerra a sessão, retorna à tela de login e mantém `/buscar` acessível sem autenticação
