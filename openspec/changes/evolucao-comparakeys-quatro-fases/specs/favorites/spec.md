# Spec Delta

## Purpose

Esta capacidade permite que cada usuário mantenha uma lista privada de jogos favoritos e os retome a partir do catálogo ou de uma página dedicada.

## ADDED Requirements

### Requirement: Gerenciar favoritos do próprio usuário
O sistema SHALL permitir que pessoas autenticadas listem favoritos por `GET /favorites`, adicionem por `POST /favorites` com `{steam_app_id, game_name, cover_url}` e removam por `DELETE /favorites/{steam_app_id}`. As rotas SHALL pertencer ao grupo Authentication e usar o mesmo `XANO_API_URL`; todas SHALL exigir `Authorization: Bearer <token>`. O Xano SHALL associar cada favorito ao usuário do token (`$auth.id`), SHALL impor unicidade por usuário e Steam App ID e SHALL NOT confiar em `user_id` enviado pelo cliente. Um favorito SHALL conter `{id, steam_app_id, game_name, cover_url, created_at}`. `GET /favorites` SHALL responder com um array desses objetos. `POST /favorites` SHALL responder com o objeto favorito; se ele já existir, SHALL devolver o objeto existente com HTTP 200 sem criar duplicata. `DELETE /favorites/{steam_app_id}` SHALL responder `{"deleted": true}` ao remover o favorito próprio.

#### Scenario: Adicionar favorito
- **WHEN** uma pessoa autenticada adiciona um jogo válido
- **THEN** `POST /favorites` associa o favorito ao `$auth.id` e retorna o objeto criado; não cria uma segunda linha para a mesma combinação de usuário e Steam App ID

#### Scenario: Inclusão idempotente
- **WHEN** uma pessoa autenticada envia `POST /favorites` para um Steam App ID que já está nos próprios favoritos
- **THEN** o endpoint responde HTTP 200 com o objeto existente e não cria outra linha

#### Scenario: Remover favorito
- **WHEN** uma pessoa autenticada remove um favorito próprio
- **THEN** `DELETE /favorites/{steam_app_id}` remove somente a combinação de usuário e Steam App ID vinculada ao `$auth.id` e responde `{"deleted": true}`

#### Scenario: Isolamento de favoritos
- **WHEN** uma pessoa autenticada lista ou altera favoritos
- **THEN** ela só pode ver, adicionar ou remover favoritos próprios, mesmo que envie um identificador de outro usuário

#### Scenario: Requisição sem autenticação
- **WHEN** uma requisição de listagem, inclusão ou remoção não contém um token válido
- **THEN** o endpoint recusa a operação com HTTP 401 e não altera favoritos

### Requirement: Controles de favorito acessíveis
Na comparação e nos cards do catálogo, o sistema SHALL apresentar um botão de coração com `aria-label` que indique se o jogo está ou não nos favoritos. Para pessoas autenticadas, o estado preenchido SHALL refletir a lista do usuário e uma ação de inclusão/remoção SHALL atualizar o estado apresentado. A lista necessária para pintar os controles SHALL ser carregada no máximo uma vez por visita à página, nunca uma vez por card. Uma pessoa visitante que aciona um coração SHALL ser encaminhada a `/entrar`.

#### Scenario: Alternar favorito autenticado
- **WHEN** uma pessoa autenticada aciona o coração de um jogo
- **THEN** o sistema chama o endpoint de inclusão ou remoção para aquele jogo e atualiza o estado do botão após o resultado

#### Scenario: Nome acessível do coração
- **WHEN** um controle de favorito é apresentado
- **THEN** seu `aria-label` informa “Adicionar aos favoritos” ou “Remover dos favoritos” de acordo com o estado atual

#### Scenario: Visitante aciona favorito
- **WHEN** uma pessoa sem sessão aciona um botão de coração
- **THEN** o sistema não envia uma chamada de escrita ao Xano e navega para `/entrar`

#### Scenario: Carregar estado de vários cards
- **WHEN** uma página contém vários cards com corações
- **THEN** o sistema chama `GET /favorites` uma vez por visita para todos os cards e não executa uma chamada de leitura por card

#### Scenario: Estado favorito na comparação
- **WHEN** uma pessoa autenticada abre uma comparação que apresenta o coração do jogo
- **THEN** o sistema chama `GET /favorites` uma vez para determinar se o Steam App ID da comparação já está na lista

#### Scenario: Carregamento composto do catálogo na F4
- **WHEN** uma pessoa autenticada visita `/catalogo` na F4
- **THEN** o sistema chama `GET /history` uma vez para os recentes e `GET /favorites` uma vez para o estado dos corações, sem chamadas por card

#### Scenario: Abertura autenticada de comparação na F4
- **WHEN** uma pessoa autenticada abre uma comparação na F4
- **THEN** o sistema chama `POST /history` uma vez para registrar a comparação e `GET /favorites` uma vez para o estado do coração, sem alterar os formatos de resposta dos endpoints

### Requirement: Página protegida de favoritos
O sistema SHALL oferecer `/favoritos` somente a pessoas autenticadas. A página SHALL mostrar capa, nome do jogo vinculado à comparação correspondente, botão acessível para remover e um estado vazio orientativo. A navegação para a página SHALL carregar a lista do usuário em uma única consulta.

#### Scenario: Listar favoritos
- **WHEN** uma pessoa autenticada abre `/favoritos`
- **THEN** o sistema apresenta somente seus favoritos com capa, nome, link para `/comparar?app_id=<steam_app_id>` e ação de remoção

#### Scenario: Lista vazia
- **WHEN** a pessoa autenticada não possui favoritos
- **THEN** a página apresenta orientação para favoritar um jogo

#### Scenario: Rota protegida sem sessão
- **WHEN** uma pessoa sem sessão abre `/favoritos`
- **THEN** o sistema não apresenta dados e redireciona a pessoa para `/entrar`

### Requirement: Header Bearer em todas as chamadas de favoritos
Cada chamada Reflex para `GET /favorites`, `POST /favorites` e `DELETE /favorites/{steam_app_id}` SHALL enviar `Authorization: Bearer <token>` usando o token da sessão autenticada. Testes SHALL verificar o header em cada método/rota sem expor o valor do token em saída ou logs.

#### Scenario: Header Bearer em todas as operações de favoritos
- **WHEN** os testes exercitam listagem, inclusão e remoção com uma sessão autenticada
- **THEN** cada requisição contém exatamente o esquema `Authorization: Bearer <token>` e nenhuma requisição inclui `user_id` como identidade
