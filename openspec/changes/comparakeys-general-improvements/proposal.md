# Proposal

## Why

A comparação já reúne preços de várias fontes, mas a pessoa precisa identificar rapidamente a loja, entender quais valores são originais ou convertidos e saber quando os dados foram consultados. O fluxo também deve tornar mais simples retomar pesquisas, navegar pelo catálogo e recuperar-se de falhas externas, preservando a busca pública, a autenticação existente e a identidade visual do ComparaKeys.

## What Changes

- Consolidar o trabalho ainda pendente de `evolucao-comparakeys-quatro-fases`: concluir a validação da integração CheapShark já implementada, incluir o histórico autenticado da F3 e manter os favoritos da F4, sem reimplementar o que já funciona.
- Aprimorar os cartões de comparação com identidade visual por loja, destaque acessível do menor preço e valores originais/convertidos claramente separados. Quando houver conversão, mostrar a cotação e sua data; exibir o horário fornecido pela fonte quando disponível ou, com rótulo explícito, o horário da consulta do ComparaKeys.
- Permitir que a pessoa autenticada consulte e exclua seu histórico, sem registrar buscas por digitação, preços ou atividade de visitantes.
- Padronizar os cards do catálogo e dos resultados e melhorar a navegação entre catálogo, busca e comparação sem remover os fluxos públicos existentes.
- Oferecer estados consistentes de carregamento, erro, ausência de resultados e indisponibilidade, com nova tentativa explícita e falhas isoladas por serviço.
- Reforçar validação e sessão de autenticação, responsividade e acessibilidade, mantendo a busca e comparação públicas e as áreas de conta protegidas.
- Manter cache somente em memória quando apropriado, timeouts e política de retry por integração; não tratar resultados antigos como preços atuais nem persistir preços ou cotações.

## Capabilities

### New Capabilities

- `price-offers`: consolidar ofertas CheapShark existentes com logos de lojas, comparação de moeda original/convertida, cotação e horário de atualização.
- `search-history`: consultar e excluir pesquisas anteriores vinculadas à conta autenticada, incorporando o escopo F3 já planejado.
- `favorites`: manter os favoritos por conta e seus controles acessíveis no catálogo e na comparação, incorporando o escopo F4 já planejado.

### Modified Capabilities

- `steam-price-search`: melhorar identificação das lojas, comparação e atualização temporal dos preços, estados de falha/retentativa, acessibilidade e navegação.
- `game-catalog`: padronizar cards, busca e caminhos de navegação, mantendo os jogos e destinos atuais.
- `user-authentication`: reforçar validação e proteção/continuidade de sessão sem alterar os contratos existentes de autenticação Xano.

## Impact

- Reflex: páginas e estado em `Projeto/Projeto.py`; integrações existentes em `Projeto/steam.py`, `Projeto/gog.py` e `Projeto/cheapshark.py`; tema, componentes e testes correspondentes.
- Xano: autenticação existente e endpoints de histórico/favoritos a criar manualmente conforme contratos documentados; nenhum push nem publicação de XanoScript.
- Documentação e OpenSpec: atualizar contratos Xano, prompts para Xano Agent, verificações `scripts/check_xano.py`, visão geral e modelo de domínio.
- Não introduzir outra stack, novos provedores de preços, compra no site ou persistência de preços/cotações. Preservar as rotas públicas e protegidas e as políticas atuais de cache/retry salvo alteração explicitamente especificada.
- A mudança substitui o plano pendente da evolução em quatro fases para fins de implementação futura; o diretório da mudança anterior permanece intacto até ser reconciliado/arquivado. A especificação e o design devem tratar a implementação já existente como baseline e distinguir claramente código pronto de tarefas ainda não verificadas.
