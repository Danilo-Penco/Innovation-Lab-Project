# Tasks

## 1. F1 — Página inicial pública

- [x] 1.1 Mover o formulário de login de `/` para `/entrar`, atualizar guards, logout, cabeçalho e links da marca, mantendo `/cadastro`; verificar com testes de navegação os destinos para visitante e pessoa autenticada e o redirecionamento de rotas protegidas.
- [x] 1.2 Implementar a landing page pública com seção superior em tela cheia, fundo preto, “Compara Keys” centralizado na metade esquerda e capa abstrata roxa/preta de noite urbana neon à direita, sem arte protegida; verificar a barra `/` do canto inferior esquerdo ao superior direito, metades empilhadas no celular e grafismos em testes/inspeção visual.
- [x] 1.3 Implementar abaixo do hero a linha preta fina e dois quadrados pretos lado a lado com borda roxa sutil, títulos EXATOS “Quem somos” e “Objetivo do site e por que usar” e descrições institucionais; verificar conteúdo, responsividade e destinos das ações da barra superior em testes.
- [x] 1.4 Criar tokens centralizados de tema e estilos responsivos/acessíveis da landing e autenticação; verificar viewport de 320 px e desktop sem rolagem horizontal, foco visível, contraste WCAG AA e `prefers-reduced-motion`.
- [x] 1.5 Atualizar README e documentação de visão geral que identificam `/` como login; verificar que descrevem `/` pública, `/entrar` como login e `/cadastro` como cadastro.
- [x] 1.6 Executar `python -m unittest discover -s tests`; confirmar que todos os testes passam.
- [x] 1.7 Executar `reflex compile`; confirmar compilação sem erro.
- [x] 1.8 Executar `reflex run` e validar no site as rotas `/`, `/entrar`, `/cadastro`, `/buscar` e `/catalogo`, incluindo o layout móvel, ações, teclado e movimento reduzido; confirmar site funcional antes de iniciar F2.
- [x] 1.9 Adicionar à landing a barra contextual com ícone acessível e ações “Entrar”/“Cadastrar” ou “Ir para o catálogo”/“Sair”, remover CTAs redundantes e padronizar o rótulo “Cadastrar” nos specs; validar foco, contraste, teclado e uma linha sem sobreposição/rolagem em 320 px.
- [x] 1.10 Remover a seção de busca somente da landing, preservar a busca do catálogo e a rota `/buscar`, eliminar código/testes específicos sem uso e atualizar spec/documentação; verificar que a landing termina após os cards e que a busca do catálogo continua coberta.
- [x] 1.11 Tornar a barra sticky via CSS, com altura de 64 px, fundo escuro translúcido/blur e fallback sólido, divisor roxo tokenizado e espaçamento de hero sem sobreposição; atualizar spec e testar CSS sem eventos de scroll.
- [x] 1.12 Restringir a regra e validação de força da senha ao cadastro; validar no login campos preenchidos e máximo de 128 caracteres, manter falhas genéricas de credenciais, atualizar specs/testes e verificar suíte e compilação.

## 2. F2 — CheapShark e conversão cambial

- [x] 2.1 Antes da conversão, testar resposta CheapShark com `country=BR` e confirmar se há indicador explícito de BRL; implementar cliente com timeout de 10 s, `User-Agent` descritivo, uma repetição somente para erro de rede, respeito a HTTP 429/`Retry-After`, validação e cache de cinco minutos; verificar teste simulado para preço nativo BRL e erros sem retry HTTP.
- [x] 2.2 Somente se a resposta CheapShark não identificar BRL, implementar Frankfurter v2 com cache de uma hora e conversão USD/BRL via `Decimal`; verificar preço convertido com o aviso exato “valores convertidos de dólar, aproximados”, e exibição em USD quando a cotação falhar.
- [x] 2.3 Integrar ofertas à comparação, excluindo Steam/GOG e lojas inativas, ordenando preços comparáveis, limitando a cinco lojas distintas, usando link CheapShark em nova aba e destacando o menor preço/empates; verificar que falhas CheapShark e cambiais não removem os resultados Steam/GOG.
- [x] 2.4 Adicionar testes simulados para jogo sem ofertas, resposta inválida, indisponibilidade, ausência de cotação, filtragem de lojas, limite de cinco, ordenação, menor preço e preservação de preços Steam/GOG em BRL; verificar com `python -m unittest discover -s tests`.
- [ ] 2.5 Validar no navegador um link CheapShark de oferta real e o fallback visual em USD, sem depender de redirecionamento acessível por ferramentas automatizadas; registrar qualquer limitação reproduzível no resultado do teste manual.
- [x] 2.6 Executar `python -m unittest discover -s tests`; confirmar suíte completa verde.
- [x] 2.7 Executar `reflex compile`; confirmar compilação sem erro.
- [ ] 2.8 Executar `reflex run` e comparar jogos com ofertas, sem ofertas e falha de integrações; confirmar no site que Steam/GOG continuam utilizáveis e que moeda, avisos e links aparecem corretamente antes de iniciar F3.

## 3. F3 — Histórico de buscas no Xano

