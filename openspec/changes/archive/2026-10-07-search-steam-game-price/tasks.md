# Tasks

## 1. Integração Steam no servidor Reflex

- [x] 1.1 Confirmar os formatos atuais das respostas públicas da Steam para busca por nome e detalhes por App ID. Busca: `items[].name`, `items[].id` e `items[].price.currency/final`; detalhe: `data.name`, `data.steam_appid`, `data.is_free` e `data.price_overview.currency/final`.
- [x] 1.2 Implementar cliente HTTP assíncrono no servidor Reflex para busca de candidatos e preço por App ID, com validação de entradas e parsing tipado das respostas; verificar os casos principais por testes sem adicionar persistência.
- [x] 1.3 Testar parsing e estados de preço com respostas simuladas para BRL pago, gratuito, preço indisponível, resposta inválida e falha/timeout HTTP; confirmar ausência de gravação em armazenamento.

## 2. Experiência pública de busca

- [x] 2.1 Substituir o formulário de login prototipado pela tela pública de busca e seleção de jogos; verificar visualmente os estados inicial, carregando, resultados, nenhum resultado e erro.
- [x] 2.2 Conectar os eventos Reflex à integração Steam, limpar seleção/preço obsoletos ao iniciar nova busca e exibir o preço atual em BRL ou o estado apropriado; verificar que o fluxo não exige login.
- [x] 2.3 Adicionar ou completar testes para validação do termo, escolha do resultado, formatação em BRL e transições de estado; executar os testes direcionados e `reflex compile --dry`.

## 3. Documentação e verificação integrada

- [x] 3.1 Atualizar `docs/project-overview.md` e `docs/domain-model.md` para documentar a exceção de busca pública via servidor Reflex, Steam como única loja nesta tela e ausência de persistência; verificar que a arquitetura geral e autenticação das demais áreas permaneçam descritas corretamente.
- [x] 3.2 Executar uma busca e consulta de preço reais sem autenticação, repetir uma consulta e validar um jogo gratuito; confirmar que resultados são da Steam, valores BRL são formatados corretamente, falhas/preços ausentes não mostram valores antigos e nenhuma busca/preço é persistido.
