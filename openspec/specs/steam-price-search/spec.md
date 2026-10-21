# Steam Price Search Specification

## Purpose

Permite que qualquer pessoa encontre um jogo na Steam e consulte seu preço regional vigente em reais. A busca e o preço são transitórios e não são persistidos pelo ComparaKeys.

## Requirements

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

### Requirement: Atualização e não persistência de preços
O sistema SHALL buscar os preços atuais na Steam e, quando aplicável, na GOG a cada solicitação de comparação. O sistema SHALL NOT persistir buscas ou preços em banco de dados nem reutilizar preço anteriormente armazenado pelo ComparaKeys.

#### Scenario: Nova consulta de preço
- **WHEN** uma pessoa solicita o preço de um jogo já consultado anteriormente
- **THEN** o sistema consulta novamente as lojas aplicáveis e apresenta os preços retornados nessa solicitação

#### Scenario: Consulta não cria histórico
- **WHEN** uma busca ou consulta de preço é concluída
- **THEN** o sistema não grava o termo pesquisado nem os preços consultados em armazenamento persistente

### Requirement: Consulta pública de oferta da GOG
O sistema SHALL consultar a busca pública da GOG sem exigir autenticação, usando o nome do jogo selecionado nos resultados da Steam. O sistema SHALL considerar apenas produtos do tipo jogo. SHALL priorizar uma correspondência única cujo título seja idêntico após remover espaços externos, condensar espaços consecutivos e ignorar diferenças entre maiúsculas e minúsculas. Se não houver correspondência exata, o sistema SHALL ignorar edições e subtítulos comuns e aceitar uma correspondência somente quando exatamente um título remanescente corresponder ao título solicitado por prefixo ou contenção. A consulta SHALL normalizar pontuação que impeça a busca pública de retornar os resultados relevantes, sem alterar o título exibido pela loja. Para uma correspondência única, o sistema SHALL usar os dados da própria GOG para identificar o jogo, sua capa, sua página e seu preço regional em BRL. O sistema SHALL tratar jogo gratuito como R$ 0,00 e SHALL NOT apresentar como BRL preço ausente ou em outra moeda.

#### Scenario: Correspondência única na GOG
- **WHEN** a busca pública da GOG retorna exatamente um produto do tipo jogo com título correspondente após a normalização
- **THEN** o sistema usa a página, a capa e o preço regional em BRL desse resultado para a comparação

#### Scenario: Correspondência exata tem prioridade
- **WHEN** a GOG retorna um jogo com título normalizado idêntico e também outros títulos que só correspondem por prefixo ou contenção
- **THEN** o sistema escolhe a correspondência exata e não considera os resultados aproximados

#### Scenario: Correspondências exatas duplicadas
- **WHEN** a GOG retorna mais de um produto do tipo jogo com título normalizado idêntico
- **THEN** o sistema trata o resultado como ambíguo e não escolhe um produto por ordenação

#### Scenario: Correspondência aproximada única
- **WHEN** a GOG não retorna correspondência exata, mas retorna exatamente um jogo após ignorar edições e subtítulos comuns e comparar por prefixo ou contenção
- **THEN** o sistema usa esse jogo como correspondência GOG

#### Scenario: Busca pública sem autenticação
- **WHEN** uma pessoa sem sessão autenticada consulta a comparação de um jogo selecionado na Steam
- **THEN** o sistema consulta a GOG sem exigir login

#### Scenario: Resultado GOG sem preço em BRL
- **WHEN** a GOG retorna o jogo correspondente, mas não fornece preço regional em BRL
- **THEN** o sistema não converte nem apresenta preço de outra moeda como BRL

### Requirement: Fallback quando a oferta GOG não pode ser comparada
Se a busca da GOG não encontrar correspondência, retornar mais de uma correspondência, não fornecer preço utilizável em BRL ou falhar, o sistema SHALL manter visível a oferta Steam e SHALL apresentar um aviso específico para o motivo: “não encontrado na GOG”, “mais de uma possível correspondência” ou “sem preço em BRL na GOG”. Uma falha técnica da GOG SHALL manter a oferta Steam e apresentar um aviso recuperável sobre a indisponibilidade da comparação. A ausência ou ambiguidade da oferta GOG SHALL NOT impedir a exibição do resultado Steam.

#### Scenario: Jogo não encontrado na GOG
- **WHEN** a busca da GOG não retorna correspondência exata nem aproximada
- **THEN** o sistema apresenta somente a oferta Steam e informa “não encontrado na GOG”

#### Scenario: Jogo ausente ou correspondência ambígua na GOG
- **WHEN** a busca GOG não retorna correspondência ou retorna mais de uma correspondência possível
- **THEN** o sistema apresenta somente a oferta Steam e informa a mensagem específica de ausência ou ambiguidade

#### Scenario: Correspondência GOG ambígua
- **WHEN** a busca retorna mais de uma correspondência exata ou, sem correspondência exata, mais de um jogo aproximado possível
- **THEN** o sistema apresenta somente a oferta Steam e informa “mais de uma possível correspondência”

#### Scenario: Falha na consulta GOG
- **WHEN** a consulta pública da GOG falha ou retorna dados inválidos
- **THEN** o sistema apresenta a oferta Steam e um aviso recuperável sobre a indisponibilidade da comparação GOG

#### Scenario: Preço GOG ausente ou em outra moeda
- **WHEN** a GOG retorna um jogo correspondente sem preço em BRL
- **THEN** o sistema apresenta somente a oferta Steam e informa “sem preço em BRL na GOG”

### Requirement: Falhas da integração Steam
O sistema SHALL informar quando uma falha da Steam ou da conexão impedir a conclusão da busca ou da consulta de preço, sem apresentar dados antigos como resultado atual.

#### Scenario: Steam indisponível durante a busca
- **WHEN** a integração não consegue obter resultados de busca da Steam
- **THEN** o sistema apresenta uma mensagem de falha e permite que a pessoa tente novamente

#### Scenario: Steam indisponível durante a consulta do preço
- **WHEN** a integração não consegue obter o preço atual do jogo escolhido
- **THEN** o sistema informa que não foi possível consultar o preço e não apresenta preço armazenado anteriormente
