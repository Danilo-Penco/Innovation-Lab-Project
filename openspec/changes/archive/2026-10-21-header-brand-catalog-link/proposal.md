# Proposal

## Why

A marca ComparaKeys identifica a aplicação, mas não oferece uma navegação consistente de volta ao catálogo. Tornar a marca um acesso previsível ao menu principal facilita retornar de cadastro, busca e comparação sem alterar o fluxo de autenticação nem a proteção existente do catálogo.

## What Changes

- Tornar clicável a marca “ComparaKeys” exibida no cabeçalho compartilhado, navegando para `/catalogo`.
- Tornar clicável para `/catalogo` a marca exibida em `/cadastro`; manter a marca da tela de login `/` como texto e ícone sem link.
- Preservar a proteção atual de `/catalogo`: pessoas sem sessão que navegam até essa rota continuam sendo redirecionadas para o login.
- Manter inalterado o layout do cabeçalho.

## Capabilities

### New Capabilities

### Modified Capabilities

- `user-authentication`: definir o comportamento do link da marca entre as telas de autenticação, catálogo e rotas públicas que exibem o cabeçalho, sem alterar a regra de acesso protegido ao catálogo.

## Impact

- Componente visual compartilhado do cabeçalho e marca das páginas de autenticação no frontend Reflex.
- Navegação para a rota existente `/catalogo`; nenhuma API, dependência, banco de dados ou integração Xano será alterada.
- A rota `/catalogo` mantém sua autorização atual no backend Reflex.

Fora de escopo: mudanças no layout do cabeçalho e alterações no Xano.
