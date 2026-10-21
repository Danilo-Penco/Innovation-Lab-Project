# Proposal

## Why

Os formulários de login e cadastro ficam visualmente baixos e podem exigir rolagem em telas comuns. A comparação também perde jogos GOG quando a busca pública retorna produtos relevantes com títulos formatados de modo diferente ou resultados em tendência, enquanto o catálogo não oferece acesso direto à comparação nem um encerramento institucional.

## What Changes

- Centralizar os formulários de login e cadastro e reduzir o espaço superior, mantendo-os visíveis sem rolagem em tamanhos comuns de desktop e celular.
- Melhorar a busca e a correspondência GOG: priorizar título normalizado idêntico em produtos do tipo jogo; sem correspondência exata, aceitar somente uma correspondência única por prefixo ou conteúdo após ignorar edições e subtítulos comuns.
- Manter apenas a oferta Steam quando a correspondência GOG não existir ou for ambígua; diferenciar as mensagens de jogo não encontrado, múltiplas correspondências e preço BRL indisponível.
- Acrescentar testes de correspondência para “Hollow Knight: Silksong” e para os estados de resultado GOG.
- Adicionar ao fim do catálogo um rodapé institucional curto com link para `/buscar`.
- Tornar clicáveis os cards de destaque e da grade, navegando para `/comparar?app_id=<id>` com o App ID Steam do jogo.

## Capabilities

### New Capabilities

### Modified Capabilities
- `user-authentication`: ajustar o posicionamento responsivo dos formulários de login e cadastro.
- `steam-price-search`: ampliar a correspondência de títulos GOG e distinguir os motivos para exibir apenas a oferta Steam.
- `game-catalog`: adicionar rodapé com link para `/buscar` e navegação de todos os cards para a comparação pelo App ID Steam.

## Impact

- Interface Reflex em `Projeto/Projeto.py`, regras de correspondência em `Projeto/gog.py` e lista fixa em `Projeto/catalog.py`.
- Testes existentes de autenticação, catálogo, estado de busca e GOG em `tests/`.
- Contratos OpenSpec de autenticação, busca de preços e catálogo.
- Consulta somente às APIs públicas existentes da Steam e GOG; sem novas lojas, Xano, dependências ou persistência de preços.
