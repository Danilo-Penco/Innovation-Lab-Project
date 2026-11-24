# Spec Delta

## Purpose

Esta capacidade permite que pessoas autenticadas retomem jogos comparados recentemente sem armazenar preços, enquanto visitantes continuam podendo pesquisar e comparar sem criar histórico.

## ADDED Requirements

### Requirement: Registrar histórico de comparações do próprio usuário
O sistema SHALL registrar um item de histórico somente quando uma pessoa autenticada abre uma comparação, usando `POST /history` no grupo Authentication e o mesmo `XANO_API_URL` existente. O corpo SHALL conter somente `term`, `steam_app_id` e `game_name`; a resposta SHALL ser `{"id": N}`. O endpoint SHALL derivar o proprietário exclusivamente de `$auth.id`; o cliente SHALL NOT enviar `user_id` nem gravar buscas por digitação, preços ou visitas de pessoas sem sessão. O item SHALL conter termo, Steam App ID, nome do jogo e data de criação. Se o jogo aberto for igual ao item mais recente do mesmo usuário, o sistema SHALL atualizar esse item em vez de criar uma duplicata consecutiva.

#### Scenario: Pessoa autenticada abre comparação
- **WHEN** uma pessoa autenticada abre uma comparação válida
- **THEN** o sistema envia `POST /history` com `term`, `steam_app_id` e `game_name`, recebe `{"id": N}` e o Xano associa o registro a `$auth.id`

#### Scenario: Visitante abre comparação
- **WHEN** uma pessoa sem sessão abre uma comparação pública
- **THEN** a comparação continua disponível e nenhum histórico é gravado

#### Scenario: Mesmo jogo aberto consecutivamente
- **WHEN** a pessoa autenticada abre novamente o mesmo Steam App ID que está no topo do próprio histórico
- **THEN** o endpoint atualiza o registro mais recente sem inserir uma duplicata consecutiva

#### Scenario: Digitação não gera histórico
- **WHEN** uma pessoa altera o termo na busca sem abrir uma comparação
- **THEN** nenhum registro de histórico é enviado ao Xano

### Requirement: Listar e limpar somente o histórico próprio
Uma pessoa autenticada SHALL poder listar os 20 itens mais recentes do próprio histórico em ordem decrescente de data por `GET /history` e limpar somente seus próprios registros por `DELETE /history`. A listagem SHALL ser um array de `{id, term, steam_app_id, game_name, created_at}` e a limpeza SHALL responder `{"deleted": N}`. Ambos os endpoints pertencem ao grupo Authentication e usam o mesmo `XANO_API_URL`; o Xano SHALL determinar o proprietário pelo token em todas as operações. Identificadores de usuário fornecidos pelo cliente SHALL NOT ampliar o acesso.

#### Scenario: Listar histórico
- **WHEN** uma pessoa autenticada abre `/historico`
- **THEN** o sistema chama `GET /history` e apresenta os 20 registros mais recentes vinculados ao `$auth.id`, em ordem do mais recente para o mais antigo

#### Scenario: Isolamento entre usuários
- **WHEN** uma pessoa autenticada solicita seu histórico
- **THEN** a resposta não contém registros associados a outro usuário, mesmo que o cliente envie um identificador de terceiro

#### Scenario: Limpar histórico próprio
- **WHEN** a pessoa confirma “Limpar histórico”
- **THEN** o sistema chama `DELETE /history`, recebe `{"deleted": N}`, remove somente os registros associados ao `$auth.id` e atualiza a tela para o estado vazio

#### Scenario: Histórico vazio
- **WHEN** a pessoa autenticada ainda não abriu uma comparação ou já limpou seu histórico
- **THEN** `/historico` apresenta orientação para pesquisar e comparar um jogo, sem erro

### Requirement: Página de histórico e atalhos recentes
O sistema SHALL oferecer a página protegida `/historico`, com nomes de jogos que abrem a comparação correspondente, ação “Limpar histórico” com confirmação e estado vazio orientativo. O catálogo protegido SHALL apresentar até cinco itens recentes, carregados em uma única consulta por visita, com cada item abrindo a comparação do jogo.

#### Scenario: Retomar jogo no histórico
- **WHEN** a pessoa seleciona um item de `/historico` ou “Buscados recentemente” no catálogo
- **THEN** o sistema abre `/comparar?app_id=<steam_app_id>` para o jogo selecionado

#### Scenario: Confirmar limpeza
- **WHEN** a pessoa seleciona “Limpar histórico”
- **THEN** o sistema pede confirmação antes de chamar o endpoint de limpeza

#### Scenario: Carregar recentes no catálogo
- **WHEN** uma pessoa autenticada visita `/catalogo`
- **THEN** o sistema chama `GET /history` para receber os últimos 20 registros e apresenta os cinco mais recentes, sem uma chamada por card

### Requirement: Autorização Bearer nas chamadas de histórico
Cada chamada Reflex para `POST /history`, `GET /history` e `DELETE /history` SHALL enviar o header `Authorization: Bearer <token>` usando o token da sessão autenticada. Testes SHALL verificar o header em cada método/rota sem expor o valor do token em saída ou logs.

#### Scenario: Header Bearer em todas as operações de histórico
- **WHEN** os testes exercitam registro, listagem e limpeza do histórico com uma sessão autenticada
- **THEN** cada requisição contém exatamente o esquema `Authorization: Bearer <token>` e nenhuma requisição inclui `user_id` como identidade

#### Scenario: Requisição de histórico sem token
- **WHEN** `POST /history`, `GET /history` ou `DELETE /history` é chamado sem token válido
- **THEN** o endpoint retorna HTTP 401 e não revela nem altera dados do histórico
