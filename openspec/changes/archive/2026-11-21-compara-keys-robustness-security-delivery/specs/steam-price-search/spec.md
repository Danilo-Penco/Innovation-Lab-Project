# Spec Delta

## ADDED Requirements

### Requirement: Cache temporário de buscas Steam e metadados GOG
O sistema SHALL manter em memória um cache limitado e de curta duração, com TTL máximo de 5 minutos, para resultados de busca Steam e metadados de identificação/correspondência GOG. As chaves SHALL considerar o termo normalizado e os parâmetros regionais relevantes. O cache SHALL remover entradas expiradas e SHALL NOT armazenar preço nem gravar buscas, resultados ou metadados em armazenamento persistente. Cada comparação SHALL consultar os preços atuais aplicáveis diretamente às lojas, mesmo quando os metadados estiverem em cache.

#### Scenario: Reutilizar resultado de busca Steam ainda válido
- **WHEN** uma pessoa repete uma busca Steam equivalente antes de o TTL expirar
- **THEN** o sistema pode reutilizar os resultados correspondentes em memória sem reutilizar preço

#### Scenario: Reutilizar metadados GOG sem reutilizar preço
- **WHEN** uma comparação encontra metadados de correspondência GOG ainda válidos no cache
- **THEN** o sistema pode reutilizar somente os metadados e consulta o preço atual da GOG para essa comparação

#### Scenario: Expirar entrada em memória
- **WHEN** uma pessoa repete uma busca após o TTL de até 5 minutos
- **THEN** o sistema consulta novamente a fonte correspondente e substitui a entrada expirada

#### Scenario: Atualizar preços em toda comparação
- **WHEN** uma pessoa abre uma comparação, mesmo que resultados ou metadados estejam em cache
- **THEN** o sistema obtém preço atual de cada loja aplicável e não usa preço previamente guardado

#### Scenario: Ausência de persistência
- **WHEN** uma busca ou comparação termina ou o processo é reiniciado
- **THEN** nenhum termo, resultado, metadado ou preço fica gravado em banco de dados ou arquivo e as entradas em memória deixam de existir com o processo ou ao expirar

### Requirement: Estados da busca e comparação acessíveis
As telas `/buscar` e `/comparar` SHALL apresentar estados de carregamento, erro, ausência de resultados e indisponibilidade de forma perceptível e anunciável por tecnologia assistiva. A indicação do menor preço SHALL incluir texto além da cor. A interface SHALL adaptar seus controles e blocos de comparação a telas estreitas e SHALL respeitar a preferência de movimento reduzido do sistema.

#### Scenario: Anunciar busca em andamento e erro
- **WHEN** uma busca inicia, termina sem resultados ou falha
- **THEN** o estado correspondente é anunciado por uma região apropriada de status/alerta, sem substituir resultados do termo mais recente

#### Scenario: Anunciar consulta de preços
- **WHEN** a comparação está carregando ou uma loja não pode ser consultada
- **THEN** o estado e a mensagem específica são apresentados e anunciados sem remover uma oferta válida da outra loja

#### Scenario: Identificar menor preço sem depender apenas de cor
- **WHEN** uma loja oferece o menor preço ou há empate
- **THEN** o resultado apresenta um rótulo textual perceptível de menor preço para cada oferta aplicável, além do destaque visual

#### Scenario: Reduzir animações
- **WHEN** o dispositivo solicita movimento reduzido
- **THEN** animações decorativas nas telas de busca e comparação são reduzidas ou removidas sem ocultar conteúdo ou estado

#### Scenario: Comparação em tela estreita
- **WHEN** a rota de comparação é exibida em viewport estreito
- **THEN** cartões, preços, mensagens e controles permanecem legíveis, operáveis por teclado e sem rolagem horizontal da página
