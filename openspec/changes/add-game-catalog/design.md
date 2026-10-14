# Design

## Context

Veja [proposal.md](./proposal.md) para a motivação e [specs/game-catalog/spec.md](./specs/game-catalog/spec.md), [specs/user-authentication/spec.md](./specs/user-authentication/spec.md) e [specs/steam-price-search/spec.md](./specs/steam-price-search/spec.md) para os contratos observáveis.

Atualmente, `/catalogo` já usa `AuthState.guard_catalog` no carregamento e renderiza o catálogo somente quando a sessão server-side foi validada. A página autorizada ainda é um placeholder. A rota pública `/buscar` usa `SearchState.search_term`; a página não tem inicializador de rota, e a busca só é executada quando a pessoa aciona “Buscar”. `Projeto/steam.py` fornece validação de termo e chamadas da API Steam, mas não inclui capas nos seus resultados. Não há imagens de jogos nos recursos locais existentes.

## Goals / Non-Goals

**Goals:**

- Transformar a página autorizada existente em um catálogo visual com um conjunto fixo e pequeno de jogos.
- Encaminhar uma pesquisa do catálogo para o fluxo Steam existente sem duplicar integração ou lógica de preço.
- Preservar o acesso público a `/buscar`, o fluxo manual de pesquisa e a validação backend atual de `/catalogo`.

**Non-Goals:**

- Implementar a comparação entre múltiplas lojas, dados reais de popularidade ou promoções.
- Consultar a Steam para buscar ou ordenar jogos ao abrir o catálogo.
- Persistir catálogo, pesquisas, cliques, preços ou histórico, ou alterar o modelo de conta.

## Decisions

1. **Reutilizar a página e o guard existentes.** Substituir o conteúdo de `catalog_page` e manter `AuthState.guard_catalog` como condição de autorização no backend. A alternativa de criar uma segunda rota de catálogo ou proteger somente a interface duplicaria navegação e poderia enfraquecer o controle de acesso já aplicado.

2. **Definir os jogos demonstrativos como dados estáticos.** Manter uma lista curta de itens com identificador, nome e URL de capa, sem requisições à API de busca ou preço na renderização do catálogo. Usar capas públicas da Steam para os jogos escolhidos, sem apresentá-las como indicação de promoção ou popularidade atual; se uma capa falhar, apresentar um estado visual substituto com texto acessível. Essa opção satisfaz a necessidade de capas sem adicionar dependências nem transformar exemplos em conteúdo dinâmico. O custo é depender da disponibilidade do host das imagens.

3. **Enviar a pesquisa pela URL e reinicializar o estado de busca.** O submit do catálogo deve validar o termo, codificá-lo como parâmetro de consulta e navegar para `/buscar?term=...`. No carregamento de `/buscar`, um handler deve ler `router.url.query_parameters`, inicializar `SearchState.search_term` com o valor recebido e usar string vazia quando não houver parâmetro. Isso evita reaproveitar acidentalmente um termo antigo quando a rota é aberta diretamente. A documentação de páginas Reflex descreve acesso a query parameters por `router.url.query_parameters`; confirmar compatibilidade com a versão Reflex 0.9.12 instalada durante a implementação. O campo continua permitindo editar o termo e executar a busca pela ação existente — não executar automaticamente preserva o comportamento atual de `/buscar`.

4. **Manter busca, validação e preço no fluxo atual.** Reutilizar `validate_search_term` e `SearchState.search`; o catálogo só encaminha a intenção de pesquisa. Não mover chamadas à Steam para o browser nem emitir consulta de preço até a pessoa selecionar um resultado, como já ocorre em `/buscar`. O parâmetro deve ser construído por mecanismo de URL seguro, nunca por interpolação de script executável.

5. **Estender a cobertura de verificação junto ao fluxo.** Preservar os testes de serviço em `tests/test_steam.py`; adicionar verificações para encaminhamento e inicialização do termo, inclusive rota direta sem parâmetro e entrada vazia. Validar visualmente autenticação de `/catalogo`, apresentação de imagens e comportamento responsivo.

## Risks / Trade-offs

- [O host externo das capas pode ficar indisponível ou bloquear requisições] → apresentar fallback acessível e não deixar o carregamento da imagem impedir o uso do catálogo.
- [Um parâmetro de consulta pode exceder o limite aceito pela busca] → limitar o comprimento da entrada do catálogo ao mesmo máximo já suportado pela busca e validar novamente no backend existente.
- [A URL da busca passa a conter o termo pesquisado] → encaminhar somente texto de busca não sensível, sem gravá-lo em armazenamento persistente; evitar incluí-lo em logs próprios.
- [Mudanças de roteamento podem afetar uma busca acessada diretamente ou pelo botão voltar] → sempre inicializar o campo de forma explícita no carregamento e testar os caminhos com e sem parâmetro.

## Migration Plan

1. Implementar a lista fixa de jogos, o leiaute responsivo e a pesquisa no catálogo, preservando o guard de autenticação.
2. Adaptar o carregamento de `/buscar` para ler o termo opcional e inicializar o campo sem alterar o disparo manual da busca ou o comportamento da rota sem parâmetro.
3. Verificar os cenários de estado vazio, termo encaminhado, busca Steam, acesso autenticado/não autenticado, falha de imagem e renderização responsiva; executar os testes pertinentes e `reflex compile --dry`.
4. Atualizar a visão geral e o modelo de domínio para remover a descrição do catálogo como placeholder. Rollback: restaurar o conteúdo placeholder, remover o formulário e a inicialização por parâmetro, mantendo o guard da rota e a busca pública existentes.
