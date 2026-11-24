# Design

## Context

Consulte [proposal.md](./proposal.md) para motivação e escopo e os sete delta specs para contratos observáveis. A aplicação atual usa Reflex em `Projeto/Projeto.py`; `/` é a landing page pública, `/entrar` é login, `/cadastro` é cadastro e `/catalogo` é protegido. Busca e comparação públicas são estados Reflex em `/buscar` e `/comparar`; integrações Steam, GOG e Xano já ficam em módulos separados, e existe cache TTL apenas em memória.

Restrições: não publicar XanoScript; toda autorização e filtragem por proprietário deve ocorrer no backend Xano usando `$auth.id`; evitar chamadas Xano redundantes e chamadas por tecla/card, com a exceção de duas leituras independentes no catálogo e na comparação em F4 para cumprir os contratos exatos de histórico e favoritos; uma falha Xano, CheapShark ou cambial não pode bloquear a comparação Steam/GOG; nenhuma credencial ou dado de teste real vai para Git.

## Goals / Non-Goals

**Goals:**
- Entregar cada fase como uma fatia testável, mantendo as fases posteriores fora do escopo de uma execução de apply.
- Preservar a busca pública e os preços reais Steam/GOG em BRL enquanto amplia apresentação e personalização.
- Manter histórico e favoritos isolados no Xano por usuário autenticado, sem enviar `user_id` como autoridade.
- Manter ofertas e cotações temporárias em memória e não gravar preços ou credenciais em armazenamento persistente.

**Non-Goals:**
- Criar ou publicar XanoScript, persistir preços, criar compras, integração própria da Epic, outras lojas fora do CheapShark, ou funcionalidades de autenticação novas.
- Transformar a taxa de câmbio de referência em cotação para compra ou apresentar preço convertido como preço local confirmado.

## Decisions

### F1 — Rotas, página pública e tema

- Manter `/` como landing page pública, criar `/entrar` para login e conservar `/cadastro`. Atualizar redirecionamentos de logout e de guardas de rotas para `/entrar`; a marca aponta ao catálogo com sessão e à landing page sem sessão.
- Construir a seção superior como hero de tela cheia, com fundo preto, “Compara Keys” centralizado na metade esquerda e grafismos abstratos roxos/pretos de noite urbana neon na metade direita. Separar as metades com uma barra diagonal `/`, do canto inferior esquerdo ao superior direito; no celular, empilhar as metades. Usar gradientes e formas CSS próprias, sem depender de arte de jogos. Abaixo, colocar a linha preta fina e os dois cards pretos com borda roxa sutil e títulos exatos. Isso evita carregamento externo e mantém a identidade visual autoral.
- Colocar antes do hero uma barra sticky de 64 px com ícone de controle à esquerda ligado a `/` e ações condicionais à direita (“Entrar”/“Cadastrar” para visitante; “Ir para o catálogo”/“Sair” com sessão). Usar fundo preto translúcido com blur quando suportado, fallback preto sólido e separador inferior de 1 px no token roxo discreto. A barra fica apenas na landing, sem handlers de scroll; o hero começa abaixo dela e mantém a altura total da primeira tela. Após os dois cards, a página termina sem seção de busca. Em 320 px a barra fica numa linha sem sobrepor o conteúdo.
- Centralizar cores e estados visuais num módulo de tema reutilizável e manter componentes Reflex, com comportamento de foco e `prefers-reduced-motion` coerentes com o CSS global. Confirmar contraste AA em teste visual, não apenas por snapshots.

### F2 — CheapShark, preço USD e conversão

Pesquisa de API pública feita em 21/11/2026:

