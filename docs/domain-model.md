# Domain Model — ComparaKeys

Conceitos principais e relacionamentos:

Usuário (papel: usuario ou admin)
Jogo
Loja
 - fornece Ofertas em tempo real (não persistidas) para os Jogos que vende
SolicitaçãoDeLoja
 - quando aprovada por um admin, origina uma Loja

## Usuário
Representa uma pessoa que usa o site para buscar e comparar preços de jogos.
### Principais informações
- nome
- e-mail
- senha (autenticação)
- papel (usuario | admin)

## Jogo
Representa um jogo pesquisável. Não é necessariamente uma tabela própria — pode ser resolvido diretamente via busca na Steam (nome → App ID), com cache leve opcional para agilizar buscas repetidas.
### Principais informações
- nome
- identificador na Steam (Steam App ID)

## Loja
Representa uma loja ou distribuidora de keys de jogos incluída no sistema.
### Principais informações
- nome da loja
- link/site da loja
- status (ativa, pendente de aprovação, inativa)
- forma de obtenção do preço (API oficial, no caso da Steam; scraping configurado, no caso de lojas parceiras)

## Oferta (não persistida)
Representa o preço de um jogo em uma loja, no momento da busca. É calculada em tempo real, consultando a Steam (via API) e as lojas parceiras (via scraping configurado), não fica salva no banco.
### Principais informações (em memória, por busca)
- preço (em BRL)
- link direto para a compra
- loja de origem

## SolicitaçãoDeLoja
Representa o pedido de uma loja para ser incluída no sistema.
### Principais informações
- nome da loja solicitante
- dados de contato
- status da solicitação (pendente, aprovada, rejeitada)
- verificações automáticas básicas (ex.: URL acessível)
### Relacionamentos
Quando aprovada por um admin, origina uma Loja.