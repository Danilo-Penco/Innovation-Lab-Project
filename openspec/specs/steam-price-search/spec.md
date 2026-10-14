# Steam Price Search Specification

## Purpose

Permite que qualquer pessoa encontre um jogo na Steam e consulte seu preço regional vigente em reais. A busca e o preço são transitórios e não são persistidos pelo ComparaKeys.

## Requirements

### Requirement: Busca pública de jogos na Steam
O sistema SHALL permitir que uma pessoa sem autenticação pesquise jogos pelo nome na Steam. A busca SHALL consultar dados atuais da Steam quando for executada e SHALL apresentar opções identificáveis para que a pessoa escolha o jogo correto. Quando a pessoa chega de uma pesquisa submetida no catálogo, o campo de busca SHALL ser preenchido com o termo encaminhado; a busca na Steam SHALL continuar sendo executada pela ação de pesquisa existente.

#### Scenario: Busca com correspondências
- **WHEN** uma pessoa informa um nome de jogo válido e executa a busca
- **THEN** o sistema consulta a Steam e apresenta os jogos correspondentes para escolha, sem exigir login

#### Scenario: Busca sem correspondências
- **WHEN** a Steam não encontra jogo correspondente ao nome pesquisado
- **THEN** o sistema informa que nenhum resultado foi encontrado e permite uma nova busca

#### Scenario: Busca sem texto
- **WHEN** a pessoa tenta executar a busca sem informar texto após remover espaços em branco
- **THEN** o sistema informa que é necessário preencher o nome e não consulta a Steam

#### Scenario: Termo recebido do catálogo
- **WHEN** a pessoa submete uma pesquisa no catálogo e chega à rota `/buscar`
- **THEN** o campo de busca apresenta o termo encaminhado e a pessoa pode executar a busca existente

### Requirement: Exibição do preço atual em BRL
Após a escolha de um jogo, o sistema SHALL consultar a Steam para obter o preço regional atual do jogo no Brasil e SHALL apresentar o resultado em reais (BRL). O sistema SHALL distinguir jogos gratuitos de preços indisponíveis e SHALL NOT apresentar um preço de outra moeda como se fosse BRL. Quando houver uma correspondência inequívoca e um preço utilizável na GOG, o sistema SHALL apresentar as ofertas Steam e GOG em blocos comparáveis, cada um com capa, nome do jogo e preço em BRL. O sistema SHALL destacar em verde o menor preço, considerando jogos gratuitos como R$ 0,00; em caso de empate, SHALL destacar ambos. O nome de cada jogo SHALL abrir a página correspondente da loja em uma nova aba. A apresentação SHALL manter o estilo visual preto e roxo e SHALL adaptar os blocos a telas estreitas.

#### Scenario: Jogo pago com preço disponível
- **WHEN** a pessoa escolhe um jogo pago para o qual a Steam retorna preço regional em BRL
- **THEN** o sistema apresenta o nome do jogo e o preço formatado em reais

#### Scenario: Jogo gratuito
- **WHEN** a pessoa escolhe um jogo que a Steam identifica como gratuito
- **THEN** o sistema informa que o jogo é gratuito em vez de tratar a ausência de preço como erro

#### Scenario: Preço brasileiro indisponível
- **WHEN** a pessoa escolhe um jogo e a Steam não fornece preço regional em BRL
- **THEN** o sistema informa que o preço está indisponível e não exibe valor convertido ou de outra região

#### Scenario: Comparação com oferta GOG disponível
- **WHEN** a pessoa seleciona um jogo Steam e a GOG retorna uma correspondência única com preço regional utilizável em BRL
- **THEN** o sistema apresenta os blocos da Steam e da GOG lado a lado, com capa, nome e preço em BRL de cada loja

#### Scenario: Destaque do menor preço
- **WHEN** ambas as lojas apresentam um preço comparável, incluindo o valor de R$ 0,00 para um jogo gratuito
- **THEN** o sistema destaca em verde apenas o menor preço ou ambos os preços quando houver empate

#### Scenario: Abrir a página de uma loja
- **WHEN** a pessoa seleciona o nome do jogo em um bloco de loja
- **THEN** o sistema abre a página daquele jogo na loja correspondente em uma nova aba