| Consulta | Resultado observado |
|---|---|
| `GET https://www.cheapshark.com/api/1.0/games?steamAppID=620` | Lista com `gameID`, `steamAppID`, `cheapest`, `cheapestDealID`, `external`, `internalName` e `thumb`; para Portal 2, `gameID` era `"36"` e `cheapest` `"9.99"`. |
| `GET .../games?id=36` | Objeto com `info`, `cheapestPriceEver` e `deals`; cada deal observado contém `storeID`, `dealID`, `price`, `retailPrice` e `savings`. |
| `GET .../deals?steamAppID=620&pageSize=60` | Lista com `salePrice`, `normalPrice`, `storeID`, `dealID`, `steamAppID`, `title` e outros metadados; o exemplo retornou somente Steam (`storeID` `"1"`). |
| `GET .../deals?steamAppID=292030&pageSize=60` | Retornou GOG (`storeID` `"7"`) e Steam (`"1"`), que devem ser excluídas do bloco adicional. |
| `GET .../deals?steamAppID=369000&pageSize=60` | Retornou seis ofertas para Pongo; entre elas DreamGame (`"35"`), Gamesplanet (`"27"`), Fanatical (`"15"`), Steam (`"1"`), IndieGala (`"30"`) e GamersGate (`"2"`). É um caso útil para teste de múltiplas lojas. |
| `GET .../games?steamAppID=620&country=BR` | Teste real: retornou Portal 2 com `cheapest: "9.99"` e sem campo de moeda/indicador explícito de BRL. |
| `GET .../deals?steamAppID=369000&pageSize=60&country=BR` versus `country=US` | Teste real: os dois retornaram os mesmos seis `dealID` e preços (`0.10`, `0.14`, `0.24` e `0.99`); os objetos não contêm campo de moeda. O teste não demonstrou preço regional BRL. |
| `GET .../stores` | Retorna `storeID`, `storeName`, `isActive` e caminhos de imagem; usar `isActive` e o catálogo de lojas para nomes e exclusão. |

A documentação oficial CheapShark informa API pública sem chave, limite de `pageSize` de 60, paginação indexada em zero, obrigação de enviar `User-Agent` descritivo e possibilidade de bloqueio temporário HTTP 429 com prazo em `Retry-After`. Também exige que destinos de ofertas usem os links CheapShark. O redirecionamento será montado como `https://www.cheapshark.com/redirect?dealID=<dealID-url-encoded>`; a ferramenta de pesquisa recebeu HTTP 403 ao abrir um desses redirecionamentos, portanto F2 deve validar o link real em navegador durante a verificação de ponta a ponta. Não trocar por link direto ou link afiliado próprio.

Primeiro inspecionar cada oferta CheapShark por um indicador explícito de BRL. Se existir, apresentar o valor nativo sem conversão. Os testes reais de 21/11/2026 não encontraram indicador de moeda e `country=BR` retornou os mesmos preços de `country=US`; portanto os dados verificados não demonstraram suporte a preços BRL. Para ofertas sem BRL, usar a moeda USD da API e converter via Frankfurter; não inferir BRL pelo valor numérico.

Fonte cambial real testada em 21/11/2026: Frankfurter v2 `GET https://api.frankfurter.dev/v2/rate/usd/brl` respondeu `{"date":"2026-11-21","base":"USD","quote":"BRL","rate":5.9079}`. A taxa é de referência, adequada somente para exibição aproximada, não cotação de transação. Cachear em memória por uma hora. Mostrar o aviso visível exato “valores convertidos de dólar, aproximados”; se câmbio falhar, mostrar `US$` e manter Steam/GOG. Fazer cálculo e arredondamento a centavos com `Decimal`.

Para minimizar chamadas CheapShark, fazer uma consulta por carregamento de comparação, pedindo até 60 resultados ordenados por preço, filtrar lojas ativas exceto IDs de Steam/GOG e mostrar até cinco lojas distintas. Se não houver resultados válidos suficientes, apresentar apenas os disponíveis; nunca fazer varredura automática do catálogo. Cachear resultados em memória por no máximo cinco minutos; nenhum preço vai a banco ou arquivo. Sempre consultar Steam e GOG no fluxo atual.

Cachear a resposta de ofertas em memória por no máximo cinco minutos; o preço presente nesse cache é volátil e nunca vai a banco ou arquivo. Cachear separadamente a taxa USD/BRL por uma hora. Sempre consultar Steam e GOG no fluxo atual; o cache CheapShark não substitui nem altera os seus preços.

Foram testadas duas fontes públicas sem chave:

