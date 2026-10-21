# Delta de especificação

## MODIFIED Requirements

### Requirement: Busca pública de jogos na Steam
O sistema SHALL permitir que uma pessoa sem autenticação pesquise jogos pelo nome na Steam. A busca SHALL consultar dados atuais da Steam automaticamente após a pessoa alterar o termo, sem exigir botão ou ação explícita de envio, e SHALL apresentar opções identificáveis para que a pessoa escolha o jogo correto. Quando a pessoa chega de uma pesquisa iniciada no catálogo, o campo SHALL ser preenchido com o termo encaminhado e a busca SHALL ser iniciada automaticamente. Resultados ou erros de uma consulta anterior SHALL NOT substituir o estado correspondente ao termo mais recente.

#### Scenario: Busca com correspondências
- **WHEN** uma pessoa informa um nome de jogo válido e pausa brevemente a digitação
- **THEN** o sistema consulta a Steam e apresenta os jogos correspondentes para escolha, sem exigir login ou clique em botão de busca

#### Scenario: Busca sem correspondências
- **WHEN** a Steam não encontra jogo correspondente ao nome pesquisado
- **THEN** o sistema informa que nenhum resultado foi encontrado e permite que a pessoa digite outro nome

#### Scenario: Busca sem texto
- **WHEN** a pessoa apaga o termo ou tenta pesquisar um termo composto apenas por espaços
- **THEN** o sistema limpa os resultados anteriores, não consulta a Steam e informa que é necessário preencher o nome quando aplicável

#### Scenario: Termo recebido do catálogo
- **WHEN** a pessoa chega à rota `/buscar` com um termo encaminhado pelo catálogo
- **THEN** o campo de busca apresenta o termo e o sistema consulta a Steam automaticamente

#### Scenario: Resposta de termo anterior
- **WHEN** uma consulta iniciada para um termo anterior termina depois de uma consulta para o termo mais recente
- **THEN** o sistema mantém visíveis somente os resultados, o estado de carregamento e os erros associados ao termo mais recente

#### Scenario: Falha na busca ao vivo
- **WHEN** a Steam falha ao responder a busca do termo atual
- **THEN** o sistema informa a falha e permite que a pessoa tente novamente alterando o termo, sem exibir resultados antigos como atuais

### Requirement: Exibição do preço atual em BRL
Após a escolha de um jogo, o sistema SHALL navegar para uma rota dedicada de comparação identificada pelo App ID da Steam e SHALL consultar a Steam para obter o preço regional atual do jogo no Brasil. A rota SHALL apresentar o resultado em reais (BRL), distinguir jogos gratuitos de preços indisponíveis e SHALL NOT apresentar um preço de outra moeda como se fosse BRL. Ao abrir a rota de comparação para um App ID válido, o sistema SHALL carregar a comparação atual desse jogo. Quando houver uma correspondência inequívoca e um preço utilizável na GOG, o sistema SHALL apresentar as ofertas Steam e GOG em blocos comparáveis, cada um com capa, nome do jogo e preço em BRL. O sistema SHALL destacar em verde o menor preço, considerando jogos gratuitos como R$ 0,00; em caso de empate, SHALL destacar ambos. O nome de cada jogo SHALL abrir a página correspondente da loja em uma nova aba. A apresentação SHALL manter o estilo visual preto e roxo e SHALL adaptar os blocos a telas estreitas.

#### Scenario: Seleção navega para comparação dedicada
- **WHEN** a pessoa seleciona um jogo entre os resultados da busca
- **THEN** o sistema navega para a rota dedicada `/comparar?app_id=<id>` e apresenta a comparação desse jogo nessa rota, em vez de exibi-la na tela de busca

#### Scenario: Abertura direta da comparação
- **WHEN** a pessoa abre `/comparar?app_id=<id>` para um App ID válido da Steam
- **THEN** o sistema consulta os preços atuais e carrega a comparação do jogo sem depender do estado anterior da tela de busca

#### Scenario: Jogo pago com preço disponível
- **WHEN** a pessoa abre a comparação de um jogo pago para o qual a Steam retorna preço regional em BRL
- **THEN** o sistema apresenta o nome do jogo e o preço formatado em reais

#### Scenario: Jogo gratuito
- **WHEN** a pessoa abre a comparação de um jogo que a Steam identifica como gratuito
- **THEN** o sistema informa que o jogo é gratuito em vez de tratar a ausência de preço como erro

#### Scenario: Preço brasileiro indisponível
- **WHEN** a pessoa abre a comparação de um jogo e a Steam não fornece preço regional em BRL
- **THEN** o sistema informa que o preço está indisponível e não exibe valor convertido ou de outra região

#### Scenario: Comparação com oferta GOG disponível
- **WHEN** a pessoa abre a comparação de um jogo Steam e a GOG retorna uma correspondência única com preço regional utilizável em BRL
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
