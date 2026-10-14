# Proposal

## Why

Hoje a busca pública exibe apenas o preço regional da Steam, então a pessoa precisa consultar outras lojas separadamente para saber se há uma opção mais barata na GOG. Comparar as duas ofertas em uma única tela, com preços atuais em BRL e links diretos para as lojas, torna a busca mais útil sem exigir login.

## What Changes

- Depois que a pessoa escolher um jogo nos resultados da Steam, consultar a busca pública da GOG pelo título escolhido e obter uma correspondência somente quando houver um resultado único com título normalizado idêntico.
- Exibir os resultados da Steam e da GOG em blocos comparáveis, com capa, nome clicável que abre a página do jogo em nova aba e preço em BRL.
- Destacar em verde o menor preço quando ambos os preços puderem ser comparados; manter o estado de jogo gratuito e de preço indisponível sem inventar valores.
- Se não houver correspondência única na GOG, a loja não tiver oferta em BRL ou a consulta falhar, manter a oferta Steam e apresentar um aviso recuperável, sem bloquear o resultado da Steam.
- Preservar o acesso público sem login, o caráter transitório das ofertas e o estilo visual preto e roxo da página.
- Manter a Epic Games Store fora do escopo.

## Capabilities

### New Capabilities

Nenhuma.

### Modified Capabilities

- `steam-price-search`: expandir a busca pública existente para comparar a oferta selecionada da Steam com uma correspondência inequívoca da GOG, incluindo apresentação, destaque do menor preço e comportamento de fallback.

## Impact

- Aplicação Reflex: estado e interface de `/buscar`, que atualmente listam resultados Steam e consultam o preço após a seleção de um jogo.
- Serviço `Projeto/steam.py` e novos ou ajustados serviços/testes para consulta pública da GOG, validação de correspondência por título e preços regionais em BRL.
- Integrações externas com os endpoints públicos Steam e GOG; falhas da GOG não devem impedir a apresentação do resultado Steam.
- Nenhuma alteração de autenticação, banco de dados, persistência de preços ou integração com a Epic Games Store.
