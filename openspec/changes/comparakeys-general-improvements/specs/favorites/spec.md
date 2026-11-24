# Spec Delta

## Purpose

Esta capacidade permite que cada pessoa autenticada mantenha uma lista privada de jogos favoritos e os retome pelo catálogo, pela comparação ou por uma página dedicada.

## ADDED Requirements

### Requirement: Gerenciar favoritos do próprio usuário
O sistema SHALL permitir listar favoritos por `GET /favorites`, adicionar por `POST /favorites` com `{steam_app_id, game_name, cover_url}` e remover por `DELETE /favorites/{steam_app_id}`. Todas as rotas SHALL exigir `Authorization: Bearer <token>` no grupo Authentication e usar o `XANO_API_URL` existente. O Xano SHALL associar cada item exclusivamente a `$auth.id`, impor unicidade por usuário e Steam App ID e NOT confiar em `user_id` do cliente. Cada favorito SHALL conter `{id, steam_app_id, game_name, cover_url, created_at}`. Inclusão repetida SHALL retornar o favorito existente com HTTP 200; remoção própria SHALL responder `{"deleted": true}`.

#### Scenario: Adicionar favorito
- **WHEN** uma pessoa autenticada adiciona um jogo válido
- **THEN** `POST /favorites` associa o favorito a `$auth.id` e retorna o objeto do favorito sem criar duplicata

#### Scenario: Inclusão idempotente
- **WHEN** a pessoa envia novamente o mesmo Steam App ID
- **THEN** o endpoint retorna o objeto existente com HTTP 200

#### Scenario: Remover favorito
- **WHEN** uma pessoa autenticada remove um favorito próprio
- **THEN** o Xano remove somente a combinação de usuário e Steam App ID vinculada a `$auth.id` e responde `{"deleted": true}`

#### Scenario: Isolamento entre usuários
- **WHEN** uma pessoa autenticada lista, adiciona ou remove favoritos
- **THEN** ela só pode consultar ou alterar itens próprios

#### Scenario: Requisição sem autenticação
- **WHEN** uma chamada de listagem, inclusão ou remoção não contém token válido
- **THEN** o endpoint responde HTTP 401 e não altera favoritos

### Requirement: Controles de favorito acessíveis e carregados em lote
Na comparação e nos cards do catálogo, o sistema SHALL apresentar um botão de favorito com `aria-label` que indique se o jogo está ou não favoritado. Para pessoas autenticadas, o estado SHALL refletir a lista do usuário e atualizar após inclusão ou remoção. A lista necessária para representar vários cards SHALL ser carregada no máximo uma vez por visita à página, nunca uma vez por card. Visitantes que acionam o controle SHALL ser encaminhados a `/entrar` sem chamada de escrita.

#### Scenario: Alternar favorito autenticado
- **WHEN** uma pessoa autenticada aciona o botão de favorito
- **THEN** o sistema chama a operação de inclusão ou remoção daquele Steam App ID e atualiza o estado apresentado

#### Scenario: Nome acessível
- **WHEN** um botão de favorito é apresentado
- **THEN** seu `aria-label` informa “Adicionar aos favoritos” ou “Remover dos favoritos” de acordo com o estado

#### Scenario: Visitante aciona favorito
- **WHEN** uma pessoa sem sessão aciona um botão de favorito
- **THEN** o sistema não envia uma chamada de escrita e encaminha a pessoa para `/entrar`

#### Scenario: Lista de favoritos para vários cards
- **WHEN** uma página contém vários cards com botões de favorito
- **THEN** o sistema chama `GET /favorites` uma vez para a página, sem chamadas por card

### Requirement: Página protegida de favoritos
O sistema SHALL oferecer `/favoritos` somente a pessoas autenticadas. A página SHALL apresentar capa, nome, link para a comparação correspondente, botão acessível de remoção e estado vazio orientativo. A lista SHALL ser obtida em uma única chamada de leitura por visita.

#### Scenario: Listar favoritos
- **WHEN** uma pessoa autenticada abre `/favoritos`
- **THEN** a página apresenta somente seus favoritos com link para `/comparar?app_id=<steam_app_id>` e ação de remoção

#### Scenario: Lista vazia
- **WHEN** a pessoa autenticada não tem favoritos
- **THEN** a página orienta a pessoa a favoritar um jogo

#### Scenario: Acesso sem autenticação
- **WHEN** uma pessoa sem sessão abre `/favoritos`
- **THEN** o sistema não apresenta dados e encaminha a pessoa para `/entrar`
