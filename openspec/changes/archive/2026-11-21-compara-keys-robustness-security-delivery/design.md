# Design

## Context

Consulte [proposal.md](./proposal.md) para motivação e `specs/` para os contratos observáveis. A aplicação Reflex mantém o token em estado server-side e valida o catálogo por `auth/me`. O header autenticado correto foi confirmado no Xano real como `Authorization: Bearer <token>`; deve ser preservado e coberto por teste. O cliente atual ainda precisa de uma fronteira compartilhada para chamadas autenticadas, retry seletivo e erros com motivo explícito.

Steam e GOG têm clientes separados e não possuem cache. A resposta GOG atual combina dados do produto e preço, portanto o cache não pode reter nem reutilizar o valor monetário. O repositório já mantém documentação e um workspace Xano versionado; o fluxo futuro será guiado por contrato e prompts para o Xano Agent, com verificação automatizada contra a instância configurada, não por export manual obrigatório.

### Verificação da sessão após recarga

O fluxo foi exercitado no servidor Reflex em modo de produção com um Xano local simulado, sem usar credenciais ou token reais. Após o login, `/catalogo` abriu; uma recarga completa manteve a página protegida acessível. A rota registra `AuthState.guard_catalog` em `on_load`, e um teste de regressão chama a guarda novamente na mesma sessão e confirma uma nova chamada a `auth/me`. A inspeção do navegador confirmou que o token Xano de teste não apareceu na URL nem no armazenamento Web; o estado Reflex manteve a sessão no servidor. Portanto, a persistência Reflex existente já atende à recarga e não foi adicionada uma segunda camada de cookie/sessão. No momento desse teste interativo, as credenciais de teste ainda não estavam configuradas; a instância real foi verificada depois, conforme o resultado registrado abaixo.

### Verificação do contrato Xano

O checker foi executado no workspace de teste autorizado, usando a conta configurada localmente e sem imprimir credenciais ou respostas integrais. Login retornou HTTP 200; `auth/me` retornou 401 sem token e 200 com a sessão de teste. Signup sem corpo retornou HTTP 400, mas sem identificar `payload.param=name`; o resultado foi SKIP, sem concluir que a obrigatoriedade de `name` foi comprovada. `POST /message/send_welcome_email` e `POST /reset/update_password` responderam HTTP 400, portanto foram reportados como rotas existentes. `POST /reset/magic-link-login` e `GET /reset/request-reset-link` responderam HTTP 500 e foram reportados como SKIP, sem concluir ausência. Os probes legados não enviaram e-mail, token, senha ou credenciais e não criaram registros. O workspace ainda requer as alterações descritas em `docs/xano-agent-prompts.md`.

### Auditoria de telas

| Tela/estado | Problema encontrado | Resultado |
|---|---|---|
| `/` | O login não informa a regra de senha e não oferece mostrar/ocultar senha. | Registrado para R3, junto com a regra e o controle acessível. |
| `/cadastro` | O texto informa apenas o tamanho mínimo, não a exigência de uma letra; não há controle para mostrar/ocultar senha. | Registrado para R3, junto com a regra e o controle acessível. |
| Transição de autenticação | A mensagem da splash não era anunciada como status. | R0: adicionado `role="status"` sem alterar a duração ou o fluxo. |
| `/catalogo` | A busca mantinha campo e botão lado a lado em telas estreitas; o cabeçalho usava espaçamento horizontal fixo. | R0: busca empilhada em viewport estreito e espaçamento do cabeçalho adaptável. |
| `/buscar` | Estados de carregamento/erro e ausência de resultados não eram anunciados; a atualização por digitação não declarava um debounce explícito. | R0: estados com semântica de status/alerta, campo com debounce de 300 ms e proteção contra respostas obsoletas. |
| `/comparar` | O carregamento e erros não tinham semântica explícita para tecnologia assistiva; o menor preço dependia apenas de cor. | R0: carregamento/erros anunciados e rótulo textual “Menor preço”. |
| Estilo compartilhado | O efeito `glow` podia se repetir indefinidamente e não respeitava movimento reduzido; o foco de teclado não era explicitamente destacado. | R0: movimento reduzido respeitado e indicador `:focus-visible` definido. |

A auditoria de código cobriu `/`, `/cadastro`, `/catalogo`, `/buscar` e `/comparar`, incluindo os estados de transição, carregamento, erro e resultado. Os testes estruturais e a compilação passaram. A validação visual interativa ficou incompleta: o servidor de produção exibiu erro de conexão no navegador e não permitiu verificar todas as rotas em viewport estreito e com teclado; R0.1 permanece aberto até essa verificação. A regra e a alternância de senha permanecem no escopo da fase R3.

## Goals / Non-Goals

**Goals:**

- Fazer chamadas autenticadas reutilizarem um helper que aplique exatamente `Authorization: Bearer <token>`.
- Distinguir erros de rede/timeout, erros 4xx conhecidos e erros 4xx desconhecidos; nunca ocultar a causa em mensagem genérica nem emitir prints de debug.
- Manter preços atualizados em cada comparação, mesmo ao reutilizar resultados/metadados em cache.
- Verificar a sessão após reload antes de adicionar persistência; se necessário, mantê-la no servidor e expor apenas identificador opaco com cookie seguro.
- Entregar prompts operacionais e um verificador que consulte o contrato Xano versionado, sem obrigar export manual.

**Non-Goals:**

