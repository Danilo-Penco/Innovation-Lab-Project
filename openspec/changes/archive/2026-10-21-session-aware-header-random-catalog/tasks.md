# Tasks

## 1. Cabeçalho e encerramento de sessão

- [x] 1.1 Atualizar o cabeçalho compartilhado para mostrar “Entrar” sem sessão e “Sair” com sessão ativa; implementar a saída limpando a identidade e o estado de autorização antes de retornar a `/`. Verificar estados autenticados/não autenticados e logout por testes, incluindo `/buscar`.
- [x] 1.2 Atualizar a documentação de autenticação em `docs/project-overview.md` e `docs/domain-model.md` para descrever as ações do cabeçalho e logout; verificar se ambas refletem o comportamento especificado sem alterar a regra de acesso público à busca.

## 2. Catálogo aleatório e acessível

- [x] 2.1 Ampliar `CATALOG_GAMES` para pelo menos 12 jogos fixos com nome e URL de capa válida; verificar quantidade, nomes, App IDs e URLs nos testes de catálogo.
- [x] 2.2 Sortear oito jogos distintos e um destaque entre eles em cada carregamento de `/catalogo`, apresentando o destaque maior no topo e os demais em grade; verificar seleção, ausência de duplicatas e pertencimento do destaque com testes determinísticos do sorteio.
- [x] 2.3 Implementar fallback visível com o nome do jogo para falhas de capa, preservando texto alternativo e apresentação ilustrativa sem alegações atuais de preço, popularidade ou promoção; verificar fallback, acessibilidade e layout visual.
- [x] 2.4 Atualizar `docs/project-overview.md` e `docs/domain-model.md` para registrar a lista ampliada e sua apresentação aleatória ilustrativa; verificar consistência com as regras do catálogo.

## 3. Verificação integrada

- [x] 3.1 Executar os testes direcionados de autenticação e catálogo e `reflex compile --dry`; verificar no navegador os estados de cabeçalho nas rotas protegida e pública, logout em `/buscar`, sorteio do catálogo, destaque e fallback de capa.
