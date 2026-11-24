# User Authentication Specification

## Purpose

Esta capacidade permite que usuários criem uma conta e entrem no ComparaKeys antes de acessar suas áreas protegidas. O fluxo usa credenciais próprias do sistema, preserva a busca pública Steam como exceção e encaminha sessões autenticadas ao catálogo.

## Requirements

### Requirement: Rotas e ações de autenticação
O sistema SHALL apresentar `/` como landing page pública e o formulário de login em `/entrar`, com campos de e-mail e senha e uma ação explícita para entrar. A tela de login SHALL oferecer a ação “Cadastrar” para abrir `/cadastro`; o formulário de cadastro SHALL manter “Cadastrar-se” no botão de envio. A interface de autenticação SHALL usar um fundo com cores preto e roxo e SHALL ser utilizável em telas estreitas e largas. Os formulários de login e cadastro SHALL ficar centralizados na área visível da tela, com espaçamento superior reduzido, sem exigir rolagem vertical em tamanhos comuns de desktop e celular. Somente o cadastro SHALL informar que a senha precisa ter no mínimo 8 caracteres e ao menos uma letra. Ambos SHALL oferecer um controle acessível para mostrar ou ocultar a senha, inicialmente oculta.

#### Scenario: Acesso inicial sem sessão
- **WHEN** uma pessoa sem sessão autenticada abre a raiz do site
- **THEN** o sistema apresenta a landing page pública sem formulário de login

#### Scenario: Abrir login
- **WHEN** a pessoa seleciona “Entrar”
- **THEN** o sistema apresenta o formulário de login em `/entrar`

#### Scenario: Abrir cadastro
- **WHEN** a pessoa seleciona “Cadastrar”
- **THEN** o sistema apresenta o formulário de criação de conta em `/cadastro` com campos de nome, e-mail e senha e o botão de envio “Cadastrar-se”

#### Scenario: Formulário centralizado em desktop
- **WHEN** uma pessoa abre a tela de login ou cadastro em uma janela desktop comum
- **THEN** o formulário aparece centralizado vertical e horizontalmente e fica visível sem rolagem vertical

#### Scenario: Formulário centralizado em celular
- **WHEN** uma pessoa abre a tela de login ou cadastro em uma tela de celular comum
- **THEN** o formulário usa espaçamento compacto, aparece centralizado e fica visível sem rolagem vertical

#### Scenario: Regra de senha no cadastro
- **WHEN** uma pessoa abre o formulário de cadastro
- **THEN** a interface informa a regra de senha e apresenta um botão nomeado para mostrar/ocultar a senha, mantendo-a oculta por padrão e permitindo operar o controle por teclado

#### Scenario: Login sem orientação de força
- **WHEN** uma pessoa abre o formulário de login
- **THEN** a interface não apresenta a regra de senha do cadastro e oferece o controle acessível para mostrar/ocultar a senha, inicialmente oculta

### Requirement: Cadastro com credenciais próprias
O sistema SHALL permitir criar uma conta usando Nome, e-mail e senha pelo endpoint existente `POST auth/signup`, enviando os campos `name`, `email` e `password` ao Xano. O Nome SHALL ser obrigatório no formulário e SHALL ser recusado também pelo endpoint quando ausente. O sistema SHALL normalizar o e-mail removendo espaços externos e ignorando diferenças entre maiúsculas e minúsculas, validar seu formato e exigir senha entre 8 e 128 caracteres com ao menos uma letra. O sistema SHALL rejeitar e-mails já cadastrados sem criar outra conta e SHALL armazenar a conta na tabela `user` do Xano, não no banco da aplicação Reflex. A senha SHALL NOT ser armazenada em texto puro nem mantida no estado da sessão após a resposta.

