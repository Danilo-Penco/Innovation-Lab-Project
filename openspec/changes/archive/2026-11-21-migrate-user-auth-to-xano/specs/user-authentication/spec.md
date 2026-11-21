# Spec Delta

## MODIFIED Requirements

### Requirement: Cadastro com credenciais próprias
O sistema SHALL permitir criar uma conta usando Nome, e-mail e senha pelo endpoint existente `POST auth/signup`, enviando os campos `name`, `email` e `password` para o Xano. O Nome SHALL ser obrigatório. O sistema SHALL normalizar o e-mail removendo espaços externos e ignorando diferenças entre maiúsculas e minúsculas, validar seu formato e exigir senha entre 8 e 128 caracteres com ao menos uma letra. O sistema SHALL rejeitar e-mails já cadastrados sem criar outra conta e SHALL armazenar as contas na tabela `user` do Xano, não no banco da aplicação Reflex. A senha SHALL NOT ser armazenada em texto puro nem mantida no estado da sessão após a resposta.

#### Scenario: Cadastro válido
- **WHEN** a pessoa envia Nome, e-mail válido ainda não cadastrado e senha entre 8 e 128 caracteres que contenha ao menos uma letra
- **THEN** o sistema envia os campos `name`, `email` e `password` a `auth/signup`, guarda o `authToken` retornado na sessão e inicia a transição autenticada para `/catalogo`

#### Scenario: E-mail já cadastrado
- **WHEN** o Xano rejeita o cadastro porque o e-mail já está associado a uma conta
- **THEN** o sistema não cria outra conta e exibe “Este endereço de e-mail já está em uso.”

#### Scenario: Dados de cadastro inválidos
- **WHEN** a pessoa envia Nome ou e-mail vazio/inválido, senha menor que 8 ou maior que 128 caracteres, ou senha sem letras
- **THEN** o sistema rejeita o cadastro antes de iniciar uma sessão, permanece em `/cadastro` e mantém as mensagens atuais “Informe um e-mail válido.” e “A senha deve ter entre 8 e 128 caracteres.”; para o novo campo Nome vazio, informa “Informe seu nome.”

### Requirement: Login por e-mail e senha
O sistema SHALL autenticar e-mail e senha pelo endpoint existente `POST auth/login`, enviando os campos `email` e `password`. O sistema SHALL iniciar uma sessão autenticada somente após obter um `authToken` válido na resposta real documentada pelo Xano. Falhas de autenticação SHALL exibir a mensagem “E-mail ou senha inválidos.” sem revelar se o e-mail ou a senha estão incorretos.

#### Scenario: Login bem-sucedido
- **WHEN** uma pessoa envia credenciais válidas e o Xano retorna um `authToken`
- **THEN** o sistema guarda o token na sessão Reflex e inicia a transição autenticada para `/catalogo`

#### Scenario: Credenciais incorretas
- **WHEN** uma pessoa envia credenciais incorretas ou uma conta inexistente
- **THEN** o sistema não inicia uma sessão, limpa a senha do formulário e exibe “E-mail ou senha inválidos.”

### Requirement: Acesso protegido ao catálogo
O sistema SHALL proteger `/catalogo` no backend Reflex e SHALL permitir sua exibição somente depois de validar o `authToken` da sessão usando o endpoint existente `GET auth/me` e a forma de autenticação por token definida no design real do Xano. O conteúdo do catálogo SHALL seguir a capacidade `game-catalog`.

#### Scenario: Navegação direta sem autenticação
- **WHEN** uma pessoa sem `authToken` de sessão abre diretamente `/catalogo`
- **THEN** o sistema não apresenta o conteúdo protegido e redireciona a pessoa para `/`

#### Scenario: Navegação ao catálogo com sessão
- **WHEN** uma pessoa autenticada abre `/catalogo` e o Xano aceita o token da sessão por `auth/me`
- **THEN** o sistema apresenta o catálogo definido pela capacidade `game-catalog`

#### Scenario: Token validado
- **WHEN** uma pessoa abre `/catalogo` com sessão cujo token é aceito por `auth/me`
- **THEN** o sistema apresenta o catálogo definido pela capacidade `game-catalog`

#### Scenario: Token rejeitado
- **WHEN** `auth/me` rejeita o token da sessão
- **THEN** o sistema limpa o token, não apresenta o catálogo e redireciona a pessoa para `/`

## ADDED Requirements

### Requirement: Indisponibilidade da autenticação Xano
Falhas de conexão, timeout, configuração ausente ou resposta inutilizável dos endpoints de autenticação SHALL ser tratadas sem interromper a tela. O sistema SHALL informar claramente que a autenticação está temporariamente indisponível e SHALL NOT iniciar uma sessão ou liberar `/catalogo` sem uma resposta válida.

#### Scenario: Xano indisponível durante cadastro ou login
- **WHEN** uma chamada de cadastro ou login não consegue obter uma resposta válida do Xano
- **THEN** o sistema permanece na tela atual, não inicia a transição autenticada e apresenta uma mensagem clara de indisponibilidade

#### Scenario: Xano indisponível ao validar o catálogo
- **WHEN** `auth/me` não consegue obter uma resposta válida do Xano
- **THEN** o sistema não libera o catálogo e apresenta uma mensagem recuperável de indisponibilidade sem quebrar a tela
