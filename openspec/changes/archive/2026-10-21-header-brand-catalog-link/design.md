# Design

## Context

Ver [proposal.md](./proposal.md) para a motivação. O cabeçalho existente é compartilhado pelo catálogo, busca pública e comparação de preços; sua marca é atualmente composta por ícone e texto sem navegação. As páginas de autenticação usam uma marca visual própria dentro dos cartões, e a rota de login não renderiza o cabeçalho. O catálogo já possui uma verificação de sessão no servidor Reflex que redireciona visitantes não autenticados para `/`.

## Goals / Non-Goals

**Goals:**

- Reutilizar a rota protegida `/catalogo` como destino da marca.
- Tornar a marca do cadastro navegável sem criar um cabeçalho novo ou alterar o layout.
- Preservar uma marca não interativa no login e preservar a autorização existente.

**Non-Goals:**

- Alterar espaçamento, alinhamento ou estilo do cabeçalho.
- Alterar comportamento de login, logout, autorização, APIs ou Xano.

## Decisions

1. **Envolver a marca do cabeçalho compartilhado em navegação para `/catalogo`.** O mesmo componente é usado no catálogo, `/buscar` e comparação; alterar esse ponto cobre as três telas e mantém a identidade visual existente. Alternativa: adicionar links por rota; rejeitada por duplicar comportamento e permitir inconsistências.

2. **Manter o login estático e habilitar a navegação somente na marca do cadastro.** O login não renderiza o cabeçalho compartilhado e sua marca deve permanecer inerte; a marca do cadastro pode reutilizar a aparência existente com uma ação de navegação. Isso evita introduzir uma ação de saída da tela de login que não foi solicitada.

3. **Não implementar uma autorização nova no link.** O destino continua sendo `/catalogo`; a guarda de sessão atual é a fonte de controle e redireciona visitantes não autenticados para `/`. Alternativa: ocultar ou desabilitar o link conforme a sessão; rejeitada porque conflita com o requisito de navegação uniforme e duplicaria a regra de autorização no frontend.

## Risks / Trade-offs

- [Um link pode alterar foco ou aparência padrão da marca] → Preservar estilos e dimensões atuais e validar por teste de componente e navegação por teclado.
- [A navegação pública para `/catalogo` pode ser confundida com acesso irrestrito] → Manter e testar a guarda de sessão no servidor sem mudanças.

## Migration Plan

Não há migração de dados nem mudança de rota. A reversão consiste em remover a ação do link mantendo o componente visual e a proteção atual do catálogo.
