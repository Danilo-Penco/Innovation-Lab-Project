# Spec Delta

## MODIFIED Requirements

### Requirement: Página inicial de login
O sistema SHALL apresentar a tela de login como primeira página do site, com campos de e-mail e senha, uma ação explícita para entrar e o botão “Cadastrar-se” imediatamente abaixo do campo de senha. A interface de autenticação SHALL usar um fundo com cores preto e roxo e SHALL ser utilizável em telas estreitas e largas. Os formulários de login e cadastro SHALL ficar centralizados na área visível da tela, com espaçamento superior reduzido, sem exigir rolagem vertical em tamanhos comuns de desktop e celular. Ambos SHALL informar que a senha precisa ter no mínimo 8 caracteres e ao menos uma letra, e SHALL oferecer um controle acessível para mostrar ou ocultar o valor digitado, inicialmente oculto.

#### Scenario: Acesso inicial sem sessão
- **WHEN** uma pessoa sem sessão autenticada abre a raiz do site
- **THEN** o sistema apresenta o formulário de login e o botão “Cadastrar-se” abaixo do campo de senha

#### Scenario: Abrir cadastro
- **WHEN** a pessoa seleciona “Cadastrar-se”
- **THEN** o sistema apresenta o formulário de criação de conta com campos de nome, e-mail e senha e uma ação para concluir o cadastro

#### Scenario: Formulário centralizado em desktop
- **WHEN** uma pessoa abre a tela de login ou cadastro em uma janela desktop comum
- **THEN** o formulário aparece centralizado vertical e horizontalmente e fica visível sem rolagem vertical

#### Scenario: Formulário centralizado em celular
- **WHEN** uma pessoa abre a tela de login ou cadastro em uma tela de celular comum
- **THEN** o formulário usa espaçamento compacto, aparece centralizado e fica visível sem rolagem vertical

#### Scenario: Orientação da senha e alternância de visibilidade
- **WHEN** uma pessoa abre o formulário de login ou cadastro
- **THEN** a interface informa a regra de senha e apresenta um botão nomeado para mostrar/ocultar a senha, mantendo-a oculta por padrão e permitindo operar o controle por teclado

### Requirement: Cadastro com credenciais próprias
O sistema SHALL permitir criar uma conta usando Nome, e-mail e senha pelo endpoint existente `POST auth/signup`, enviando os campos `name`, `email` e `password` ao Xano. O Nome SHALL ser obrigatório no formulário e SHALL ser recusado também pelo endpoint quando ausente. O sistema SHALL normalizar o e-mail removendo espaços externos e ignorando diferenças entre maiúsculas e minúsculas, validar seu formato e exigir senha entre 8 e 128 caracteres com ao menos uma letra. O sistema SHALL rejeitar e-mails já cadastrados sem criar outra conta e SHALL armazenar a conta na tabela `user` do Xano, não no banco da aplicação Reflex. A senha SHALL NOT ser armazenada em texto puro nem mantida no estado da sessão após a resposta.

#### Scenario: Cadastro válido
- **WHEN** a pessoa envia Nome, e-mail válido ainda não cadastrado e senha entre 8 e 128 caracteres que contenha ao menos uma letra
- **THEN** o sistema envia os campos `name`, `email` e `password` a `auth/signup`, guarda o `authToken` retornado na sessão server-side e inicia a transição autenticada para `/catalogo`

#### Scenario: Nome obrigatório
- **WHEN** a pessoa envia o cadastro sem Nome ou com Nome composto apenas por espaços
- **THEN** o sistema rejeita o cadastro antes de iniciar uma sessão, informa que o Nome é obrigatório e o endpoint Xano recusa uma chamada sem `name`

#### Scenario: E-mail já cadastrado
- **WHEN** o Xano rejeita o cadastro porque o e-mail já está associado a uma conta
- **THEN** o sistema não cria outra conta e exibe “Este endereço de e-mail já está em uso.”

#### Scenario: Dados de cadastro inválidos
- **WHEN** a pessoa envia e-mail inválido, campos obrigatórios vazios, senha menor que 8 ou maior que 128 caracteres, ou senha sem letras
- **THEN** o sistema rejeita o cadastro, informa o problema e não cria uma sessão nem uma conta inválida

### Requirement: Login por e-mail e senha
O sistema SHALL autenticar e-mail e senha pelo endpoint existente `POST auth/login`, enviando os campos `email` e `password`. A validação local de senha SHALL exigir entre 8 e 128 caracteres e ao menos uma letra. O sistema SHALL iniciar uma sessão autenticada somente após obter um `authToken` válido na resposta Xano. Falhas de autenticação SHALL exibir mensagens próprias e recuperáveis sem revelar se o e-mail ou a senha estão incorretos.

#### Scenario: Login bem-sucedido
- **WHEN** uma pessoa envia credenciais válidas e o Xano retorna um `authToken`
- **THEN** o sistema guarda o token somente na sessão server-side e inicia a transição autenticada para `/catalogo`

