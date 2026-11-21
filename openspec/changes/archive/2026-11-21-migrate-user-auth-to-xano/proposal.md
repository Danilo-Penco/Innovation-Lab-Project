# Proposal

## Why

A autenticação atual mantém contas em SQLite no Reflex, enquanto o Xano já oferece os endpoints de autenticação associados à tabela `user`. Migrar o cadastro, o login e a validação de sessão para esses endpoints remove a persistência local de usuários e faz do Xano a fonte de verdade da identidade.

## What Changes

- Integrar o Reflex aos endpoints existentes `auth/signup`, `auth/login` e `auth/me` por HTTP, usando `XANO_API_URL` como URL base configurada no ambiente.
- Manter `/` como login e `/cadastro` como cadastro, acrescentando o campo obrigatório Nome; preservar as mensagens atuais para dados inválidos, e-mail duplicado e credenciais inválidas.
- Guardar `authToken` somente no estado da sessão Reflex e validar a sessão no backend com `auth/me` antes de liberar `/catalogo`.
- Apresentar uma mensagem clara e recuperável quando não for possível conectar ao Xano, sem derrubar a interface.
- Remover a persistência SQLite de usuários e sua infraestrutura Alembic; não migrar contas existentes.
- Atualizar a documentação de arquitetura e domínio para refletir Xano como persistência de usuários.
- Não criar nem publicar XanoScript; não usar endpoints `reset/*` ou `message/*`.

## Capabilities

### New Capabilities

Nenhuma.

### Modified Capabilities

- `user-authentication`: alterar o cadastro/login para usar a identidade do Xano, exigir Nome no cadastro, validar `/catalogo` com `auth/me` e especificar o tratamento de indisponibilidade do serviço, mantendo rotas e mensagens de erro existentes.

## Impact

- Código: estado e telas de autenticação Reflex, novo módulo HTTP `Projeto/xano.py` e remoção do serviço/modelo de usuários SQLite.
- Configuração e dependências: configuração Reflex, variável de ambiente `XANO_API_URL` e limpeza de SQLite/Alembic.
- Serviços: consumo dos endpoints existentes `POST auth/signup` (`name`, `email`, `password`), `POST auth/login` (`email`, `password`) e `GET auth/me` com token.
- Documentação: `docs/project-overview.md` e `docs/domain-model.md`.
- Contratos: os formatos reais de saída e o local exato de `authToken` ainda precisam ser conferidos no design do Xano antes da implementação; a mudança não deve presumir campos de resposta além do nome `authToken` informado.
