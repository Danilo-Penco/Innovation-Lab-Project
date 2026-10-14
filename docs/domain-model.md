# Domain Model — ComparaKeys

Conceitos principais e relacionamentos:

Usuário (conta autenticada; papéis/permissões ainda não implementados)
Jogo
Loja
 - fornece Ofertas em tempo real (não persistidas) para os Jogos que vende
SolicitaçãoDeLoja
 - quando aprovada por um admin, origina uma Loja

## Usuário
Representa uma pessoa que usa as funcionalidades autenticadas do ComparaKeys. O cadastro e o login desta etapa usam o banco SQLite próprio da aplicação Reflex; a busca e comparação pública Steam/GOG podem ser usadas sem conta.
### Principais informações
- identificador da conta
- e-mail normalizado (único, sem distinção entre maiúsculas e minúsculas)
- salt e hash da senha (a senha em texto puro não é persistida)

### Autenticação e escopo atual
- A sessão Reflex mantém somente a identidade da conta no estado do servidor.
- Papéis de usuário/admin, recuperação de senha e login externo não fazem parte desta etapa.
- O catálogo é protegido e apresenta exemplos fixos de jogos com capas; esses exemplos não correspondem a ofertas verificadas nem são persistidos. A busca e comparação pública Steam/GOG permanecem disponíveis em `/buscar`, inclusive quando iniciadas a partir do catálogo. A GOG só é comparada quando existe uma correspondência única de título e preço regional em BRL; falha ou ausência GOG mantém o resultado Steam.

## Jogo
Representa um jogo pesquisável. Os cards ilustrativos do catálogo são uma lista fixa de exemplos e não constituem um catálogo persistido. Na busca pública, o jogo é resolvido a cada consulta na Steam (nome → App ID) e a oferta GOG é procurada pelo título Steam correspondente, sem persistência ou cache.
### Principais informações
- nome
- identificador na Steam (Steam App ID)
- capa ilustrativa (nos cards de exemplo do catálogo)

## Loja
Representa uma loja ou distribuidora de keys de jogos incluída no sistema.
### Principais informações
- nome da loja
- link/site da loja
- status (ativa, pendente de aprovação, inativa)
- forma de obtenção do preço (API pública no caso da Steam e catálogo público JSON no caso da GOG; outras integrações de lojas não fazem parte desta comparação)

## Oferta (não persistida)
Representa o preço de um jogo em uma loja, no momento da busca. É consultada em tempo real via servidor Reflex e APIs públicas da Steam e da GOG, e não fica salva no banco. A GOG só participa quando o título tem correspondência única e há preço regional em BRL; a Epic Games Store não faz parte deste fluxo.
### Principais informações (em memória, por busca)
- preço (em BRL)
- link direto para a página do jogo na loja de origem
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