#### Scenario: Layout da comparação em telas estreitas
- **WHEN** a comparação é exibida em uma tela estreita
- **THEN** os blocos continuam legíveis e se reorganizam sem cortar seus nomes, capas ou preços

### Requirement: Atualização e não persistência de preços
O sistema SHALL buscar os preços atuais na Steam e, quando aplicável, na GOG a cada solicitação de comparação. O sistema SHALL NOT persistir buscas ou preços em banco de dados nem reutilizar preço anteriormente armazenado pelo ComparaKeys.

#### Scenario: Nova consulta de preço
- **WHEN** uma pessoa solicita o preço de um jogo já consultado anteriormente
- **THEN** o sistema consulta novamente as lojas aplicáveis e apresenta os preços retornados nessa solicitação

#### Scenario: Consulta não cria histórico
- **WHEN** uma busca ou consulta de preço é concluída
- **THEN** o sistema não grava o termo pesquisado nem os preços consultados em armazenamento persistente

### Requirement: Consulta pública de oferta da GOG
O sistema SHALL consultar a busca pública da GOG sem exigir autenticação, usando o nome do jogo selecionado nos resultados da Steam. O sistema SHALL considerar uma correspondência somente quando houver exatamente um resultado cujo título seja idêntico após remover espaços externos, condensar espaços consecutivos e ignorar diferenças entre maiúsculas e minúsculas. Para uma correspondência, o sistema SHALL usar os dados da própria GOG para identificar o jogo, sua capa, sua página e seu preço regional em BRL. O sistema SHALL tratar jogo gratuito como R$ 0,00 e SHALL NOT apresentar como BRL preço ausente ou em outra moeda.

#### Scenario: Correspondência única na GOG
- **WHEN** a busca pública da GOG retorna exatamente um jogo com título correspondente após a normalização definida
- **THEN** o sistema usa a página, a capa e o preço regional em BRL desse resultado para a comparação

#### Scenario: Busca pública sem autenticação
- **WHEN** uma pessoa sem sessão autenticada consulta a comparação de um jogo selecionado na Steam
- **THEN** o sistema consulta a GOG sem exigir login

#### Scenario: Resultado GOG sem preço em BRL
- **WHEN** a GOG retorna o jogo correspondente, mas não fornece preço regional em BRL
- **THEN** o sistema não converte nem apresenta preço de outra moeda como BRL

### Requirement: Fallback quando a oferta GOG não pode ser comparada
Se a busca da GOG não encontrar correspondência, retornar mais de uma correspondência, não fornecer preço utilizável em BRL ou falhar, o sistema SHALL manter visível a oferta Steam e SHALL apresentar um aviso de que a comparação GOG está indisponível. A falha ou ausência da oferta GOG SHALL NOT impedir a exibição do resultado Steam.

#### Scenario: Jogo ausente ou correspondência ambígua na GOG
- **WHEN** a busca GOG não retorna correspondência ou retorna mais de uma correspondência com título correspondente
- **THEN** o sistema apresenta somente a oferta Steam e um aviso de que não foi possível comparar com a GOG

#### Scenario: Falha na consulta GOG
- **WHEN** a consulta pública da GOG falha ou retorna dados inválidos
- **THEN** o sistema apresenta a oferta Steam e um aviso recuperável sobre a indisponibilidade da comparação GOG

#### Scenario: Preço GOG ausente ou em outra moeda
- **WHEN** a GOG retorna um jogo correspondente sem preço em BRL
- **THEN** o sistema apresenta somente a oferta Steam e um aviso de que não foi possível comparar com a GOG

### Requirement: Falhas da integração Steam
O sistema SHALL informar quando uma falha da Steam ou da conexão impedir a conclusão da busca ou da consulta de preço, sem apresentar dados antigos como resultado atual.

#### Scenario: Steam indisponível durante a busca
- **WHEN** a integração não consegue obter resultados de busca da Steam
- **THEN** o sistema apresenta uma mensagem de falha e permite que a pessoa tente novamente

#### Scenario: Steam indisponível durante a consulta do preço
- **WHEN** a integração não consegue obter o preço atual do jogo escolhido
- **THEN** o sistema informa que não foi possível consultar o preço e não apresenta preço armazenado anteriormente
