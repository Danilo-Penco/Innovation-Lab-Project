# Design

## Context

Veja [proposal.md](./proposal.md) para motivação e [specs/user-authentication/spec.md](./specs/user-authentication/spec.md) para o contrato observável. Hoje `Projeto/auth.py` implementa cadastro e validação de credenciais em SQLite; `AuthState` em `Projeto/Projeto.py` mantém um identificador local e protege `/catalogo` consultando o banco. `rxconfig.py`, `alembic.ini`, `alembic/` e `reflex.db` fazem parte da persistência atual. `httpx` já está declarado nas dependências.

O Xano já tem os endpoints `auth/signup`, `auth/login` e `auth/me` no grupo Authentication, associados à tabela `user`. Os contratos abaixo foram conferidos nos testes reais do painel:

| Endpoint | Entrada | Sucesso | Erros relevantes |
|---|---|---|---|
| `POST auth/signup` | JSON: `name`, `email`, `password` | HTTP 200: `{"authToken":"<token>","user_id":<int>}` | HTTP 403, `code: "ERROR_CODE_ACCESS_DENIED"`, `message: "An account with this email already exists."`; HTTP 400, `code: "ERROR_CODE_INPUT_ERROR"`, `payload.param: "email"` para e-mail inválido |
| `POST auth/login` | JSON: `email`, `password` | HTTP 200: `{"authToken":"<token>","user_id":<int>}` | HTTP 403, `code: "ERROR_CODE_ACCESS_DENIED"`, `message: "Invalid Credentials."`; HTTP 400, `code: "ERROR_CODE_INPUT_ERROR"`, `payload.param: "email"` para e-mail inválido |
| `GET auth/me` | Sem corpo; header `Authorization` com o valor de `authToken` | HTTP 200: `{"id":<int>,"created_at":<ms>,"name":<string>,"email":<string>,"role":<string>}` | HTTP 401: `"Unauthorized - Authentication Required"` sem token ou `"Invalid token."` para token inválido |

O token retornado fica em `authToken`; `user_id` é um inteiro. A autenticação usa o header `Authorization` com o token como valor (sem acrescentar prefixo não especificado). O Xano não exige `name`, portanto o Reflex deve validar Nome obrigatório antes da chamada e enviá-lo como `name`. Nenhuma resposta de sucesso contém senha.

## Goals / Non-Goals

**Goals:**

- Fazer do Xano a fonte de verdade de contas e autenticação.
- Manter o token somente no estado server-side da sessão Reflex e validar `/catalogo` em cada carregamento.
- Preservar `/`, `/cadastro`, as mensagens existentes e a integridade da interface em falhas de rede.
- Remover a infraestrutura local de persistência de usuários e Alembic, sem migração de contas.

**Non-Goals:**

- Criar ou publicar XanoScript, alterar endpoints existentes ou chamar `reset/*` ou `message/*`.
- Recuperação de senha, login externo, papéis administrativos ou migração de contas SQLite.
- Alterar as rotas públicas de busca e comparação de preços.

## Decisions

1. **Consumir somente os endpoints REST existentes usando `httpx`.** Criar `Projeto/xano.py` como ponto de integração, formar os caminhos relativos `auth/signup`, `auth/login` e `auth/me` a partir de `XANO_API_URL` lida do ambiente e nunca embutir a URL no código. Usar timeout explícito e propagar falhas de transporte, timeout, configuração ou resposta inválida como erros tipados que os handlers possam apresentar; não converter falha em sucesso. Evitar qualquer dependência de geração/publicação de XanoScript.

2. **Usar os contratos reais do painel.** Validar no cliente a estrutura das respostas HTTP e extrair `authToken` diretamente dos corpos de sucesso de `signup` e `login`. Para `me`, enviar o valor do token no header `Authorization`. Mapear os erros reais listados acima para as mensagens existentes; respostas não reconhecidas não devem ser tratadas como sucesso.

3. **Manter o token no estado privado da sessão Reflex.** Após cadastro/login, extrair `authToken` conforme a resposta documentada, guardar somente o token de autenticação necessário e limpar a senha do estado. Não usar `localStorage`, não incluir o token em URLs, logs ou mensagens. O estado autenticado deve derivar da presença de um token tratado como válido; a autorização de `/catalogo` só é concedida após `auth/me` confirmar o token. Resposta de token inválido limpa a sessão; falha de rede não pode autorizar o catálogo.

4. **Preservar o comportamento das telas e mapear erros conhecidos.** Acrescentar Nome obrigatório ao formulário de `/cadastro` e enviá-lo como `name`; manter o login em `/`, as rotas e os textos de erro existentes para dados inválidos, e-mail duplicado e credenciais inválidas. Usar os códigos/campos de erro reais do Xano (a confirmar na etapa de contrato) para manter essas mensagens estáveis. Falhas de conectividade e respostas inesperadas recebem mensagem explícita de indisponibilidade e deixam a pessoa na tela atual.

5. **Remover a persistência local somente após integrar e verificar o fluxo.** Excluir o serviço/modelo de conta SQLite, configurações de conexão, configuração e migrações Alembic, dependência exclusiva e arquivo de banco local. Não criar fluxo de migração, pois não há contas a preservar. Manter as dependências SQLite/SQLAlchemy somente se ainda forem necessárias a outra parte do projeto.

## Risks / Trade-offs

- [O formato de resposta real do Xano divergir das suposições do cliente] → conferir o design do Xano e registrar os campos reais neste arquivo antes de implementar; validar as respostas com testes de contrato.
- [A indisponibilidade do Xano impedir autenticação ou impedir a validação do catálogo] → limitar tempo de espera, mostrar mensagem recuperável e falhar fechado no catálogo sem derrubar a aplicação.
- [Remover persistência local antes da validação deixar autenticação sem backend funcional] → remover SQLite/Alembic como etapa final, depois de validar chamadas, estados e guarda de rota.
- [Mensagens/códigos de erro do Xano não corresponderem aos textos atuais] → conferir os erros reais do endpoint e mapear apenas os casos conhecidos, mantendo falhas não reconhecidas explícitas como indisponibilidade.

## Migration Plan

1. Revisar o design do Xano e preencher os contratos reais de entrada, saída, token, erros e autenticação neste arquivo; não iniciar código até completar essa revisão.
2. Implementar e testar `Projeto/xano.py`, estado de sessão, formulário com Nome, login e validação de `/catalogo` usando respostas simuladas do contrato conferido.
3. Validar o fluxo integrado com `XANO_API_URL` configurada, incluindo cadastro/login, token aceito/rejeitado, duplicidade, credenciais inválidas e indisponibilidade.
4. Remover a persistência SQLite e Alembic, atualizar `docs/project-overview.md` e `docs/domain-model.md`, e executar os testes/build relevantes.
5. Não migrar os registros atuais. Em caso de rollback de código, reverter a integração sem depender de contas locais migradas; os dados locais removidos não serão restaurados.
