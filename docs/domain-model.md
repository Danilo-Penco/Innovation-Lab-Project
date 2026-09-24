# Domain Model — ComparaKeys

Conceitos principais e relacionamentos:

Usuário
Jogo
 - possui várias Ofertas (uma por Loja)
Loja
 - possui várias Ofertas (uma por Jogo que vende)
Oferta (preço de um Jogo em uma Loja)
SolicitaçãoDeLoja
 - quando aprovada, origina uma Loja

## Usuário
Representa uma pessoa que usa o site para buscar e comparar preços de jogos.
### Principais informações
- nome
- e-mail
- senha (autenticação)

## Jogo
Representa um jogo cujo preço pode ser comparado entre lojas.
### Principais informações
- nome
- identificador na Steam (Steam App ID), quando aplicável
### Relacionamentos
Um jogo pode ter várias ofertas, uma em cada loja que o vende.

## Loja
Representa uma loja ou distribuidora oficial de keys de jogos incluída no sistema.
### Principais informações
- nome da loja
- link/site da loja
- status (ativa, pendente de aprovação, etc.)
### Relacionamentos
Uma loja pode ter várias ofertas, uma para cada jogo que vende.

## Oferta
Representa o preço de um jogo específico em uma loja específica.
### Principais informações
- preço
- link direto para a compra
- data da última atualização do preço
### Relacionamentos
Uma oferta pertence a um jogo e a uma loja.

## SolicitaçãoDeLoja
Representa o pedido de uma loja para ser incluída no sistema.
### Principais informações
- nome da loja solicitante
- dados de contato
- status da solicitação (pendente, aprovada, rejeitada)
### Relacionamentos
Quando aprovada, origina uma Loja.
