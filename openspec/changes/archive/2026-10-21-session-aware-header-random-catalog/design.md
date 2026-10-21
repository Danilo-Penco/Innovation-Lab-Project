# Design

## Contexto

Consulte [proposal.md](./proposal.md) para a motivação e [specs](./specs/) para o contrato observável. Hoje `AuthState` mantém a identidade da sessão e valida o acesso ao catálogo; a função compartilhada `navbar()` sempre renderiza “Entrar”. `CatalogState.prepare_page` é executado ao carregar `/catalogo`, mas limpa apenas o erro de pesquisa. Os exemplos ficam em `Projeto/catalog.py` e a página os apresenta em uma única grade.

## Objetivos / Não objetivos

**Objetivos:**
- Derivar as ações do cabeçalho do estado de autenticação existente e encerrar a sessão no backend antes de redirecionar.
- Sortear a seleção e o destaque durante a preparação de cada carregamento do catálogo.
- Preservar a estrutura de dados fixa, o texto alternativo e a navegação de pesquisa existente, acrescentando um fallback legível para capas indisponíveis.

**Não objetivos:**
- Alterar a persistência, o método de autenticação ou os controles de acesso já aplicados no backend Reflex.
- Tornar os exemplos dinâmicos ou buscar preços, popularidade e promoções.
- Migrar o catálogo ou a autenticação para o Xano.

## Decisões

1. **Manter o estado de autenticação como fonte do cabeçalho.** A função comum do cabeçalho decide entre “Entrar” e “Sair” pela identidade autenticada já mantida em `AuthState`; “Sair” limpa a identidade e os indicadores derivados de autorização antes de redirecionar para `/`. A mesma função atende às páginas que já exibem o cabeçalho, inclusive `/buscar`. A checagem de autorização do catálogo continua independente e no backend; ocultar ou exibir um botão não concede acesso. Isso evita introduzir outro mecanismo de sessão ou acoplar a rota pública à proteção do catálogo.
2. **Sortear no evento de carregamento, não na renderização.** `CatalogState.prepare_page` seleciona oito entradas distintas de `CATALOG_GAMES` e escolhe uma delas como destaque. O estado mantém a seleção para a renderização daquela carga, e a próxima entrada na rota executa novo sorteio. A lista continua sendo fixa e deve conter pelo menos 12 jogos; o destaque pertence à seleção exibida, garantindo oito jogos no total sem duplicação.
3. **Separar a apresentação do destaque e da grade sem duplicar os dados.** A página usa o mesmo modelo `CatalogGame` e componentes de cartão para o destaque e os demais itens, com dimensões visuais apropriadas a cada apresentação. O nome permanece visível independentemente da capa.
4. **Tratar erro de imagem por capa.** O componente da capa apresenta texto alternativo identificando o jogo e, em falha de carregamento, substitui a imagem por um fallback visível com o nome correspondente. O estado de falha não deve afetar as outras capas.
5. **Manter os exemplos não promocionais.** Usar nomes, App IDs e capas fixas como dados ilustrativos; não associar preços, selos ou afirmações de popularidade. A barra de pesquisa e o fluxo de navegação para `/buscar` continuam inalterados.

## Riscos / Trade-offs

- **Uma imagem pode falhar depois de a página carregar** → manter o fallback vinculado ao erro individual da imagem e assegurar que o nome do jogo continue visível.
- **Seleções aleatórias podem coincidir em carregamentos consecutivos** → isso é permitido pelo requisito; os testes verificam novo sorteio e formato válido, não que resultados sucessivos sejam necessariamente diferentes.
- **O estado de sessão pode não corresponder mais a uma conta válida** → manter a validação existente no guard do catálogo; “Sair” sempre limpa o estado local autenticado antes de navegar.

## Plano de migração

Não há migração de dados nem mudança de dependências. Após implementar, validar os testes de autenticação e catálogo e conferir visualmente estados sem sessão/com sessão, logout em `/buscar`, seleção aleatória, destaque, grade e fallback de capa. Rollback consiste em reverter as alterações de estado, cabeçalho e apresentação; não há dados persistidos novos para reverter.
