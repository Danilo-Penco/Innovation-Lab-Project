# Spec Delta

## Purpose

Esta capacidade permite que cada pessoa autenticada consulte e exclua suas pesquisas recentes sem armazenar preços, enquanto visitantes continuam podendo pesquisar e comparar sem gerar histórico.

## ADDED Requirements

### Requirement: Registrar comparações no histórico do próprio usuário
O sistema SHALL registrar uma entrada somente quando uma pessoa autenticada abre uma comparação válida. A chamada SHALL ser `POST /history` no grupo Authentication e enviar `Authorization: Bearer <token>` com o corpo `{term, steam_app_id, game_name}`, recebendo `{"id": N}`. O endpoint SHALL obter o proprietário exclusivamente de `$auth.id`; o cliente SHALL NOT enviar `user_id`. Para uma abertura direta da rota de comparação sem termo de busca disponível, `term` SHALL usar o nome do jogo retornado pela Steam. Registros consecutivos do mesmo Steam App ID para o usuário SHALL atualizar o item mais recente em vez de criar duplicata. O histórico SHALL conter apenas dados de pesquisa, nunca preços, taxa cambial ou dados de visitantes.

#### Scenario: Pessoa autenticada abre comparação
- **WHEN** uma pessoa autenticada abre uma comparação válida
- **THEN** o sistema envia uma única chamada `POST /history` com termo, Steam App ID e nome, e o Xano associa o registro a `$auth.id`

#### Scenario: Abertura direta da comparação
- **WHEN** uma pessoa autenticada abre `/comparar?app_id=<id>` sem termo de busca na sessão ou URL
- **THEN** o sistema usa o nome validado do jogo como `term` do registro

#### Scenario: Visitante pesquisa ou compara
- **WHEN** uma pessoa sem sessão digita, pesquisa ou abre uma comparação
- **THEN** a busca e comparação continuam disponíveis e nenhuma chamada de histórico é enviada

#### Scenario: Digitação não gera histórico
- **WHEN** uma pessoa altera o termo de busca sem abrir uma comparação
- **THEN** nenhum registro é criado

#### Scenario: Repetição consecutiva do mesmo jogo
- **WHEN** uma pessoa autenticada abre novamente o Steam App ID que está no topo do próprio histórico
- **THEN** o Xano atualiza esse registro em vez de criar uma duplicata consecutiva

### Requirement: Listar e limpar somente o histórico próprio
Uma pessoa autenticada SHALL poder listar os 20 itens mais recentes por `GET /history`, em ordem decrescente de criação, e limpar seu histórico por `DELETE /history`. A lista SHALL conter `{id, term, steam_app_id, game_name, created_at}` e a remoção SHALL responder `{"deleted": N}`. Ambos os endpoints SHALL exigir `Authorization: Bearer <token>` e derivar o proprietário exclusivamente de `$auth.id`.

#### Scenario: Listar histórico
- **WHEN** uma pessoa autenticada abre `/historico`
- **THEN** o sistema apresenta até 20 registros próprios, do mais recente ao mais antigo

#### Scenario: Isolamento entre usuários
- **WHEN** uma pessoa autenticada solicita ou limpa seu histórico
- **THEN** a operação afeta somente registros associados a `$auth.id`, independentemente de parâmetros enviados pelo cliente

#### Scenario: Limpar histórico
- **WHEN** a pessoa confirma a ação “Limpar histórico”
- **THEN** o sistema chama `DELETE /history`, recebe `{"deleted": N}` e mostra o estado vazio

#### Scenario: Histórico vazio
- **WHEN** a pessoa autenticada não tem registros
- **THEN** `/historico` apresenta orientação para pesquisar e comparar um jogo sem indicar erro

#### Scenario: Requisição sem token
- **WHEN** um endpoint de histórico recebe uma chamada sem token válido
- **THEN** o Xano responde HTTP 401 e não revela nem altera dados

### Requirement: Apresentar históricos e atalhos recentes
O sistema SHALL disponibilizar `/historico` como rota protegida, com confirmação antes de limpar, links para reabrir cada comparação e estado vazio orientativo. O catálogo autenticado SHALL apresentar os cinco itens mais recentes, carregados em uma única chamada de listagem por visita, sem consultar o histórico por card.

#### Scenario: Retomar pesquisa
- **WHEN** a pessoa seleciona um item em `/historico` ou nos recentes do catálogo
- **THEN** o sistema abre `/comparar?app_id=<steam_app_id>`

#### Scenario: Carregar recentes no catálogo
- **WHEN** uma pessoa autenticada visita `/catalogo`
- **THEN** o sistema faz no máximo uma chamada `GET /history` e apresenta até cinco itens recentes

#### Scenario: Acesso sem autenticação
- **WHEN** uma pessoa sem sessão abre `/historico`
- **THEN** o sistema não apresenta dados e encaminha a pessoa para `/entrar`
