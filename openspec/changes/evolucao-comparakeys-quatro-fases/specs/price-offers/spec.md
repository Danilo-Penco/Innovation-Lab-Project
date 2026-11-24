# Spec Delta

## Purpose

Esta capacidade amplia a comparação de preços com ofertas de outras lojas encontradas pela API pública CheapShark e identifica claramente preços em BRL reais e valores convertidos aproximados.

## ADDED Requirements

### Requirement: Ofertas CheapShark para o Steam App ID
Ao carregar uma comparação, o sistema SHALL consultar a API pública CheapShark usando o Steam App ID do jogo e SHALL apresentar no máximo cinco ofertas de lojas diferentes de Steam e GOG. Cada oferta SHALL mostrar o nome da loja, o preço disponível e um link de oferta do CheapShark que abre em nova aba. O sistema SHALL ordenar as ofertas elegíveis por preço numérico comparável, sem incluir lojas inativas nem duplicar lojas.

#### Scenario: Ofertas disponíveis em outras lojas
- **WHEN** CheapShark retorna ofertas válidas para o Steam App ID
- **THEN** a comparação apresenta até cinco lojas distintas, exclui Steam e GOG e ordena as ofertas pelo menor preço comparável

#### Scenario: Link da oferta
- **WHEN** a pessoa seleciona uma oferta CheapShark
- **THEN** o sistema abre em nova aba o redirecionamento CheapShark correspondente ao `dealID`, sem substituir o destino por um link afiliado próprio

#### Scenario: Nenhuma oferta de outra loja
- **WHEN** CheapShark não retorna oferta válida de loja diferente de Steam e GOG
- **THEN** a comparação mantém as ofertas Steam/GOG existentes e informa que não há ofertas adicionais disponíveis

### Requirement: Conversão aproximada de ofertas CheapShark
O sistema SHALL primeiro verificar se a resposta da própria CheapShark identifica explicitamente a oferta como BRL. Se houver preço CheapShark explicitamente em BRL, SHALL exibi-lo sem conversão. Somente quando a CheapShark não fornecer preço em BRL o sistema SHALL tratar o preço segundo a moeda USD da API e convertê-lo para BRL aproximado usando uma taxa obtida de uma API pública sem chave. Quando houver cotação válida, cada oferta SHALL exibir o preço original em dólar e o convertido no formato “US$ x,xx ≈ R$ x,xx”. Logo abaixo do título “Outras lojas”, SHALL exibir o aviso visível exato “Preços internacionais em dólar, convertidos pela cotação do dia. Steam e GOG mostram o preço regional em reais, então a comparação é aproximada.” Se a cotação falhar, SHALL mostrar somente o preço em dólar, no formato “US$ x,xx”, e o aviso próprio de cotação indisponível. O sistema SHALL cachear a cotação apenas em memória por até uma hora. Preços Steam e GOG SHALL continuar exibidos somente na moeda BRL retornada pelas próprias lojas e SHALL NOT ser convertidos.

#### Scenario: CheapShark fornece BRL
- **WHEN** a resposta CheapShark identifica explicitamente que uma oferta está em BRL
- **THEN** o sistema apresenta o preço recebido sem consultar câmbio nem exibir aviso de conversão

#### Scenario: Converter oferta em dólar
- **WHEN** uma oferta CheapShark fornece preço em USD e há uma cotação USD/BRL válida
- **THEN** o sistema mostra o preço original e o convertido no formato “US$ x,xx ≈ R$ x,xx” e o aviso definido diretamente abaixo do título “Outras lojas”

#### Scenario: Cotação indisponível
- **WHEN** a fonte de câmbio falha, retorna resposta inválida ou não contém USD/BRL
- **THEN** o sistema mostra somente o preço CheapShark em “US$ x,xx”, exibe o aviso próprio de cotação indisponível e mantém a comparação Steam/GOG disponível

#### Scenario: Preços Steam e GOG
- **WHEN** Steam ou GOG retorna preço regional utilizável em BRL
- **THEN** o sistema apresenta o preço original em BRL sem conversão ou aviso de câmbio

### Requirement: Menor preço entre lojas e isolamento de falhas
Quando houver ofertas comparáveis, o sistema SHALL indicar em verde o menor preço entre Steam, GOG e CheapShark, incluindo empate, e SHALL manter um aviso textual sobre aproximações cambiais. Falha, timeout, resposta inválida ou limitação da CheapShark SHALL NOT impedir a exibição das ofertas Steam e GOG; falha de câmbio SHALL NOT impedir ofertas CheapShark em USD.

#### Scenario: Menor preço entre as lojas
- **WHEN** há preços comparáveis em mais de uma loja, incluindo valores convertidos válidos
- **THEN** o sistema destaca em verde a menor oferta ou todas as ofertas empatadas e mantém visível o aviso de conversão para cada valor aproximado

#### Scenario: Falha da CheapShark
- **WHEN** CheapShark está indisponível, excede o timeout, retorna JSON inválido ou limita a chamada
- **THEN** o sistema apresenta uma mensagem específica recuperável e mantém os resultados válidos de Steam e GOG

### Requirement: Cache volátil e limites da integração CheapShark
O sistema SHALL limitar cada solicitação CheapShark a 10 segundos e SHALL repetir uma única vez somente após erro de rede, sem repetir respostas HTTP. Resultados de ofertas SHALL poder permanecer apenas em cache volátil em memória por no máximo cinco minutos; nenhum preço CheapShark, consulta ou metadado SHALL ser gravado em banco de dados ou arquivo. As chamadas SHALL usar um `User-Agent` descritivo, respeitar `Retry-After` em HTTP 429 e SHALL ocorrer como consequência de uma ação de comparação, nunca a cada tecla digitada.

#### Scenario: Erro transitório de rede
- **WHEN** a primeira chamada CheapShark falha por erro de rede
- **THEN** o sistema tenta novamente uma única vez e retorna os dados ou erro da tentativa seguinte

#### Scenario: Resposta HTTP de erro ou limite
- **WHEN** CheapShark responde com HTTP 4xx, 5xx ou 429
- **THEN** o sistema não repete a chamada automaticamente, respeita `Retry-After` para requisições futuras e mantém Steam/GOG disponíveis

#### Scenario: Expiração ou reinício do processo
- **WHEN** o TTL de cinco minutos expira ou o processo Reflex reinicia
- **THEN** ofertas em cache deixam de ser reutilizáveis e não há preço CheapShark persistido em banco de dados ou arquivo
