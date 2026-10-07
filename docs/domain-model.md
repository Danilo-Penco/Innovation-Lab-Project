# Domain Model — ComparaKeys

Conceitos principais e relacionamentos:

Usuário (papel: usuario ou admin)
Jogo
Loja
 - fornece Ofertas em tempo real (não persistidas) para os Jogos que vende
SolicitaçãoDeLoja
 - quando aprovada por um admin, origina uma Loja

## Usuário
Representa uma pessoa que usa as funcionalidades autenticadas do ComparaKeys. A busca inicial de preço na Steam pode ser usada sem conta.
### Principais informações
- nome
- e-mail
- senha (autenticação)
- papel (usuario | admin)

## Jogo
Representa um jogo pesquisável. Não é necessariamente uma tabela própria — na busca pública inicial, é resolvido a cada consulta na Steam (nome → App ID) e não é persistido nem armazenado em cache.
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
Representa o preço de um jogo em uma loja, no momento da busca. Na primeira funcionalidade, é consultada em tempo real exclusivamente na Steam, via servidor Reflex e API pública, e não fica salva no banco. Outras lojas não fazem parte deste fluxo.
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