# Proposal

## Why

O ComparaKeys exige login para usar o site, mas ainda não possui um fluxo de cadastro e autenticação implementado. Sem papéis aplicados no backend, a aprovação de solicitações de loja não pode ser restrita de forma confiável a administradores.

## What Changes

- Adicionar cadastro e login de usuários usando o backend Xano.
- Definir os papéis `usuario` e `admin`; novos cadastros recebem sempre `usuario`.
- Restringir a aprovação de solicitações de loja a usuários `admin`, com autorização verificada no backend.
- Permitir o provisionamento inicial de administradores por promoção manual no Xano; não haverá seleção pública de papel nem fluxo de autoelevação.
- Exigir autenticação nas funcionalidades do site destinadas a usuários autenticados.

Ficam fora do escopo recuperação de senha, login por provedores externos, gestão de usuários por interface administrativa e alterações no fluxo completo de cadastro de solicitações de loja.

## Capabilities

### New Capabilities

- `user-auth`: cadastro e login, papéis de usuário e autorização backend para ações administrativas.

### Modified Capabilities

Nenhuma. Ainda não existem specs de capacidades no projeto.

## Impact

- Backend Xano/XanoScript: autenticação, identidade, atribuição e verificação de papel, proteção das operações autenticadas e da operação de aprovação de lojas.
- Banco de dados Xano: persistência dos usuários e seus papéis, reutilizando o mecanismo de autenticação disponível no Xano.
- Frontend HTML/CSS/JavaScript: formulários de cadastro/login e apresentação dos estados autenticado e não autenticado; controles de interface não substituem autorização no backend.
- Operação do ambiente: promoção manual no Xano da conta que será o primeiro `admin`.