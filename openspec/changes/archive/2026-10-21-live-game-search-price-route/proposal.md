# Proposta

## Por quê

Na página `/buscar`, a pessoa precisa clicar em “Buscar” para ver correspondências e, após escolher um jogo, a comparação aparece na própria tela. Isso torna a descoberta menos imediata e mistura a seleção do jogo com a consulta de preços; a busca ao digitar e uma tela de comparação dedicada tornam esse fluxo mais direto e claro.

## O que muda

- Consultar resultados da Steam automaticamente conforme o termo é digitado, sem exigir um botão “Buscar”.
- Manter estados claros de carregamento, erro e ausência de resultados, descartando respostas antigas quando o termo mudar rapidamente.
- Ao selecionar um resultado, navegar para uma rota dedicada de comparação, usando o identificador Steam do jogo.
- Apresentar os preços atuais da Steam e, quando houver correspondência utilizável, da GOG nessa rota dedicada.
- Preservar a busca pública, o preenchimento do termo encaminhado pelo catálogo, os preços em BRL e a não persistência de buscas e ofertas.

## Capacidades

### Novas capacidades

Nenhuma.

### Capacidades modificadas

- `steam-price-search`: substituir a busca submetida por botão por busca ao digitar e definir navegação para uma tela de comparação dedicada ao jogo selecionado.

## Impacto

- Interface, estado e roteamento Reflex em `Projeto/Projeto.py`, especialmente as rotas `/buscar` e de comparação por App ID.
- Testes da busca e da seleção/comparação, principalmente `tests/test_search_state.py` e eventuais testes de roteamento.
- Integrações existentes com Steam e GOG permanecem como fonte de dados atuais; não se prevê mudança de API, persistência, dependências ou backend Xano.
