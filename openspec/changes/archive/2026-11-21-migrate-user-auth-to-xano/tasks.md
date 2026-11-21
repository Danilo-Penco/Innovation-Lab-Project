# Tasks

## 1. Contrato e cliente Xano

- [x] 1.1 Consultar no design do Xano os contratos reais de entrada/saída e erros de `auth/signup`, `auth/login` e `auth/me`; registrar neste `design.md` o caminho de `authToken` e o cabeçalho de autenticação, verificando cada campo com o painel antes de iniciar a integração.
- [x] 1.2 Criar `Projeto/xano.py` para consumir somente esses três endpoints com `httpx`, `XANO_API_URL` do ambiente e timeout explícito; validar com testes de transporte simulado os payloads, token, timeout, falha de conexão e resposta inválida conforme os contratos registrados.

## 2. Fluxos de autenticação e autorização

- [x] 2.1 Atualizar `/cadastro` com Nome obrigatório e adaptar cadastro/login para os contratos Xano, preservando as mensagens atuais e limpando senha/token conforme necessário; verificar testes de estado e layout para rotas, campos, erros e transição após sucesso.
- [x] 2.2 Guardar `authToken` apenas na sessão Reflex e validar `/catalogo` com `auth/me`, incluindo token aceito/rejeitado e falha de conexão; verificar testes de acesso direto, logout, falha fechada e mensagem recuperável sem quebra de tela.

## 3. Remoção da persistência local e integração

- [x] 3.1 Após os fluxos Xano passarem nos testes, remover o serviço/modelo de usuários SQLite, configuração de banco Reflex, Alembic, testes exclusivos da persistência antiga e o banco local; verificar que não há referências ativas a SQLite/Alembic para autenticação e que a aplicação inicia sem eles.
- [x] 3.2 Atualizar `docs/project-overview.md` e `docs/domain-model.md` para documentar autenticação e persistência de usuários no Xano, sem contas migradas; revisar os documentos para remover as referências contraditórias ao SQLite.
- [x] 3.3 Executar a suíte de testes relevante e a compilação Reflex com `XANO_API_URL` configurada; validar o fluxo integrado com o serviço Xano e confirmar que `/`, `/cadastro`, `/catalogo` e a busca pública mantêm o comportamento especificado, sem criar/publicar XanoScript nem chamar `reset/*` ou `message/*`.
