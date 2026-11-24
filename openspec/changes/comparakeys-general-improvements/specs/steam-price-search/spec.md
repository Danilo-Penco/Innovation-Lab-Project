# Spec Delta

## ADDED Requirements

### Requirement: Identidade acessível das lojas na comparação
A comparação SHALL apresentar um identificador visual reconhecível e o nome de cada loja junto ao respectivo preço. Logos SHALL possuir texto alternativo; se a imagem não estiver disponível, o nome da loja SHALL permanecer como fallback. A identificação SHALL coexistir com a indicação textual do menor preço e não depender somente de cor ou logotipo.

#### Scenario: Comparação com várias lojas
- **WHEN** a comparação apresenta ofertas Steam, GOG e CheapShark
- **THEN** cada preço está visualmente associado ao nome e ao identificador da sua própria loja

#### Scenario: Logo indisponível
- **WHEN** o logo da loja não pode ser carregado
- **THEN** a comparação mantém o nome textual da loja e o preço associados

### Requirement: Data de atualização ou consulta de cada preço
Para cada preço apresentado, o sistema SHALL mostrar a data e o horário fornecidos pela loja/API quando a resposta identificar explicitamente a atualização daquele preço. Se a fonte não fornecer essa informação, SHALL mostrar a data e o horário em que o ComparaKeys obteve a resposta, com rótulo explícito “Consultado pelo ComparaKeys”. O horário SHALL ser apresentado no fuso `America/Sao_Paulo`. Ao reutilizar dados em cache, SHALL manter o horário da consulta que originou a entrada, sem atualizá-lo por causa da leitura do cache. Se não for possível obter uma atualização válida, o sistema SHALL apresentar a falha/estado desatualizado e SHALL NOT rotular um valor anterior como preço atual.

#### Scenario: Fonte informa atualização do preço
- **WHEN** a resposta da loja contém uma data válida de atualização do preço
- **THEN** a comparação apresenta essa data e hora identificadas como atualização informada pela fonte

#### Scenario: Fonte não informa atualização do preço
- **WHEN** a resposta da loja não contém data de atualização do preço
- **THEN** a comparação apresenta a data e hora da consulta do ComparaKeys com rótulo explícito

#### Scenario: Oferta CheapShark retirada do cache
- **WHEN** uma oferta CheapShark é mostrada a partir do cache em memória
- **THEN** o horário exibido é o da consulta original, não o instante de leitura do cache

#### Scenario: Falha sem dado atual
- **WHEN** a consulta atual falha e não existe dado dentro da política de cache válida
- **THEN** a interface informa indisponibilidade/desatualização sem apresentar um preço antigo como atual

### Requirement: Nova tentativa explícita em falhas recuperáveis
Quando uma fonte externa falhar de forma recuperável, a tela SHALL oferecer uma ação explícita de nova tentativa para aquela fonte ou comparação. Uma nova tentativa SHALL respeitar timeout, limite e política de retry da integração, SHALL atualizar somente o estado da fonte solicitada e SHALL manter visíveis as ofertas válidas das demais fontes.

#### Scenario: Repetir consulta de uma loja
- **WHEN** a pessoa aciona “Tentar novamente” após uma falha recuperável de uma loja
- **THEN** o sistema consulta novamente a fonte indicada e mantém os resultados válidos das outras lojas

#### Scenario: Fonte limitada por HTTP 429
- **WHEN** a resposta da fonte informa limite temporário com `Retry-After`
- **THEN** o sistema informa a espera necessária e não inicia uma tentativa antes do prazo informado

## MODIFIED Requirements

### Requirement: Atualização e não persistência de preços
O sistema SHALL buscar os preços atuais da Steam e, quando aplicável, da GOG a cada solicitação de comparação. Ofertas CheapShark poderão permanecer somente em cache volátil em memória por até cinco minutos, conforme `price-offers`; o horário original de consulta SHALL ser preservado ao reutilizar esse cache. Nenhum preço SHALL ser gravado em banco de dados ou arquivo. Termos pesquisados SHALL NOT ser persistidos durante a digitação ou busca. Somente a abertura de uma comparação por pessoa autenticada poderá registrar dados não monetários do jogo no histórico próprio, conforme `search-history`; o cliente SHALL NOT enviar `user_id`. Preços, moedas e cotações SHALL NOT ser gravados no histórico.

#### Scenario: Nova consulta de preço
- **WHEN** uma pessoa solicita novamente o preço de um jogo já consultado
- **THEN** o sistema consulta novamente Steam e GOG e apresenta os valores retornados nessa solicitação

#### Scenario: Consulta não cria histórico
- **WHEN** uma busca ou consulta de preço é concluída sem abrir uma comparação autenticada
- **THEN** o sistema não grava buscas, preços ou cotações em armazenamento persistente; somente a abertura autenticada pode registrar os dados não monetários previstos em `search-history`

#### Scenario: Comparação autenticada registra histórico
- **WHEN** uma pessoa autenticada abre uma comparação válida
- **THEN** o sistema registra uma única entrada sem preço no histórico próprio, conforme `search-history`

#### Scenario: Comparação de visitante não cria histórico
- **WHEN** uma pessoa sem sessão abre uma comparação pública
- **THEN** a comparação funciona sem gravar histórico ou preço

#### Scenario: Cache CheapShark volátil
- **WHEN** uma oferta CheapShark é reutilizada antes de seu TTL de cinco minutos
- **THEN** ela permanece somente na memória do processo, mantém seu horário original de consulta e não é persistida em banco ou arquivo
