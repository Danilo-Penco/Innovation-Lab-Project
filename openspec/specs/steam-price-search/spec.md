# Steam Price Search Specification

## Purpose

Permite que qualquer pessoa encontre um jogo na Steam e consulte seu preço regional vigente em reais. A busca e o preço são transitórios e não são persistidos pelo ComparaKeys.

## Requirements

### Requirement: Busca pública de jogos na Steam
O sistema SHALL permitir que uma pessoa sem autenticação pesquise jogos pelo nome na Steam. A busca SHALL consultar dados atuais da Steam quando for executada e SHALL apresentar opções identificáveis para que a pessoa escolha o jogo correto.

#### Scenario: Busca com correspondências
- **WHEN** uma pessoa informa um nome de jogo válido e executa a busca
- **THEN** o sistema consulta a Steam e apresenta os jogos correspondentes para escolha, sem exigir login

#### Scenario: Busca sem correspondências
- **WHEN** a Steam não encontra jogo correspondente ao nome pesquisado
- **THEN** o sistema informa que nenhum resultado foi encontrado e permite uma nova busca

#### Scenario: Busca sem texto
- **WHEN** a pessoa tenta executar a busca sem informar texto após remover espaços em branco
- **THEN** o sistema informa que é necessário preencher o nome e não consulta a Steam

### Requirement: Exibição do preço atual em BRL
Após a escolha de um jogo, o sistema SHALL consultar a Steam para obter o preço regional atual do jogo no Brasil e SHALL apresentar o resultado em reais (BRL). O sistema SHALL distinguir jogos gratuitos de preços indisponíveis e SHALL NOT apresentar um preço de outra moeda como se fosse BRL.

#### Scenario: Jogo pago com preço disponível
- **WHEN** a pessoa escolhe um jogo pago para o qual a Steam retorna preço regional em BRL
- **THEN** o sistema apresenta o nome do jogo e o preço formatado em reais

#### Scenario: Jogo gratuito
- **WHEN** a pessoa escolhe um jogo que a Steam identifica como gratuito
- **THEN** o sistema informa que o jogo é gratuito em vez de tratar a ausência de preço como erro

#### Scenario: Preço brasileiro indisponível
- **WHEN** a pessoa escolhe um jogo e a Steam não fornece preço regional em BRL
- **THEN** o sistema informa que o preço está indisponível e não exibe valor convertido ou de outra região

### Requirement: Atualização e não persistência de preços
O sistema SHALL buscar o preço na Steam a cada solicitação de preço e SHALL NOT persistir buscas ou preços em banco de dados nem reutilizar preço anteriormente armazenado pelo ComparaKeys.

#### Scenario: Nova consulta de preço
- **WHEN** uma pessoa solicita o preço de um jogo já consultado anteriormente
- **THEN** o sistema consulta novamente a Steam e apresenta o preço retornado nessa solicitação

#### Scenario: Consulta não cria histórico
- **WHEN** uma busca ou consulta de preço é concluída
- **THEN** o sistema não grava o termo pesquisado nem o preço consultado em armazenamento persistente

### Requirement: Falhas da integração Steam
O sistema SHALL informar quando uma falha da Steam ou da conexão impedir a conclusão da busca ou da consulta de preço, sem apresentar dados antigos como resultado atual.

#### Scenario: Steam indisponível durante a busca
- **WHEN** a integração não consegue obter resultados de busca da Steam
- **THEN** o sistema apresenta uma mensagem de falha e permite que a pessoa tente novamente

#### Scenario: Steam indisponível durante a consulta do preço
- **WHEN** a integração não consegue obter o preço atual do jogo escolhido
- **THEN** o sistema informa que não foi possível consultar o preço e não apresenta preço armazenado anteriormente
