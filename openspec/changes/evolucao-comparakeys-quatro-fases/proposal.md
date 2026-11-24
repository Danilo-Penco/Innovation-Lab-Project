# Proposal

## Why

O ComparaKeys hoje abre no login, compara Steam e GOG e não oferece uma página pública de apresentação nem recursos pessoais de histórico e favoritos. Esta evolução organiza a ampliação em quatro entregas que podem ser implementadas e verificadas uma por vez, preservando a busca pública e o comportamento resiliente das integrações existentes.

## What Changes

- **F1 — Página inicial:** tornar `/` uma landing page pública responsiva e acessível; mover login para `/entrar`; manter `/cadastro`; ajustar logout, rotas protegidas e destino da marca conforme a sessão; atualizar conteúdo e documentação que hoje definem `/` como login.
- **F2 — Ofertas CheapShark e câmbio:** acrescentar até cinco ofertas de outras lojas para o mesmo Steam App ID, sem duplicar Steam/GOG; verificar primeiro se a CheapShark identifica preço em BRL e, somente se não identificar, converter preços USD para valores aproximados em BRL via Frankfurter sem chave e cachear somente a cotação por uma hora. Steam e GOG continuam usando preços reais em BRL; indisponibilidade da integração ou do câmbio não bloqueia a comparação existente.
- **F3 — Histórico:** registrar uma única vez por ação de abertura de comparação, somente para usuários autenticados; deduplicar registros consecutivos iguais no backend; oferecer listagem dos 20 últimos itens, limpeza e acesso pela página protegida `/historico` e pelo bloco de cinco itens recentes no catálogo.
- **F4 — Favoritos:** permitir listar, adicionar e remover favoritos por usuário; oferecer controles acessíveis nas comparações e cards e uma página protegida `/favoritos`; carregar o conjunto uma vez por visita, não uma vez por card.
- Para tabelas e endpoints Xano novos, versionar contratos, exemplos e prompts do Xano Agent; estender o checker com PASS/FAIL para autenticação e isolamento entre usuários. A implementação Reflex será baseada no contrato e em respostas simuladas.
- Organizar `tasks.md` em quatro fases independentes e ordenadas. Cada fase terá seu próprio gate de testes unitários, compilação Reflex e verificação do site em execução.
- Não criar nem publicar XanoScript; o plano Free não permite esse fluxo.

## Capabilities

### New Capabilities
- `landing-page`: página pública de apresentação, navegação e acesso à busca.
- `price-offers`: ofertas de lojas CheapShark e valores convertidos e claramente aproximados.
- `search-history`: histórico pessoal de comparações persistido no Xano.
- `favorites`: lista pessoal de jogos favoritos persistida no Xano.

### Modified Capabilities
- `user-authentication`: rotas públicas e protegidas, login em `/entrar`, logout e navegação da marca condicionados à sessão.
- `game-catalog`: links para histórico e favoritos e controles de favoritos nos cards; bloco recente de buscas.
- `steam-price-search`: ofertas adicionais sem bloquear Steam/GOG e persistência de histórico apenas para usuários autenticados, sem persistir preços.

## Impact

- **Reflex:** rotas, navegação compartilhada, landing page, estado de comparação, cards e páginas protegidas para histórico e favoritos.
- **Integrações externas:** API pública CheapShark e Frankfurter para referência USD/BRL; Steam e GOG permanecem fontes de preços reais em BRL.
- **Xano:** duas novas tabelas (`search_history`, `favorite`) e endpoints autenticados com identidade derivada de `$auth.id`; nenhum endpoint aceita identidade do usuário enviada pelo cliente.
- **Checker e contrato:** `docs/xano-setup.md`, `docs/xano-agent-prompts.md` e `scripts/check_xano.py` passam a cobrir os contratos novos e o isolamento por usuário.
- **Documentação e qualidade:** atualizar `README.md`, `docs/project-overview.md` e `docs/domain-model.md`; testes simulados e um gate de validação independente para cada fase.
- **Fora do escopo:** Nuuvem, integração própria da Epic, alertas, painel/admin e aprovação de lojas, notificações por e-mail/push, recuperação de senha, login social e compra no site.