- Implementar ou alterar endpoints Xano nesta revisão dos artefatos.
- Adicionar novas lojas, notificações por e-mail/push, histórico ou persistência de preços.
- Colocar tokens, senhas ou URLs privadas em código, logs, argumentos de linha de comando ou documentação de exemplo.

## Decisions

1. **Helper compartilhado para chamadas autenticadas.** Centralizar montagem do header e a execução HTTP autenticada num helper reutilizável pelos endpoints protegidos; o valor do header é `Bearer ` seguido do token Xano real. Não remover o prefixo. Um teste de contrato deve verificar exatamente o esquema Bearer sem expor o segredo no output.

2. **Retry e mapeamento de erro no cliente Xano.** Repetir no máximo uma vez apenas em exceção de rede ou timeout. Nunca repetir 4xx. Mapear pelo endpoint, status, código Xano e `payload.param`; em particular `400` com `param=password` tem mensagem própria e a validação local mantém a exigência de ao menos uma letra. 401 ao validar rota protegida deve invalidar/encerrar sessão e retornar ao login com aviso claro de sessão expirada. Outros erros precisam de mensagem explicativa baseada no motivo/status/código, sem fallback genérico que esconda a causa e sem imprimir detalhes de debug, token ou senha.

3. **Cache curto, limitado e sem valores monetários.** Usar cache em memória do processo, TTL máximo de 300 segundos, chave por termo normalizado e parâmetros regionais, relógio monotônico e capacidade limitada. Resultados de busca Steam e metadados de identificação GOG podem ser retidos; campos de preço não podem entrar no cache. Como o endpoint atual GOG une metadados e preço, cada comparação precisa obter resposta atual e reutilizar apenas metadados já normalizados, sem economizar chamadas à custa de preço desatualizado.

4. **Sessão: testar primeiro, persistir server-side se necessário.** O estado de sessão Reflex atual permanece como primeira opção se o teste provar que sobrevive a reload e workers suportados. Se não sobreviver, armazenar token apenas no servidor e usar identificador de sessão opaco em cookie `HttpOnly`, `Secure` em HTTPS e `SameSite` apropriado. Não usar `localStorage` ou cookie JavaScript-acessível para o token. Em 401 protegido, limpar a sessão e redirecionar ao login com aviso; em falha de rede/timeout, manter acesso fechado e exibir o motivo recuperável.

5. **Automação Xano dirigida pelo contrato versionado.** `docs/xano-setup.md` registra tabelas, campos, endpoints e exemplos de entrada/saída; `docs/xano-agent-prompts.md` contém prompts independentes para tornar `name` obrigatório no signup, remover rotas `reset/*` e `message/*`, e criar tabelas/endpoints das funcionalidades futuras já especificadas. Todo endpoint autenticado deve derivar a identidade do token, nunca de `user_id` enviado pelo cliente. `scripts/check_xano.py` lê configuração e credenciais de teste do `.env`, solicita token sem imprimi-lo, mascara credenciais e apresenta PASS/FAIL por endpoint para os contratos verificados. O uso fica documentado no README. Regenerar o código do grupo de API pode ser instruído como passo opcional, sem export manual obrigatório.

6. **Correções pequenas de UI em componentes existentes.** Preservar rotas e fluxo, adicionando instruções completas de senha, alternância por teclado, status/alertas, indicação textual de menor preço, adaptação responsiva e suporte a movimento reduzido. Não introduzir outra biblioteca visual.

## Risks / Trade-offs

- [O retry do signup pode ocorrer após o Xano criar a conta e a resposta se perder] → limitar a uma repetição e mapear corretamente a duplicidade, sem tentativas ilimitadas nem sucesso presumido.
- [O endpoint GOG combina preço e metadados] → cachear somente os campos não monetários e obter resposta atual para cada comparação.
- [O estado Reflex pode sobreviver ao reload apenas no mesmo worker] → testar recarga e comportamento multi-worker; persistência adicional somente server-side.
- [O script de verificação pode revelar credenciais em mensagens de erro HTTP] → nunca imprimir request/response completos, token ou senha; emitir apenas endpoint, status/código sanitizado e PASS/FAIL.
- [Rotas removidas ou protegidas variam conforme funcionalidades documentadas] → manter no contrato uma lista explícita de endpoints para testar e exigir atualização sincronizada dessa lista ao mudar o workspace.
- [Contrato versionado divergir da instância Xano] → rodar `scripts/check_xano.py` contra a instância configurada e atualizar contrato e prompts na mesma alteração.

## Migration Plan

1. R0: concluir auditoria de interface e registrar/corrigir pequenos problemas; executar a suíte completa.
2. R1: centralizar chamadas Xano autenticadas, manter Bearer, retry seletivo, mapeamentos e fluxo 401; executar a suíte completa.
3. R2: adicionar cache de resultados/metadados sem preço e testar expiração/limites; executar a suíte completa.
4. R3: melhorar formulários e acessibilidade; executar a suíte completa.
5. R4: testar reload e implementar persistência server-side somente se necessária; executar a suíte completa.
6. R5: versionar contrato, prompts, checker e documentação do README; validar em instância de teste e executar a suíte completa. Regeneração do grupo de API é opcional. Nenhuma fase exige export manual do workspace.

Rollback remove cache/persistência nova ou reverte cliente sem alterar os contratos existentes e sem deixar segredos nos arquivos.