- Frankfurter v2 `GET https://api.frankfurter.dev/v2/rate/usd/brl`: em 21/11/2026 respondeu `{"date":"2026-11-21","base":"USD","quote":"BRL","rate":5.9079}`. Sua documentação descreve taxas de referência de bancos centrais/fontes oficiais, atualizações ao longo do dia, sem cotas diárias/mensais e limitação apenas para abuso.
- AwesomeAPI `GET https://economia.awesomeapi.com.br/json/last/USD-BRL`: respondeu objeto `USDBRL` com `bid`, `ask`, `high`, `low`, `timestamp` e `create_date`; na consulta de 20/11/2026, `bid` era `"5.9488"` e `ask` `"5.9493"`.

Escolher Frankfurter v2 como fonte primária: tem esquema simples e documenta explicitamente que são taxas de referência, apropriadas para a exibição aproximada, não cotações de transação. Não escolher AwesomeAPI como fallback automático, pois bid/ask representam outra semântica e misturá-las tornaria o valor menos consistente. Se Frankfurter falhar, mostrar o preço original `US$` e conservar Steam/GOG. Fazer cálculo e arredondamento a centavos com `Decimal`.

Usar timeout de 10 segundos e uma nova tentativa somente em erro de rede. Não repetir 4xx/5xx nem 429; usar `Retry-After` para evitar chamada antes do prazo quando disponível. Todo erro de integração deve ser recuperável e jamais cancelar resultados já válidos da Steam ou GOG.

### F3/F4 — Contratos Xano e limite de uma chamada por ação

Manter as tabelas novas e os endpoints no grupo Authentication existente e usar o `XANO_API_URL` já configurado. Todas as rotas autenticadas exigem `Authorization: Bearer <token>`; o Xano deriva o proprietário exclusivamente de `$auth.id`, e os corpos não contêm `user_id`.

Contrato inicial a registrar em `docs/xano-setup.md`:

| Tabela | Campos e tipos/limites | Restrições |
|---|---|---|
| `search_history` | `id` inteiro; `user` relação com `user`; `term` texto até 100 caracteres; `steam_app_id` inteiro positivo; `game_name` texto até 200 caracteres; `created_at` timestamp gerado no servidor | Índices por `user` e `created_at`; sem preço. Mesmo Steam App ID do registro mais recente do usuário atualiza esse registro e `created_at` em vez de duplicar. |
| `favorite` | `id` inteiro; `user` relação com `user`; `steam_app_id` inteiro positivo; `game_name` texto até 200; `cover_url` texto HTTPS até 2048; `created_at` timestamp do servidor | Restrição única (`user`, `steam_app_id`); validar URL de capa contra hosts de capa Steam aceitos. |

Endpoints previstos (corpos não incluem `user_id`):

| Método e endpoint | Entrada | Saída de sucesso |
|---|---|---|
| Método e endpoint | Entrada | Resposta |
|---|---|---|
| `POST /history` | `{term, steam_app_id, game_name}` | `{"id": N}`; deduplicar comparando com o registro mais recente de `$auth.id`, atualizando esse registro quando o Steam App ID coincide. |
| `GET /history` | Nenhuma | Array de `{id, term, steam_app_id, game_name, created_at}`, máximo 20 do usuário atual, mais recentes primeiro. |
| `DELETE /history` | Nenhuma | `{"deleted": N}` para os registros do usuário atual. |
| `GET /favorites` | Nenhuma | Array de `{id, steam_app_id, game_name, cover_url, created_at}` do usuário atual. |
| `POST /favorites` | `{steam_app_id, game_name, cover_url}` | O objeto favorito `{id, steam_app_id, game_name, cover_url, created_at}`; inclusão repetida retorna o favorito existente com HTTP 200. |
| `DELETE /favorites/{steam_app_id}` | Steam App ID no caminho | `{"deleted": true}` ao remover o favorito próprio. |

Todos os endpoints acima são do grupo Authentication, usam a base `XANO_API_URL` existente, exigem o header Bearer e filtram por `$auth.id`. Usar índice único composto (`user`, `steam_app_id`) em `favorite`; não aceitar identidade enviada pelo cliente.

