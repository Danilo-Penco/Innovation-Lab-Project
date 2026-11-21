# Tasks

## R0. Auditoria e correções pequenas de interface

- [ ] R0.1 Auditar `/`, `/cadastro`, `/catalogo`, `/buscar` e `/comparar` para UX, texto, responsividade e acessibilidade; registrar achados em `design.md` e corrigir os pequenos, verificando cada tela em desktop, viewport estreito e navegação por teclado.
- [x] R0.2 Ao concluir R0, executar `python -m unittest discover -s tests` e confirmar a suíte completa verde.

## R1. Cliente Xano

- [x] R1.1 Criar helper compartilhado para chamadas autenticadas e preservar `Authorization: Bearer <token>`; cobrir por teste o header exato sem imprimir o token.
- [x] R1.2 Implementar uma única nova tentativa apenas para erro de rede/timeout, nunca para 4xx; manter validação local de senha com ao menos uma letra e mapear `400` com `param=password` para mensagem própria.
- [x] R1.3 Mapear erros conhecidos por endpoint/status/código/campo; garantir mensagem que não esconda o motivo em fallback genérico e ausência de `print` de debug, token ou senha.
- [x] R1.4 Tratar 401 em rota protegida limpando a sessão e levando ao login com aviso de sessão inválida/expirada; cobrir login, signup, erros e guarda com testes.
- [x] R1.5 Ao concluir R1, executar `python -m unittest discover -s tests` e confirmar a suíte completa verde.

## R2. Cache sem persistir preços

- [x] R2.1 Adicionar cache limitado em memória, TTL máximo de 5 minutos, para resultados de busca Steam e metadados de identificação GOG; não inserir campos de preço no cache.
- [x] R2.2 Garantir consulta atual de preço em cada comparação e testar hit, expiração, limite, reinício/ausência de persistência e renovação de preços.
- [x] R2.3 Atualizar `docs/project-overview.md` e `docs/domain-model.md` para diferenciar cache efêmero de armazenamento/histórico de preços.
- [x] R2.4 Ao concluir R2, executar `python -m unittest discover -s tests` e confirmar a suíte completa verde.

## R3. Formulários

- [x] R3.1 Exibir em login e cadastro a regra “mínimo de 8 caracteres e ao menos uma letra” e adicionar controle acessível por teclado para mostrar/ocultar, inicialmente oculto.
- [x] R3.2 Cobrir regra e alternância de senha, rótulos, foco e limpeza do segredo com testes de autenticação/layout.
- [x] R3.3 Ao concluir R3, executar `python -m unittest discover -s tests` e confirmar a suíte completa verde.

## R4. Persistência e validação da sessão

- [x] R4.1 Testar login seguido de reload e confirmar nova validação de sessão por `auth/me`; registrar o comportamento atual.
- [x] R4.2 Se a sessão não sobreviver ao reload, implementar persistência server-side com identificador opaco e cookie `HttpOnly`, `Secure` em HTTPS e `SameSite` apropriado; comprovar que o token não fica em `localStorage`, JavaScript, URLs ou logs.
- [x] R4.3 Testar recarga, sessão inválida/401 com aviso e falha de rede com acesso fechado e mensagem recuperável.
- [x] R4.4 Ao concluir R4, executar `python -m unittest discover -s tests` e confirmar a suíte completa verde.

## R5. Automação e contrato Xano

- [x] R5.1 Criar `docs/xano-agent-prompts.md` com prompts prontos separados para tornar `name` obrigatório no signup, remover `reset/*` e `message/*`, e criar tabelas/endpoints para funcionalidades futuras documentadas; instruir que toda identidade autenticada venha do token, nunca de `user_id` do cliente.
- [x] R5.2 Manter `docs/xano-setup.md` como contrato versionado no GitHub, incluindo tabelas, campos, endpoints e exemplos de entrada/saída; regenerar o código do grupo de API somente como passo opcional, sem exigir export manual do workspace.
- [x] R5.3 Criar `scripts/check_xano.py`, lendo `XANO_API_URL`, `XANO_TEST_EMAIL` e `XANO_TEST_PASSWORD` do `.env`; imprimir PASS/FAIL por endpoint para signup sem `name` recusado, endpoints autenticados com 401 sem token e rotas `reset/*`/`message/*` ausentes, nunca imprimindo senha/token ou respostas integrais.
- [x] R5.4 Documentar no README como configurar o `.env` sem commitar segredos e executar o checker; validar o script com uma instância de teste e confirmar os resultados por endpoint.
- [x] R5.5 Ao concluir R5, executar `python -m unittest discover -s tests` e confirmar a suíte completa verde; executar também `python scripts/check_xano.py` no ambiente de teste e revisar que nenhum segredo é impresso.
