# Spec Delta

## Purpose

Esta capacidade permite que pessoas criem uma conta e façam login no ComparaKeys, e que operações administrativas sejam autorizadas no backend conforme o papel do usuário autenticado.

## ADDED Requirements

### Requirement: Cadastro de usuário
O sistema SHALL permitir que uma pessoa crie uma conta informando nome, e-mail e senha. O sistema SHALL rejeitar um e-mail já cadastrado e SHALL atribuir o papel `usuario` a toda conta criada pelo fluxo público de cadastro.

#### Scenario: Cadastro válido
- **WHEN** uma pessoa envia nome, e-mail ainda não cadastrado e senha válida
- **THEN** o sistema cria a conta com o papel `usuario` e não expõe a senha na resposta

#### Scenario: E-mail já cadastrado
- **WHEN** uma pessoa tenta cadastrar um e-mail que já pertence a uma conta
- **THEN** o sistema rejeita o cadastro e não cria uma segunda conta para esse e-mail

#### Scenario: Tentativa de escolher papel privilegiado
- **WHEN** uma pessoa envia `admin` ou outro papel no cadastro público
- **THEN** o sistema ignora ou rejeita o papel informado e a conta não recebe privilégios administrativos

### Requirement: Login de usuário
O sistema SHALL autenticar uma conta por e-mail e senha e fornecer credenciais de sessão aceitas pelas operações protegidas. Credenciais inválidas SHALL ser rejeitadas sem revelar se o e-mail ou a senha foi o dado incorreto.

#### Scenario: Login válido
- **WHEN** uma conta envia seu e-mail e senha corretos
- **THEN** o sistema autentica a conta e retorna credenciais utilizáveis nas operações protegidas

#### Scenario: Credenciais inválidas
- **WHEN** uma conta envia e-mail inexistente ou senha incorreta
- **THEN** o sistema rejeita o login com uma resposta que não distingue qual dado falhou

### Requirement: Autenticação nas operações protegidas
O sistema SHALL rejeitar no backend chamadas não autenticadas às funcionalidades que exigem login, independentemente do estado ou dos controles exibidos no frontend.

#### Scenario: Usuário não autenticado acessa operação protegida
- **WHEN** uma chamada sem credenciais válidas invoca uma operação que exige login
- **THEN** o backend rejeita a chamada sem executar a operação protegida

#### Scenario: Usuário autenticado acessa funcionalidade protegida
- **WHEN** uma chamada apresenta credenciais válidas para uma conta ativa
- **THEN** o backend reconhece a identidade da conta e aplica as permissões correspondentes ao seu papel

### Requirement: Autorização da aprovação de solicitações de loja
O sistema SHALL permitir a aprovação de uma solicitação de loja somente quando a identidade autenticada tiver o papel `admin`. O backend SHALL verificar essa autorização em toda operação de aprovação.

#### Scenario: Administrador aprova solicitação
- **WHEN** uma conta autenticada com papel `admin` aprova uma solicitação de loja
- **THEN** o backend autoriza a operação

#### Scenario: Usuário comum tenta aprovar solicitação
- **WHEN** uma conta autenticada com papel `usuario` tenta aprovar uma solicitação de loja
- **THEN** o backend rejeita a operação e mantém a solicitação sem aprovação

#### Scenario: Chamada não autenticada tenta aprovar solicitação
- **WHEN** uma chamada sem credenciais válidas tenta aprovar uma solicitação de loja
- **THEN** o backend rejeita a operação e mantém a solicitação sem aprovação

### Requirement: Provisionamento de administradores
O sistema SHALL permitir que a atribuição inicial do papel `admin` seja realizada manualmente por um operador autorizado no Xano. O fluxo público de cadastro SHALL NOT permitir autoelevação para `admin`.

#### Scenario: Conta promovida no Xano
- **WHEN** um operador autorizado altera o papel de uma conta para `admin` no Xano
- **THEN** chamadas autenticadas dessa conta recebem as permissões administrativas definidas pelo backend
