# User Authentication Specification

## Purpose

Esta capacidade permite que usuários criem uma conta e entrem no ComparaKeys antes de acessar suas áreas protegidas. O fluxo usa credenciais próprias do sistema, preserva a busca pública Steam como exceção e encaminha sessões autenticadas ao catálogo.

## Requirements

### Requirement: Página inicial de login
O sistema SHALL apresentar a tela de login como primeira página do site, com campos de e-mail e senha, uma ação explícita para entrar e o botão “Cadastrar-se” imediatamente abaixo do campo de senha. A interface de autenticação SHALL usar um fundo com cores preto e roxo e SHALL ser utilizável em telas estreitas e largas. Os formulários de login e cadastro SHALL ficar centralizados na área visível da tela, com espaçamento superior reduzido, sem exigir rolagem vertical em tamanhos comuns de desktop e celular.

#### Scenario: Acesso inicial sem sessão
- **WHEN** uma pessoa sem sessão autenticada abre a raiz do site
- **THEN** o sistema apresenta o formulário de login e o botão “Cadastrar-se” abaixo do campo de senha

#### Scenario: Abrir cadastro
- **WHEN** a pessoa seleciona “Cadastrar-se”
- **THEN** o sistema apresenta o formulário de criação de conta com campos de e-mail e senha e uma ação para concluir o cadastro

#### Scenario: Formulário centralizado em desktop
- **WHEN** uma pessoa abre a tela de login ou cadastro em uma janela desktop comum
- **THEN** o formulário aparece centralizado vertical e horizontalmente e fica visível sem rolagem vertical

#### Scenario: Formulário centralizado em celular
- **WHEN** uma pessoa abre a tela de login ou cadastro em uma tela de celular comum
- **THEN** o formulário usa espaçamento compacto, aparece centralizado e fica visível sem rolagem vertical

### Requirement: Cadastro com credenciais próprias
O sistema SHALL permitir criar uma conta usando e-mail e senha, normalizar o e-mail removendo espaços externos e ignorando diferenças entre maiúsculas e minúsculas, validar seu formato e exigir senha entre 8 e 128 caracteres. O sistema SHALL rejeitar e-mails normalizados já cadastrados e armazenar a conta no banco de dados próprio da aplicação Reflex. O sistema SHALL NOT enviar credenciais ao Xano nem armazenar a senha em texto puro.

#### Scenario: Cadastro válido
- **WHEN** a pessoa envia um e-mail válido ainda não cadastrado e uma senha entre 8 e 128 caracteres
- **THEN** o sistema cria a conta e inicia uma sessão autenticada para essa pessoa

#### Scenario: E-mail já cadastrado
- **WHEN** a pessoa tenta cadastrar um e-mail que, após normalização, já possui uma conta
- **THEN** o sistema não cria uma segunda conta e informa que o endereço já está em uso

#### Scenario: Dados de cadastro inválidos
- **WHEN** a pessoa envia e-mail inválido, campos obrigatórios vazios ou senha menor que 8 ou maior que 128 caracteres
- **THEN** o sistema rejeita o cadastro, informa o problema e não cria a conta

### Requirement: Login por e-mail e senha
O sistema SHALL autenticar as credenciais no backend da aplicação Reflex e SHALL iniciar uma sessão autenticada somente após validar uma conta existente. Falhas de autenticação SHALL exibir uma mensagem recuperável sem revelar se o e-mail ou a senha estão incorretos.

#### Scenario: Login bem-sucedido
- **WHEN** uma pessoa envia e-mail e senha correspondentes a uma conta cadastrada
- **THEN** o sistema inicia uma sessão autenticada para a conta

#### Scenario: Credenciais incorretas
- **WHEN** uma pessoa envia credenciais incorretas ou uma conta inexistente
- **THEN** o sistema não inicia uma sessão e exibe uma mensagem genérica de falha de autenticação

### Requirement: Acesso protegido ao catálogo
O sistema SHALL proteger a página de catálogo no backend Reflex e SHALL permitir sua exibição somente a uma sessão autenticada. O conteúdo do catálogo SHALL seguir a capacidade `game-catalog`.

#### Scenario: Navegação direta sem autenticação
- **WHEN** uma pessoa sem sessão abre diretamente a rota do catálogo
- **THEN** o sistema não apresenta o conteúdo protegido e redireciona a pessoa para a página de login

#### Scenario: Navegação ao catálogo com sessão
- **WHEN** uma pessoa autenticada abre a rota do catálogo
- **THEN** o sistema apresenta o catálogo definido pela capacidade `game-catalog`

### Requirement: Splash screen após autenticação
Após um login ou cadastro bem-sucedido, o sistema SHALL apresentar uma splash screen breve com identidade visual preta e roxa e SHALL encaminhar a sessão autenticada para a rota do catálogo. Falhas de login ou cadastro SHALL permanecer no formulário e SHALL NOT iniciar o redirecionamento.

#### Scenario: Transição após login bem-sucedido
- **WHEN** o login é concluído com sucesso
- **THEN** a splash screen aparece brevemente e o sistema redireciona a pessoa autenticada para o catálogo

#### Scenario: Transição após cadastro bem-sucedido
- **WHEN** o cadastro é concluído com sucesso
- **THEN** a splash screen aparece brevemente e o sistema redireciona a pessoa autenticada para o catálogo

#### Scenario: Falha não inicia a transição
- **WHEN** o login ou o cadastro falha na validação ou autenticação
- **THEN** o formulário permanece visível com uma mensagem de erro e não há redirecionamento ao catálogo

### Requirement: Preservação da busca pública Steam
A busca pública de jogos e preços Steam SHALL permanecer acessível em rota própria sem autenticação, mesmo com a página inicial dedicada ao login. O fluxo de autenticação SHALL NOT exigir sessão para consultar essa rota pública.

#### Scenario: Acessar busca sem sessão
- **WHEN** uma pessoa sem autenticação abre a rota própria de busca Steam
- **THEN** o sistema permite pesquisar jogos e consultar preços conforme a capacidade `steam-price-search`

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
