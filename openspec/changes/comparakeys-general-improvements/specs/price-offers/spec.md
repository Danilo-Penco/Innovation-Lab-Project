# Spec Delta

## Purpose

Esta capacidade torna as ofertas comparáveis e transparentes, identificando as lojas, as moedas, a cotação e a idade dos dados sem apresentar valores aproximados como preços locais confirmados.

## ADDED Requirements

### Requirement: Identificação visual das lojas na comparação
Cada oferta comparada SHALL apresentar o nome e o logotipo identificável da loja de origem, incluindo Steam, GOG e lojas adicionais. O logotipo SHALL ter texto alternativo com o nome da loja; se não houver imagem válida, o nome SHALL continuar visível como fallback. As ofertas CheapShark SHALL continuar limitadas às lojas ativas, distintas de Steam e GOG, sem duplicar loja, e SHALL abrir o redirecionamento correspondente do CheapShark em nova aba.

#### Scenario: Logotipo disponível
- **WHEN** uma loja comparável possui um logotipo válido
- **THEN** a comparação exibe o logotipo com nome acessível e mantém o nome da loja visível

#### Scenario: Logotipo ausente ou indisponível
- **WHEN** a fonte da loja não fornece um logotipo válido ou a imagem não carrega
- **THEN** a comparação identifica a loja pelo nome sem deixar espaço visual quebrado

#### Scenario: Ofertas adicionais elegíveis
- **WHEN** a CheapShark retorna ofertas para o Steam App ID
- **THEN** a comparação mostra no máximo cinco lojas ativas distintas, exclui Steam e GOG e abre cada oferta pelo link CheapShark em nova aba

### Requirement: Moeda original, conversão e cotação explícita
O sistema SHALL identificar a moeda explicitamente retornada pela CheapShark. Uma oferta em BRL SHALL ser mostrada sem conversão. Quando a oferta for em USD e houver cotação USD/BRL válida, SHALL mostrar o valor original e o valor aproximado convertido no formato “US$ x,xx ≈ R$ x,xx”, além do valor exato da taxa usada e da data da cotação informada pela fonte. O aviso visível SHALL ser “Preços internacionais em dólar, convertidos pela cotação do dia. Steam e GOG mostram o preço regional em reais, então a comparação é aproximada.” Se a cotação falhar, SHALL mostrar somente o preço original em “US$ x,xx” e um aviso próprio de indisponibilidade, sem bloquear as ofertas Steam/GOG. Preços Steam e GOG em BRL SHALL NOT ser convertidos.

#### Scenario: Oferta CheapShark em dólar com cotação
- **WHEN** uma oferta está em USD e a fonte de câmbio retorna uma taxa USD/BRL válida
- **THEN** a oferta mostra o valor em USD, o valor convertido aproximado em BRL, a taxa usada e a data retornada pela fonte

#### Scenario: Cotação indisponível
- **WHEN** a fonte de câmbio falha ou retorna dados inválidos
- **THEN** a oferta mostra somente seu preço original em USD, apresenta um aviso de cotação indisponível e mantém Steam e GOG disponíveis

#### Scenario: Preço local em BRL
- **WHEN** Steam ou GOG retorna preço regional em BRL, ou a CheapShark identifica explicitamente BRL
- **THEN** o sistema mostra o preço BRL original sem aplicar câmbio

### Requirement: Menor preço e comparabilidade
Entre valores numéricos comparáveis, o sistema SHALL destacar em verde o menor preço e SHALL indicar textualmente esse estado; empates SHALL destacar todas as ofertas empatadas. Ofertas em USD sem cotação válida SHALL NOT participar da comparação numérica em BRL. Identificação da moeda ou logotipos SHALL NOT alterar o resultado do cálculo do menor preço.

#### Scenario: Menor preço e empate
- **WHEN** duas ou mais lojas possuem valores comparáveis e uma ou mais compartilham o menor valor
- **THEN** cada oferta com o menor valor recebe destaque verde e indicação textual de menor preço

#### Scenario: Oferta USD sem conversão
- **WHEN** uma oferta permanece em USD porque a cotação falhou
- **THEN** ela não é comparada numericamente com ofertas em BRL nem recebe destaque de menor preço baseado em conversão inexistente

### Requirement: Integração resiliente e cache volátil de ofertas
Falha, timeout, resposta inválida ou HTTP 429 da CheapShark ou da fonte cambial SHALL afetar somente os dados dependentes dessa fonte e SHALL NOT remover ofertas válidas de Steam ou GOG. Cada integração SHALL ter timeout limitado e mensagens de erro próprias; chamadas GET poderão repetir uma única vez somente após erro de rede/timeout, nunca após resposta HTTP, e SHALL respeitar `Retry-After` quando aplicável. Ofertas SHALL permanecer apenas em cache de memória por no máximo cinco minutos e cotações por no máximo uma hora; preços e cotações SHALL NOT ser persistidos em banco ou arquivo.

#### Scenario: Falha isolada de ofertas ou câmbio
- **WHEN** CheapShark ou a fonte cambial falha durante uma comparação
- **THEN** o sistema apresenta aviso recuperável para a integração afetada e preserva as demais ofertas válidas

#### Scenario: Resposta HTTP de erro
- **WHEN** uma integração externa responde com erro HTTP
- **THEN** o sistema não repete automaticamente a solicitação e respeita a limitação temporária indicada pela fonte

#### Scenario: Expiração do cache
- **WHEN** o TTL de uma oferta ou cotação expira ou o processo Reflex reinicia
- **THEN** o dado deixa de ser reutilizável e nenhum preço ou cotação permanece em armazenamento persistente
