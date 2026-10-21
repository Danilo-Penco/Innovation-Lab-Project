# Spec Delta

## MODIFIED Requirements

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

#### Scenario: Preço GOG ausente ou em outra moeda
- **WHEN** a GOG retorna uma correspondência única, mas não fornece preço em BRL
- **THEN** o sistema apresenta somente a oferta Steam e informa “sem preço em BRL na GOG”

#### Scenario: Falha na consulta GOG
- **WHEN** a consulta pública da GOG falha ou retorna dados inválidos
- **THEN** o sistema apresenta a oferta Steam e um aviso recuperável sobre a indisponibilidade da comparação GOG
