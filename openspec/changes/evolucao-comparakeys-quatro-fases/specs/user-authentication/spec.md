# Spec Delta

## MODIFIED Requirements

### Requirement: Rotas e ações de autenticação
O sistema SHALL apresentar `/` como landing page pública definida pela capacidade `landing-page`. O formulário de login SHALL estar em `/entrar`, com campos de e-mail e senha, uma ação explícita para entrar e o link “Cadastrar” para `/cadastro`. O cadastro SHALL continuar em `/cadastro` e seu botão de envio SHALL manter o texto “Cadastrar-se”. As telas de autenticação SHALL usar o tema preto e roxo e SHALL ser utilizáveis em telas estreitas e largas. Os formulários SHALL permanecer centralizados; somente o cadastro SHALL informar a política de senha de no mínimo 8 caracteres e ao menos uma letra. Ambos SHALL oferecer controle acessível para mostrar ou ocultar a senha, inicialmente oculta.

#### Scenario: Acesso inicial sem sessão
- **WHEN** uma pessoa sem sessão autenticada abre `/`
- **THEN** o sistema apresenta a landing page pública, sem formulário de login

#### Scenario: Abrir login
- **WHEN** uma pessoa sem sessão seleciona “Entrar”
- **THEN** o sistema apresenta o formulário de autenticação em `/entrar`

#### Scenario: Abrir cadastro
- **WHEN** uma pessoa sem sessão seleciona “Cadastrar”
- **THEN** o sistema apresenta o formulário de criação de conta em `/cadastro` com nome, e-mail e senha

#### Scenario: Formulário centralizado em desktop
- **WHEN** uma pessoa abre `/entrar` ou `/cadastro` em uma janela desktop comum
- **THEN** o formulário aparece centralizado vertical e horizontalmente e fica visível sem rolagem vertical

#### Scenario: Formulário centralizado em celular
- **WHEN** uma pessoa abre `/entrar` ou `/cadastro` em uma tela de celular comum
- **THEN** o formulário usa espaçamento compacto, aparece centralizado e fica visível sem rolagem vertical

#### Scenario: Orientação da senha e alternância de visibilidade
- **WHEN** uma pessoa abre o formulário de cadastro
- **THEN** a interface informa a regra de senha e apresenta um botão nomeado para mostrar/ocultar a senha, mantendo-a oculta por padrão e permitindo operar o controle por teclado

#### Scenario: Login sem validação de força
- **WHEN** uma pessoa abre o formulário de login em `/entrar`
- **THEN** a interface omite a regra de senha e apresenta apenas validações para campos vazios e limite máximo de 128 caracteres, sem mínimo ou requisito de letra

### Requirement: Login por e-mail e senha
O sistema SHALL autenticar por `POST auth/login`, validando no formulário apenas e-mail/senha preenchidos e o máximo de 128 caracteres para senha. Senhas curtas ou sem letras SHALL ser enviadas ao cliente Xano. O cliente SHALL manter sua validação existente de formato do e-mail. Erros de credenciais ou entrada no login SHALL exibir “E-mail ou senha inválidos.” sem identificar o campo incorreto; indisponibilidade SHALL manter mensagem própria. A validação de força e a mensagem específica para HTTP 400 com `payload.param=password` SHALL permanecer exclusivas do cadastro.

#### Scenario: Rejeitar campos vazios e senha longa
- **WHEN** a pessoa envia o login com e-mail ou senha vazios, ou senha acima de 128 caracteres
- **THEN** a aplicação rejeita a tentativa antes de chamar o cliente Xano e informa o campo ou limite correspondente

#### Scenario: Enviar senha curta ao cliente Xano
- **WHEN** a pessoa envia e-mail e senha não vazios com senha abaixo de 8 caracteres ou sem letras
- **THEN** o formulário não aplica validação de força e chama o cliente Xano

#### Scenario: Falha de credenciais genérica
- **WHEN** o cliente Xano rejeita as credenciais ou retorna erro de entrada no login
- **THEN** o sistema mostra “E-mail ou senha inválidos.” sem revelar qual campo falhou

### Requirement: Acesso protegido ao catálogo
O sistema SHALL proteger `/catalogo` no backend Reflex e SHALL permitir sua exibição somente depois de validar o `authToken` da sessão usando o endpoint existente `GET auth/me` e a forma de autenticação por token definida no design real do Xano. O conteúdo do catálogo SHALL seguir a capacidade `game-catalog`. A sessão autenticada SHALL sobreviver a uma recarga da página sem expor o `authToken` a armazenamento acessível por JavaScript; caso o estado de sessão atual não sobreviva, o sistema SHALL usar uma persistência server-side com identificador de sessão em cookie `HttpOnly`, `Secure` em HTTPS e `SameSite` apropriado. Falha de validação SHALL manter o acesso fechado.

#### Scenario: Navegação direta sem autenticação
- **WHEN** uma pessoa sem `authToken` de sessão abre diretamente `/catalogo`
- **THEN** o sistema não apresenta o conteúdo protegido e redireciona a pessoa para `/entrar`

#### Scenario: Token validado
- **WHEN** uma pessoa abre `/catalogo` com sessão cujo token é aceito por `auth/me`
- **THEN** o sistema apresenta o catálogo definido pela capacidade `game-catalog`

