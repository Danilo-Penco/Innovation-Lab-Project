# Proposal

## Why

A página `/catalogo` ainda é apenas um placeholder após o login, sem conteúdo que ajude a pessoa a iniciar uma busca. Um catálogo visual com jogos de exemplo e uma entrada direta para a busca Steam torna a área autenticada útil sem antecipar integrações de ofertas que ainda não existem.

## What Changes

- Substituir o placeholder de `/catalogo` por uma página autenticada com uma seleção pequena de jogos de exemplo, cada um apresentado com capa e identificação.
- Incluir no topo uma barra de pesquisa com o texto de exemplo “Comparar Preços”.
- Ao submeter um termo no catálogo, navegar para `/buscar` levando o termo; a busca Steam existente recebe o termo preenchido. A pesquisa e a consulta de preço continuam seguindo o fluxo já existente nessa página.
- Manter a proteção de `/catalogo` no backend e não exigir autenticação para a busca pública Steam em `/buscar`.
- Usar dados fixos de exemplo nesta etapa; ofertas, popularidade e promoções reais, bem como rotação dinâmica do catálogo, ficam fora do escopo.

## Capabilities

### New Capabilities
- `game-catalog`: exibição autenticada de jogos de exemplo com capa e pesquisa que encaminha o termo à busca Steam.

### Modified Capabilities
- `user-authentication`: substituir o requisito de catálogo-placeholder por uma área autenticada com o conteúdo definido pela capacidade `game-catalog`, preservando os cenários de autorização.
- `steam-price-search`: aceitar um termo encaminhado do catálogo e apresentá-lo preenchido na busca existente em `/buscar`.

## Impact

- `Projeto/Projeto.py`: página protegida do catálogo, estado/formulário de busca e integração de navegação com o estado da busca Steam existente.
- `Projeto/steam.py` e/ou estado da busca em Reflex: adaptação para aceitar um termo de entrada na rota `/buscar`, sem alterar a busca atual quando a rota é aberta sem termo.
- Recursos visuais do frontend: capas para os itens fixos de exemplo, respeitando a identidade visual existente.
- `docs/project-overview.md` e `docs/domain-model.md`: atualizar a descrição que atualmente caracteriza o catálogo como placeholder.
- OpenSpec: nova especificação delta `game-catalog` e atualização dos contratos de `user-authentication` e `steam-price-search`.
- Nenhum serviço de preço novo, integração de promoção, persistência de buscas ou mudança de dependências é pressuposto por esta proposta.