O contrato exato não contém endpoint agregado. Portanto, em F4, a visita ao catálogo faz uma chamada `GET /history` para recentes e uma `GET /favorites` para pintar os corações; a abertura de comparação autenticada faz `POST /history` e uma `GET /favorites` para o coração da comparação. Essa é uma exceção deliberada ao limite anterior de uma chamada por ação, escolhida para manter os endpoints e formatos solicitados. Cada ação explícita de listar, limpar, adicionar ou remover executa somente a chamada correspondente; nenhum card dispara sua própria requisição. `GET /history` e `GET /favorites` continuam sendo chamados no máximo uma vez cada por visita à página.

O checker usará duas contas descartáveis de teste, configuradas fora do Git, para provar 401 sem token, header Bearer válido, isolamento entre usuários, respostas exatas e idempotência; fará limpeza dos dados de teste.

### Estratégia de verificação

- Testes unitários simulam HTTP com `httpx.MockTransport`; verificam método, caminho, corpo e `Authorization: Bearer <token>` em cada endpoint sem expor o token; não dependem de preços atuais nem de Xano de produção.
- O checker executado manualmente contra uma instância descartável de teste valida respostas e PASS/FAIL por endpoint, 401 sem token, identidade do `$auth.id`, isolamento de duas contas e ausência de segredos na saída. F3/F4 registram em seus tasks o prompt exato a colar no Xano Agent e o comando do checker.
- A CLI instalada confirma `reflex compile` como comando de compilação. Cada fase deve concluir o conjunto completo `.\.venv\Scripts\python.exe -m unittest discover -s tests`, `.\.venv\Scripts\reflex.exe compile` e uma execução de `.\.venv\Scripts\reflex.exe run` seguida de smoke test das rotas e do comportamento visual/teclado em viewport estreito e desktop antes de iniciar a próxima fase.

## Risks / Trade-offs

- [A API pode mudar, limitar ou omitir uma loja para determinado Steam App ID] → validar esquema, `isActive`, moeda/valores e `dealID`; uma falha remove apenas o bloco CheapShark, não os resultados Steam/GOG.
- [CheapShark não informa moeda no JSON observado e o link de redirecionamento retornou 403 na ferramenta de pesquisa] → documentar a premissa USD, não exibir conversão como preço real, usar o formato oficial baseado em `dealID` e validar a navegação em navegador durante F2.
- [Taxa Frankfurter é de referência e pode estar atrasada em relação a mercado] → rotular todo valor como aproximado, manter cotação por até uma hora e mostrar USD se indisponível.
- [Novos endpoints Xano podem aceitar identidade enviada pelo cliente por engano] → todas as regras por proprietário usam `$auth.id`; checker e testes com duas contas verificam isolamento antes de aceitar a fase.
- [Uma consulta múltipla pode exceder limite Free do Xano ou CheapShark] → nunca consultar em `on_change`, agrupar estado do catálogo, limitar cada página a uma leitura e fazer uma consulta CheapShark por comparação; honrar 429 sem retry automático.
- [A mudança de `/` para `/entrar` pode deixar links antigos apontando ao login] → atualizar cabeçalho, callbacks, documentos e testes de rotas na F1; preservar `/` como landing e redirecionar todos os guards/logout para `/entrar`.

## Migration Plan

1. Aplicar somente F1, validar os gates e publicar a landing/rotas sem alterar contratos Xano.
2. Em ambiente de teste, aplicar F2 e validar respostas/link CheapShark e câmbio; atualizar o site e verificar fallback antes de habilitar a integração.
3. Criar manualmente `search_history` e endpoints pelo Xano Agent conforme contrato versionado; rodar checker com duas contas descartáveis, depois aplicar e validar F3.
4. Criar manualmente `favorite` e endpoints conforme contrato; estender agregados/saída de comparação, rodar checker e validar F4.
5. Publicar apenas após todos os gates da fase correspondente. Em rollback de F3/F4, desabilitar os links/controles e as chamadas Reflex; manter tabelas e registros Xano para evitar exclusão acidental de dados. F2 pode ser desabilitada removendo só o bloco adicional de ofertas.

## Open Questions

Nenhuma. A API Meta do Xano documenta índices do tipo `unique` sobre múltiplos campos; a configuração do índice composto de `favorite` será feita manualmente no workspace, sem publicar XanoScript.