#### Scenario: Credenciais incorretas
- **WHEN** uma pessoa envia credenciais incorretas ou uma conta inexistente
- **THEN** o sistema não inicia uma sessão, limpa a senha do formulário e exibe “E-mail ou senha inválidos.”

#### Scenario: Senha inválida localmente
- **WHEN** a pessoa envia uma senha fora da política local
- **THEN** o sistema rejeita a senha antes da chamada Xano e apresenta uma mensagem que identifica a regra violada

### Requirement: Acesso protegido ao catálogo
O sistema SHALL proteger `/catalogo` no backend Reflex e SHALL permitir sua exibição somente depois de validar o `authToken` da sessão usando o endpoint existente `GET auth/me`. O conteúdo do catálogo SHALL seguir a capacidade `game-catalog`. A sessão autenticada SHALL sobreviver a uma recarga da página sem expor o `authToken` a armazenamento acessível por JavaScript; caso o estado de sessão atual não sobreviva, o sistema SHALL usar uma persistência server-side com identificador de sessão em cookie `HttpOnly`, `Secure` em HTTPS e `SameSite` apropriado. Falha de validação SHALL manter o acesso fechado.

#### Scenario: Navegação direta sem autenticação
- **WHEN** uma pessoa sem token de sessão abre diretamente `/catalogo`
- **THEN** o sistema não apresenta o conteúdo protegido e redireciona a pessoa para `/`

#### Scenario: Navegação ao catálogo com sessão
- **WHEN** uma pessoa autenticada abre `/catalogo` e o Xano aceita o token da sessão por `auth/me`
- **THEN** o sistema apresenta o catálogo definido pela capacidade `game-catalog`

#### Scenario: Sessão após recarregar a página
- **WHEN** uma pessoa autenticada recarrega `/catalogo`
- **THEN** o sistema recupera a sessão server-side, valida novamente o token por `auth/me` e apresenta o catálogo sem expor o token ao JavaScript ou a `localStorage`

#### Scenario: Token rejeitado
- **WHEN** `auth/me` rejeita o token da sessão
- **THEN** o sistema limpa a sessão, não apresenta o catálogo e redireciona a pessoa para `/` com um aviso claro de sessão inválida ou expirada

#### Scenario: Xano indisponível ao validar o catálogo
- **WHEN** `auth/me` falha por indisponibilidade de rede ou timeout
- **THEN** o sistema não libera o catálogo e apresenta uma mensagem recuperável que identifica a indisponibilidade

## ADDED Requirements

### Requirement: Chamadas autenticadas e tratamento de erros Xano
Todas as chamadas autenticadas ao Xano SHALL compartilhar um comportamento de requisição consistente e enviar o token no header `Authorization` exatamente como `Bearer <token>`. O cliente SHALL realizar no máximo uma nova tentativa automática somente em erro de rede ou timeout e SHALL NOT repetir respostas HTTP 4xx. Erros conhecidos SHALL ser mapeados a mensagens próprias que identifiquem o motivo sem revelar segredos. Em particular, HTTP 400 com `payload.param=password` SHALL apresentar mensagem própria de política de senha. Erros não reconhecidos SHALL apresentar o status/código Xano sanitizado em vez de uma mensagem genérica que esconda a causa. O sistema SHALL NOT imprimir dados de debug, token ou senha.

#### Scenario: Header Bearer em chamada autenticada
- **WHEN** o sistema envia uma chamada autenticada ao Xano
- **THEN** o header contém `Authorization: Bearer <token>` com o token real e o teste verifica o esquema e o prefixo sem imprimir ou registrar o token

#### Scenario: Retry de falha transitória
- **WHEN** uma chamada ao Xano falha por erro de rede ou timeout na primeira tentativa
- **THEN** o cliente repete a mesma chamada uma única vez e retorna o resultado ou erro específico da tentativa seguinte

#### Scenario: Não repetir erro 4xx
- **WHEN** o Xano responde com qualquer status HTTP 4xx
- **THEN** o cliente não repete a chamada e apresenta a mensagem específica mapeada para o motivo da resposta

#### Scenario: Senha recusada pelo Xano
- **WHEN** o Xano responde HTTP 400 com `payload.param=password`
- **THEN** o sistema apresenta uma mensagem própria sobre a política de senha e não substitui o motivo por indisponibilidade genérica

#### Scenario: Erro Xano não reconhecido
- **WHEN** o Xano retorna erro não reconhecido com status/código
- **THEN** o sistema apresenta uma mensagem segura baseada no status/código sanitizado, sem ocultar a causa em texto genérico e sem expor o payload bruto

#### Scenario: 401 em rota protegida
- **WHEN** uma chamada de validação de sessão para uma rota protegida recebe HTTP 401
- **THEN** o sistema encerra a sessão, não apresenta o conteúdo protegido e redireciona ao login com aviso de sessão inválida ou expirada