- [ ] 3.1 Atualizar `docs/xano-setup.md` com contrato exato de `search_history` e `POST /history`, `GET /history`, `DELETE /history`, request/response, 401, deduplicação consecutiva e `$auth.id`, no grupo Authentication e mesmo `XANO_API_URL`; verificar exemplos e header contra os testes.
- [ ] 3.2 Adicionar a `docs/xano-agent-prompts.md` o prompt pronto para colar no Xano Agent para criar a tabela e exatamente os endpoints da F3 sem publicar XanoScript; verificar que o prompt inclui Bearer, proprietário `$auth.id`, validação, limites, respostas e ausência de preços.
- [ ] 3.3 Estender `scripts/check_xano.py` com PASS/FAIL para os três endpoints F3, 401 sem token, header Bearer válido, deduplicação consecutiva e isolamento entre duas contas descartáveis; verificar execução contra workspace Xano de teste usando credenciais fora do Git e limpeza dos dados de teste.
- [ ] 3.4 Criar manualmente a tabela e os endpoints F3 pelo Xano Agent conforme os documentos, sem push/publicação de XanoScript; executar `scripts/check_xano.py` e confirmar PASS para todos os cenários antes de integrar o cliente.
- [ ] 3.5 Implementar cliente Reflex para `POST /history`, `GET /history` e `DELETE /history`; verificar com mocks corpo/resposta exatos e `Authorization: Bearer <token>` em cada rota, ausência de `user_id`, nenhum registro por digitação/visitante, 401 encerrando sessão e falha Xano sem bloquear comparação.
- [ ] 3.6 Implementar `/historico`, limpeza com confirmação e recentes do catálogo usando `GET /history`; atualizar `project-overview.md` e `domain-model.md` para registrar histórico não monetário apenas de usuários autenticados; verificar lista de 20, cinco recentes, estado vazio, retorno à comparação e escopo próprio em testes.
- [ ] 3.7 Incluir na documentação F3 a instrução explícita “Prompt do Xano Agent a colar” e o comando/configuração para executar `scripts/check_xano.py`; verificar que outra pessoa consegue seguir os passos sem credenciais versionadas.
- [ ] 3.8 Executar `python -m unittest discover -s tests`; confirmar suíte completa verde.
- [ ] 3.9 Executar `reflex compile`; confirmar compilação sem erro.
- [ ] 3.10 Executar `reflex run` e validar `/historico`, recentes no catálogo, confirmação de limpeza e comparação para visitante/autenticado; confirmar site funcional antes de iniciar F4.

## 4. F4 — Favoritos e lista de desejos no Xano

- [ ] 4.1 Atualizar `docs/xano-setup.md` com contrato exato de `favorite`, índice único composto usuário + Steam App ID e `GET /favorites`, `POST /favorites`, `DELETE /favorites/{steam_app_id}`, incluindo exemplos, resposta idempotente HTTP 200, 401 e isolamento, no grupo Authentication e mesmo `XANO_API_URL`; verificar consistência com os testes.
- [ ] 4.2 Adicionar a `docs/xano-agent-prompts.md` o prompt pronto para colar no Xano Agent para criar a tabela/índice e exatamente os endpoints F4, sem publicar XanoScript; verificar que especifica Bearer, usa `$auth.id` e não aceita `user_id` do cliente.
- [ ] 4.3 Estender `scripts/check_xano.py` com PASS/FAIL dos três endpoints de favoritos, 401 sem token, header Bearer válido, inclusão idempotente HTTP 200 e isolamento entre duas contas; verificar execução contra workspace Xano de teste e limpeza dos dados criados.
- [ ] 4.4 Criar manualmente a tabela, índice e endpoints F4 pelo Xano Agent conforme os documentos, sem push/publicação de XanoScript; executar `scripts/check_xano.py` e confirmar PASS de todos os cenários antes de integrar a interface.
- [ ] 4.5 Implementar cliente Reflex e estado favorito acessível na comparação e nos cards, redirecionando visitantes a `/entrar`; verificar com mocks os métodos, caminhos, corpos, respostas e header Bearer em cada chamada, uma carga de `GET /favorites` por página (sem chamada por card), mais `GET /history` no catálogo e `POST /history` na abertura autenticada da comparação conforme a exceção documentada.
- [ ] 4.6 Implementar `/favoritos` com capa, link para comparação, remoção e estado vazio, além dos links do cabeçalho; atualizar `domain-model.md` e README para documentar entidades, relações e favoritos; verificar proteção da rota, rótulos `aria-label`, inclusão/remoção e navegação em testes.
- [ ] 4.7 Incluir na documentação F4 a instrução explícita “Prompt do Xano Agent a colar” e o comando/configuração para executar `scripts/check_xano.py`; verificar que os passos cobrem os novos endpoints sem incluir segredos.
- [ ] 4.8 Executar `python -m unittest discover -s tests`; confirmar suíte completa verde.
- [ ] 4.9 Executar `reflex compile`; confirmar compilação sem erro.
- [ ] 4.10 Executar `reflex run` e validar `/favoritos`, os corações em cards e comparação, estado vazio e fluxo visitante/autenticado; confirmar no site uma chamada de cada listagem por visita (histórico e favoritos no catálogo, favoritos na comparação), sem chamadas por card, antes de concluir F4.
