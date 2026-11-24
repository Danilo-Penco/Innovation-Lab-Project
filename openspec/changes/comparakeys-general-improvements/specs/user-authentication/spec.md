# Spec Delta

## MODIFIED Requirements

### Requirement: Acesso protegido ao catálogo
O sistema SHALL proteger `/catalogo`, `/historico` e `/favoritos` no backend Reflex e SHALL permitir a exibição de dados protegidos somente depois de validar o `authToken` da sessão usando o endpoint existente `GET auth/me` e a forma de autenticação por token definida no contrato real do Xano. O conteúdo do catálogo SHALL seguir `game-catalog`; histórico e favoritos SHALL apresentar somente dados autorizados pelo próprio Xano para `$auth.id`. A sessão autenticada SHALL sobreviver a uma recarga sem expor o `authToken` a armazenamento acessível por JavaScript; caso o estado de sessão atual não sobreviva, o sistema SHALL usar persistência server-side com identificador de sessão em cookie `HttpOnly`, `Secure` em HTTPS e `SameSite` apropriado. Falha de validação SHALL manter o acesso fechado, limpar a sessão em HTTP 401 e encaminhar a pessoa para `/entrar` com aviso de sessão inválida ou expirada.

#### Scenario: Navegação direta sem autenticação
- **WHEN** uma pessoa sem `authToken` abre `/catalogo`, `/historico` ou `/favoritos`
- **THEN** o sistema não apresenta dados protegidos e encaminha a pessoa para `/entrar`

#### Scenario: Navegação ao catálogo com sessão
- **WHEN** uma pessoa autenticada abre `/catalogo` e o Xano aceita o token por `auth/me`
- **THEN** o sistema apresenta o catálogo definido pela capacidade `game-catalog`

#### Scenario: Token validado
- **WHEN** uma pessoa abre uma rota protegida com sessão cujo token é aceito por `auth/me`
- **THEN** o sistema apresenta somente o conteúdo autorizado para aquela rota

#### Scenario: Histórico ou favoritos com sessão válida
- **WHEN** uma pessoa autenticada abre `/historico` ou `/favoritos`
- **THEN** o sistema valida a sessão no backend e apresenta somente os dados associados pelo Xano ao `$auth.id`

#### Scenario: Sessão após recarregar a página
- **WHEN** uma pessoa autenticada recarrega uma rota protegida
- **THEN** o sistema recupera a sessão server-side, valida novamente o token por `auth/me` e não expõe o token ao JavaScript ou a `localStorage`

#### Scenario: Token rejeitado
- **WHEN** `auth/me` rejeita o token da sessão
- **THEN** o sistema limpa a sessão, não apresenta dados protegidos e encaminha a pessoa para `/entrar` com aviso claro de sessão inválida ou expirada

#### Scenario: Xano indisponível ao validar o catálogo
- **WHEN** `auth/me` falha por rede ou timeout
- **THEN** o sistema não libera dados protegidos e apresenta uma mensagem recuperável de indisponibilidade

## ADDED Requirements

### Requirement: Validação acessível e consistente dos formulários
Os formulários de login e cadastro SHALL validar os campos obrigatórios e seus limites antes da chamada Xano, exibir a mensagem junto ao campo correspondente e associá-la programaticamente ao controle. Erros SHALL ser anunciáveis por tecnologia assistiva; campos inválidos SHALL ser identificados sem depender apenas de cor. A validação do cliente SHALL permanecer consistente com o contrato Xano, e mensagens de login SHALL NOT revelar se e-mail ou senha foram a causa da rejeição.

#### Scenario: Campo obrigatório inválido
- **WHEN** uma pessoa envia login ou cadastro com campo obrigatório vazio ou inválido
- **THEN** o sistema não inicia a chamada Xano, identifica o campo e anuncia a mensagem específica associada a ele

#### Scenario: Erro retornado pelo Xano
- **WHEN** o Xano rejeita cadastro ou login
- **THEN** o sistema apresenta a mensagem segura correspondente, associada ao formulário, sem expor payload bruto, token ou senha

#### Scenario: Erro de credenciais no login
- **WHEN** o Xano rejeita as credenciais de login
- **THEN** a interface mostra mensagem genérica sem identificar qual credencial falhou

### Requirement: Sessão protegida em novas páginas autenticadas
Toda página nova que apresentar histórico, favoritos ou outros dados de conta SHALL ser protegida no backend, exigir validação da sessão e receber dados próprios exclusivamente de endpoints autenticados. A interface SHALL NOT tratar ocultação de links como autorização nem aceitar um identificador de usuário enviado pelo cliente como prova de propriedade.

#### Scenario: Usuário tenta acessar dados de outra conta
- **WHEN** uma pessoa autenticada tenta solicitar histórico ou favoritos de outro usuário
- **THEN** o backend retorna somente dados de `$auth.id` e ignora qualquer identidade fornecida pelo cliente

#### Scenario: Sessão expira durante uso
- **WHEN** uma chamada a endpoint protegido retorna HTTP 401
- **THEN** o sistema encerra a sessão, remove conteúdo protegido e encaminha a pessoa para `/entrar` com aviso