#### Scenario: Cadastro válido
- **WHEN** a pessoa envia Nome, e-mail válido ainda não cadastrado e senha entre 8 e 128 caracteres que contenha ao menos uma letra
- **THEN** o sistema envia os campos `name`, `email` e `password` a `auth/signup`, guarda o `authToken` retornado na sessão server-side e inicia a transição autenticada para `/catalogo`

#### Scenario: Nome obrigatório
- **WHEN** a pessoa envia o cadastro sem Nome ou com Nome composto apenas por espaços
- **THEN** o sistema rejeita o cadastro antes de iniciar uma sessão, informa “Informe seu nome.” e o endpoint Xano recusa uma chamada sem `name`

#### Scenario: E-mail já cadastrado
- **WHEN** o Xano rejeita o cadastro porque o e-mail já está associado a uma conta
- **THEN** o sistema não cria outra conta e exibe “Este endereço de e-mail já está em uso.”

#### Scenario: Dados de cadastro inválidos
- **WHEN** a pessoa envia Nome ou e-mail vazio/inválido, senha menor que 8 ou maior que 128 caracteres, ou senha sem letras
- **THEN** o sistema rejeita o cadastro antes de iniciar uma sessão, permanece em `/cadastro` e mantém as mensagens atuais “Informe um e-mail válido.” e “A senha deve ter entre 8 e 128 caracteres.”; para o campo Nome vazio, informa “Informe seu nome.”

### Requirement: Login por e-mail e senha
O sistema SHALL autenticar e-mail e senha pelo endpoint existente `POST auth/login`, enviando os campos `email` e `password`. O formulário SHALL validar que e-mail e senha não estejam vazios e que a senha não exceda 128 caracteres, sem aplicar mínimo ou validação de força; uma senha curta ou sem letras SHALL ser enviada ao Xano. O cliente Xano SHALL manter a normalização e validação de formato de e-mail já existente. Falhas de credenciais ou de entrada retornadas pelo cliente Xano SHALL usar a mensagem genérica “E-mail ou senha inválidos.”, sem indicar qual campo falhou; indisponibilidade SHALL continuar com sua mensagem própria. O tratamento específico HTTP 400 com `payload.param=password` SHALL ser apresentado no cadastro, não no login. O sistema SHALL iniciar uma sessão autenticada somente após obter um `authToken` válido na resposta real documentada pelo Xano.

#### Scenario: Login bem-sucedido
- **WHEN** uma pessoa envia credenciais válidas e o Xano retorna um `authToken`
- **THEN** o sistema guarda o token somente na sessão server-side e inicia a transição autenticada para `/catalogo`

#### Scenario: Credenciais incorretas
- **WHEN** uma pessoa envia credenciais incorretas ou uma conta inexistente
- **THEN** o sistema não inicia uma sessão, limpa a senha do formulário e exibe “E-mail ou senha inválidos.”

#### Scenario: Campos obrigatórios no login
- **WHEN** a pessoa envia o login sem e-mail ou sem senha
- **THEN** o sistema não chama o Xano e informa especificamente que o campo está vazio

#### Scenario: Limite máximo de senha no login
- **WHEN** a pessoa envia uma senha com mais de 128 caracteres
- **THEN** o sistema rejeita a senha antes da chamada Xano e informa o limite máximo

#### Scenario: Senha curta ou sem letras no login
- **WHEN** a pessoa envia e-mail e senha preenchidos e a senha tem menos de 8 caracteres ou não contém letras
- **THEN** o formulário não aplica a política de força local e envia as credenciais ao cliente Xano

#### Scenario: Falha de autenticação sem revelar o campo
- **WHEN** o cliente Xano rejeita as credenciais ou retorna erro de entrada no login
- **THEN** o sistema apresenta “E-mail ou senha inválidos.” sem identificar se o e-mail ou a senha falhou

