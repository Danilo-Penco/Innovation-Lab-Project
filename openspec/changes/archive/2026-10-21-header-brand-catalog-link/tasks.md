# Tasks

## 1. Navegação da marca

- [x] 1.1 Tornar clicável para `/catalogo` a marca do cabeçalho compartilhado sem alterar seu layout; adicionar testes cobrindo catálogo, `/buscar` e comparação e verificar os destinos no teste de componentes.
- [x] 1.2 Tornar clicável para `/catalogo` a marca do cadastro, mantendo a marca de `/` estática; adicionar testes das duas páginas e atualizar `docs/project-overview.md` para descrever o comportamento.

## 2. Verificação integrada

- [x] 2.1 Verificar que uma visita não autenticada a `/catalogo`, inclusive após selecionar a marca em uma rota pública, continua redirecionando para `/`; executar os testes relevantes de autenticação e navegação.
- [x] 2.2 Compilar a aplicação com `reflex compile --dry` e validar os artefatos com `openspec validate header-brand-catalog-link`.
