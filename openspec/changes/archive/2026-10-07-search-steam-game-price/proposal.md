# Proposal

## Why

O protótipo atual do ComparaKeys não permite pesquisar jogos nem consultar preços. Esta mudança entrega a primeira experiência funcional do produto: encontrar um jogo na Steam e mostrar seu preço vigente em reais, sem armazenar ofertas.

## What Changes

- Adicionar uma tela de busca de jogos na aplicação Reflex, com resultados que permitam escolher o jogo correto quando houver nomes semelhantes.
- Consultar a Steam em tempo real e exibir o preço atual em BRL, incluindo estados claros para carregamento, ausência de resultado e indisponibilidade de preço.
- Fazer as consultas à API pública da Steam no servidor Reflex, sem exigir uma nova operação no Xano.
- Manter a busca acessível sem autenticação e não persistir buscas nem preços.
- Limitar esta funcionalidade à Steam; comparação com outras lojas e autenticação para a busca ficam fora do escopo.

## Capabilities

### New Capabilities

- `steam-price-search`: pesquisar jogos por nome na Steam e apresentar o preço atual em BRL sem persistência.

### Modified Capabilities

Nenhuma. Ainda não existem specs base de capacidades no projeto.

## Impact

- Aplicação Reflex: substituir o conteúdo de protótipo da página inicial por uma experiência pública de busca e resultados; executar a integração HTTP com a Steam no servidor Reflex.
- Integração externa: depender da disponibilidade da busca pública da Steam e dos dados de preço regional para o Brasil.
- Banco de dados: nenhuma tabela ou persistência de preço será adicionada.
- O change em andamento de autenticação define acesso autenticado em termos gerais; a busca descrita aqui deverá permanecer uma exceção pública se esse change for aplicado.
