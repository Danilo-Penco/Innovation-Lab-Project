# Tasks

## 1. F1 — Comparação, cotação e atualização dos preços

- [x] 1.1 Reconciliar a implementação CheapShark existente com as tarefas F2 pendentes da mudança anterior, validar ofertas, fallback USD e navegação real no site, e registrar qualquer limitação sem duplicar código; verificar com smoke test de `/comparar` e estado documentado do change anterior.
- [x] 1.2 Padronizar o modelo de oferta para preservar loja, logo seguro, moeda/valor original, valor BRL comparável e metadados temporais; ampliar parsers de Steam, GOG, CheapShark e Frankfurter com respostas simuladas para dados presentes, ausentes e inválidos.
- [x] 1.3 Exibir logo e nome acessível de cada loja, preço original e convertido, taxa e data da cotação, mantendo o destaque verde e o fallback USD existentes; verificar com testes de apresentação e comparação de menor preço/empate, e atualizar a documentação de ofertas.
- [x] 1.4 Mostrar para cada oferta a data de atualização fornecida pela fonte ou, quando ausente, o horário explicitamente rotulado da consulta em `America/Sao_Paulo`; preservar a hora original em cache, marcar indisponibilidade sem cache válido e testar timestamps de fonte, fallback e cache.
- [x] 1.5 Harmonizar timeout, retry único somente para rede/timeout, tratamento de HTTP 429/`Retry-After`, mensagens e nova tentativa explícita por integração sem remover ofertas válidas de outras lojas; verificar com mocks de cada falha e testes de estado parcial.
- [x] 1.6 Atualizar `README.md`, `docs/project-overview.md` e `docs/domain-model.md` para refletir logos, cotação, datas e a distinção entre preço da fonte e horário consultado; verificar consistência com os specs e executar a suíte completa, `reflex compile` e smoke test de comparação.

## 2. F2 — Histórico autenticado no Xano

- [x] 2.1 Documentar em `docs/xano-setup.md` o contrato exato de `search_history` e `POST /history`, `GET /history`, `DELETE /history`, incluindo tipos, limites, corpos/respostas, Bearer, 401, deduplicação consecutiva e `$auth.id`; verificar exemplos contra o spec `search-history`.
- [x] 2.2 Adicionar em `docs/xano-agent-prompts.md` o prompt pronto para criar a tabela e endpoints sem publicar XanoScript, e estender `scripts/check_xano.py` com PASS/FAIL para respostas, Bearer, 401, deduplicação e isolamento entre duas contas descartáveis; verificar que não há segredos no repositório ou na saída.
- [ ] 2.3 Criar manualmente tabela e endpoints F3 pelo Xano Agent em workspace de teste, sem push/publicação de XanoScript, e executar o checker; confirmar PASS de todos os cenários e limpar somente os dados descartáveis criados para o teste.
- [ ] 2.4 Implementar o cliente Reflex para as três operações de histórico usando `Authorization: Bearer <token>` e sem `user_id`; testar caminhos, corpos, respostas, erros, 401 e ausência de chamadas por digitação/visitante com respostas simuladas antes de ligar a interface.
- [ ] 2.5 Implementar `/historico`, limpeza com confirmação, retorno à comparação e bloco de cinco pesquisas recentes no catálogo; registrar somente abertura autenticada da comparação, testar lista de 20, estado vazio, acesso protegido e uma chamada de listagem por visita, e atualizar o modelo de domínio.
- [ ] 2.6 Executar a suíte completa, `reflex compile` e smoke test de `/historico`, recentes no catálogo e fluxo de visitante/autenticado; confirmar que falhas Xano não bloqueiam comparação e que preços não são persistidos.

## 3. F3 — Favoritos e lista de desejos no Xano

- [ ] 3.1 Documentar em `docs/xano-setup.md` o contrato exato de `favorite`, unicidade por usuário + Steam App ID e `GET /favorites`, `POST /favorites`, `DELETE /favorites/{steam_app_id}`; verificar respostas, HTTP 200 idempotente, Bearer, 401, isolamento e `$auth.id` contra o spec `favorites`.
- [ ] 3.2 Adicionar em `docs/xano-agent-prompts.md` o prompt pronto para criar a tabela/índice e endpoints sem XanoScript e estender `scripts/check_xano.py` com PASS/FAIL para 401, inclusão idempotente e isolamento; verificar que credenciais ficam fora do Git e dos logs.
- [ ] 3.3 Criar manualmente tabela, índice e endpoints F4 pelo Xano Agent em workspace de teste e executar o checker; confirmar todos os cenários, inclusive isolamento entre contas, antes de integrar o Reflex.
- [ ] 3.4 Implementar o cliente Reflex de favoritos com Bearer e respostas tipadas; testar métodos, caminhos, corpos, idempotência, 401 e que a lista é carregada uma vez por visita, não por card.
- [ ] 3.5 Implementar controles de favorito acessíveis na comparação e nos cards, encaminhar visitantes para `/entrar` sem chamada de escrita e criar `/favoritos` com capas, navegação, remoção e estado vazio; testar proteção, `aria-label`, carregamento em lote e atualização após operações.
- [ ] 3.6 Atualizar `README.md`, `docs/project-overview.md` e `docs/domain-model.md` com favoritos e relações de propriedade; executar suíte completa, `reflex compile` e smoke test de `/favoritos`, controles, estado vazio e fluxo visitante/autenticado.

## 4. F4 — Catálogo, autenticação e acessibilidade integrada

- [ ] 4.1 Padronizar hierarquia, capas/fallbacks e destinos dos cards do catálogo e resultados de busca sem substituir a lista atual de jogos; testar App IDs, navegação, alvos de teclado e layouts de desktop, tablet e celular.
- [ ] 4.2 Revisar validação dos formulários e guards de sessão; associar mensagens a campos acessíveis, preservar regras atuais do Xano, revalidar rotas protegidas e encerrar a sessão em HTTP 401 com redirecionamento para `/entrar`; testar mensagens, ausência de token no cliente e acesso após reload.
- [ ] 4.3 Harmonizar estados de carregamento, erro, vazio e nova tentativa nas telas de catálogo, busca e comparação; testar anúncios por tecnologia assistiva, foco visível, `prefers-reduced-motion`, contraste AA e ausência de rolagem horizontal em 320 px, tablet e desktop.
- [ ] 4.4 Atualizar README, documentação de arquitetura e contexto `openspec/config.yaml` para remover divergências sobre autenticação, busca pública, moeda e histórico; executar `openspec validate` e verificar que nenhum contrato Xano ou requisito de fase ficou contraditório.
- [ ] 4.5 Executar a suíte completa, `reflex compile` e `reflex run`; validar no navegador as rotas públicas e protegidas, comparação com/sem oferta e falha de API, histórico, favoritos, catálogo, sessão, teclado e viewports responsivos antes de reconciliar ou arquivar a mudança anterior.