### Requirement: Acesso protegido ao catálogo
O sistema SHALL proteger `/catalogo` no backend Reflex e SHALL permitir sua exibição somente depois de validar o `authToken` da sessão usando o endpoint existente `GET auth/me` e a forma de autenticação por token definida no design real do Xano. O conteúdo do catálogo SHALL seguir a capacidade `game-catalog`. A sessão autenticada SHALL sobreviver a uma recarga da página sem expor o `authToken` a armazenamento acessível por JavaScript; caso o estado de sessão atual não sobreviva, o sistema SHALL usar uma persistência server-side com identificador de sessão em cookie `HttpOnly`, `Secure` em HTTPS e `SameSite` apropriado. Falha de validação SHALL manter o acesso fechado.

#### Scenario: Navegação direta sem autenticação
- **WHEN** uma pessoa sem `authToken` de sessão abre diretamente `/catalogo`
- **THEN** o sistema não apresenta o conteúdo protegido e redireciona a pessoa para `/`

#### Scenario: Navegação ao catálogo com sessão
- **WHEN** uma pessoa autenticada abre `/catalogo` e o Xano aceita o token da sessão por `auth/me`
- **THEN** o sistema apresenta o catálogo definido pela capacidade `game-catalog`

#### Scenario: Token validado
- **WHEN** uma pessoa abre `/catalogo` com sessão cujo token é aceito por `auth/me`
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

### Requirement: Indisponibilidade da autenticação Xano
Falhas de conexão, timeout, configuração ausente ou resposta inutilizável dos endpoints de autenticação SHALL ser tratadas sem interromper a tela. O sistema SHALL informar claramente que a autenticação está temporariamente indisponível e SHALL NOT iniciar uma sessão ou liberar `/catalogo` sem uma resposta válida.

#### Scenario: Xano indisponível durante cadastro ou login
- **WHEN** uma chamada de cadastro ou login não consegue obter uma resposta válida do Xano
- **THEN** o sistema permanece na tela atual, não inicia a transição autenticada e apresenta uma mensagem clara de indisponibilidade

#### Scenario: Xano indisponível ao validar o catálogo
- **WHEN** `auth/me` não consegue obter uma resposta válida do Xano
- **THEN** o sistema não libera o catálogo e apresenta uma mensagem recuperável de indisponibilidade sem quebrar a tela

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

### Requirement: Chamadas autenticadas e tratamento de erros Xano
Todas as chamadas autenticadas ao Xano SHALL compartilhar um comportamento de requisição consistente e enviar o token no header `Authorization` exatamente como `Bearer <token>`. O cliente SHALL realizar no máximo uma nova tentativa automática somente em erro de rede ou timeout e SHALL NOT repetir respostas HTTP 4xx. Erros conhecidos SHALL ser mapeados a mensagens próprias que identifiquem o motivo sem revelar segredos. Em particular, HTTP 400 com `payload.param=password` SHALL apresentar mensagem própria de política de senha somente no cadastro; no login, falhas de entrada SHALL usar a mensagem genérica “E-mail ou senha inválidos.” Erros não reconhecidos fora do fluxo de credenciais SHALL apresentar o status/código Xano sanitizado em vez de uma mensagem genérica que esconda a causa. O sistema SHALL NOT imprimir dados de debug, token ou senha.

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
- **WHEN** o Xano responde HTTP 400 com `payload.param=password` durante `auth/signup`
- **THEN** o sistema apresenta uma mensagem própria sobre a política de senha e não substitui o motivo por indisponibilidade genérica

#### Scenario: Erro Xano não reconhecido
- **WHEN** o Xano retorna erro não reconhecido com status/código
- **THEN** o sistema apresenta uma mensagem segura baseada no status/código sanitizado, sem ocultar a causa em texto genérico e sem expor o payload bruto

#### Scenario: 401 em rota protegida
- **WHEN** uma chamada de validação de sessão para uma rota protegida recebe HTTP 401
- **THEN** o sistema encerra a sessão, não apresenta o conteúdo protegido e redireciona ao login com aviso de sessão inválida ou expirada