#### Scenario: Navegação ao catálogo com sessão
- **WHEN** uma pessoa autenticada abre `/catalogo` e o Xano aceita o token da sessão por `auth/me`
- **THEN** o sistema apresenta o catálogo definido pela capacidade `game-catalog`

#### Scenario: Sessão após recarregar a página
- **WHEN** uma pessoa autenticada recarrega `/catalogo`
- **THEN** o sistema recupera a sessão server-side, valida novamente o token por `auth/me` e apresenta o catálogo sem expor o token ao JavaScript ou a `localStorage`

#### Scenario: Token rejeitado
- **WHEN** `auth/me` rejeita o token da sessão
- **THEN** o sistema limpa a sessão, não apresenta o catálogo e redireciona a pessoa para `/entrar` com aviso de sessão inválida ou expirada

#### Scenario: Xano indisponível ao validar o catálogo
- **WHEN** `auth/me` falha por indisponibilidade de rede ou timeout
- **THEN** o sistema não libera o catálogo e apresenta uma mensagem recuperável que identifica a indisponibilidade

### Requirement: Ações da sessão no cabeçalho
O cabeçalho SHALL mostrar “Entrar” somente quando não houver sessão autenticada e SHALL mostrar “Sair” quando houver uma sessão autenticada. Quando houver sessão, SHALL também apresentar links para `/favoritos` e `/historico`. A ação “Entrar” SHALL abrir `/entrar`; “Sair” SHALL encerrar a sessão no backend e retornar a pessoa a `/entrar`.

#### Scenario: Cabeçalho sem sessão
- **WHEN** uma pessoa sem sessão autenticada abre uma tela com cabeçalho
- **THEN** o cabeçalho mostra “Entrar”, não mostra “Sair” e não mostra links de páginas protegidas

#### Scenario: Cabeçalho com sessão
- **WHEN** uma pessoa autenticada abre uma tela com cabeçalho, inclusive `/buscar`
- **THEN** o cabeçalho mostra “Sair” e links para Favoritos e Histórico, sem mostrar “Entrar”

#### Scenario: Abrir login pelo cabeçalho
- **WHEN** uma pessoa sem sessão seleciona “Entrar”
- **THEN** o sistema abre `/entrar`

#### Scenario: Encerrar sessão pelo cabeçalho
- **WHEN** uma pessoa autenticada seleciona “Sair”
- **THEN** o sistema limpa a sessão e retorna a pessoa a `/entrar`

#### Scenario: Encerrar sessão em rota pública
- **WHEN** uma pessoa autenticada seleciona “Sair” enquanto está em `/buscar`
- **THEN** o sistema encerra a sessão, retorna a pessoa a `/entrar` e mantém `/buscar` acessível sem autenticação

### Requirement: Navegação pela marca ComparaKeys
A marca visual “ComparaKeys” SHALL navegar para `/catalogo` quando houver sessão autenticada e para `/` quando não houver sessão. Essa regra SHALL ser respeitada nas telas que exibem a marca, incluindo landing page, login, cadastro, catálogo, busca pública, comparação, histórico e favoritos. Rotas protegidas SHALL continuar validando a sessão no backend.

#### Scenario: Marca para pessoa visitante
- **WHEN** uma pessoa sem sessão seleciona a marca ComparaKeys em uma tela que a apresenta
- **THEN** o sistema navega para `/`

#### Scenario: Marca sem navegação na tela de login
- **WHEN** uma pessoa sem sessão seleciona a marca ComparaKeys em `/entrar`
- **THEN** o sistema navega para `/`, a landing page pública

#### Scenario: Marca para pessoa autenticada
- **WHEN** uma pessoa autenticada seleciona a marca ComparaKeys em uma tela que a apresenta
- **THEN** o sistema navega para `/catalogo`

#### Scenario: Marca no cadastro
- **WHEN** uma pessoa seleciona a marca ComparaKeys em `/cadastro`
- **THEN** o sistema navega para `/` sem sessão ou `/catalogo` com sessão autenticada

#### Scenario: Navegar pelo logo no cadastro
- **WHEN** uma pessoa seleciona a marca ComparaKeys em `/cadastro`
- **THEN** o sistema navega para `/` sem sessão ou `/catalogo` com sessão autenticada

#### Scenario: Navegar pela marca nas telas com cabeçalho
- **WHEN** uma pessoa seleciona a marca ComparaKeys em `/catalogo`, `/buscar` ou na rota de comparação
- **THEN** o sistema navega para `/` sem sessão ou `/catalogo` com sessão autenticada

#### Scenario: Marca nas telas públicas de busca e comparação
- **WHEN** uma pessoa seleciona a marca ComparaKeys em `/buscar` ou `/comparar`
- **THEN** o sistema navega para `/` sem sessão ou `/catalogo` com sessão autenticada

#### Scenario: Proteção do catálogo ao navegar sem sessão
- **WHEN** uma pessoa sem sessão seleciona a marca ComparaKeys em uma rota pública e chega a `/catalogo`
- **THEN** o sistema não apresenta o catálogo protegido e redireciona a pessoa para `/entrar`

#### Scenario: Proteção do catálogo pela marca
- **WHEN** uma pessoa sem sessão tenta abrir `/catalogo` por qualquer link ou URL
- **THEN** o sistema não apresenta o catálogo protegido e redireciona a pessoa para `/entrar`
