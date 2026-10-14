# Domain Model — ComparaKeys

Conceitos principais e relacionamentos:

Usuário (conta autenticada; papéis/permissões ainda não implementados)
Jogo
Loja
 - fornece Ofertas em tempo real (não persistidas) para os Jogos que vende
SolicitaçãoDeLoja
 - quando aprovada por um admin, origina uma Loja

## Usuário
Representa uma pessoa que usa as funcionalidades autenticadas do ComparaKeys. O cadastro e o login desta etapa usam o banco SQLite próprio da aplicação Reflex; a busca pública Steam pode ser usada sem conta.
### Principais informações
- identificador da conta
- e-mail normalizado (único, sem distinção entre maiúsculas e minúsculas)
- salt e hash da senha (a senha em texto puro não é persistida)

### Autenticação e escopo atual
- A sessão Reflex mantém somente a identidade da conta no estado do servidor.
- Papéis de usuário/admin, recuperação de senha e login externo não fazem parte desta etapa.
- O catálogo é protegido e aparece inicialmente como placeholder; a busca pública Steam permanece disponível em `/buscar`.

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