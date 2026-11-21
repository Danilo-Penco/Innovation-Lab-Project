# Domain Model — ComparaKeys

Conceitos principais e relacionamentos:

Usuário (conta autenticada; papéis/permissões ainda não implementados)
Jogo
Loja
 - fornece Ofertas em tempo real (não persistidas) para os Jogos que vende
SolicitaçãoDeLoja
 - quando aprovada por um admin, origina uma Loja

## Usuário
Representa uma pessoa que usa as funcionalidades autenticadas do ComparaKeys. O cadastro e o login usam os endpoints existentes de autenticação do Xano e persistem a conta na tabela `user`; a busca ao vivo e comparação pública Steam/GOG podem ser usadas sem conta.
### Principais informações
- identificador da conta
- nome
- e-mail
- papel retornado pelo Xano (sem papéis administrativos definidos nesta etapa)

### Autenticação e escopo atual
- O cadastro envia Nome, e-mail e senha a `auth/signup`; o Nome é obrigatório no Reflex. O login envia e-mail e senha a `auth/login`.
- A sessão Reflex mantém o `authToken` apenas no estado server-side e sobrevive à recarga completa do navegador. O backend valida novamente o token por `auth/me` em cada carregamento de `/catalogo`; token inválido encerra a sessão e falha de conexão não libera o conteúdo protegido. O token Xano não é gravado em `localStorage`, `sessionStorage` ou URL.
- Senhas e contas não são persistidas no SQLite da aplicação Reflex. Não há migração de contas locais.
- O cabeçalho mostra “Entrar” sem identidade autenticada e “Sair” com a sessão ativa; a saída limpa a identidade e redireciona para a tela de login, inclusive na rota pública `/buscar`.
- Papéis de usuário/admin, recuperação de senha e login externo não fazem parte desta etapa.
- O catálogo é protegido e mantém uma lista fixa de pelo menos 12 exemplos com capas e App IDs Steam. A cada carregamento, apresenta oito jogos sorteados, com um destaque e os demais em grade; texto alternativo e fallback pelo nome mantêm a identificação acessível mesmo quando uma capa falha. Todos os cards abrem `/comparar?app_id=<id>` usando o identificador Steam do jogo; após a grade há um texto institucional e um link para `/buscar`. Esses exemplos não correspondem a ofertas verificadas nem são persistidos. A busca pública Steam atualiza os resultados conforme a digitação em `/buscar`; a seleção também abre a comparação em rota dedicada.
- A GOG prioriza um título normalizado idêntico entre produtos do tipo jogo. Sem resultado exato, pode usar uma única correspondência por prefixo/contenção após ignorar qualificadores comuns de edição; nenhuma ou múltiplas correspondências não são escolhidas. Metadados de identificação podem ficar em cache na memória por até 5 minutos, mas cada comparação consulta a resposta atual e nunca reutiliza preço cacheado. Ausência, ambiguidade e preço sem BRL são comunicados separadamente, e a oferta Steam permanece disponível.

## Jogo
Representa um jogo pesquisável. Os cards ilustrativos do catálogo são selecionados aleatoriamente a cada carregamento a partir de uma lista fixa com pelo menos 12 exemplos, e não constituem um catálogo persistido ou uma indicação de preço, popularidade ou promoção atual. Cada exemplo inclui App ID Steam e seu card abre a comparação dedicada por esse identificador. Na busca pública, o jogo é resolvido na Steam (nome → App ID); resultados de busca podem ser reutilizados por até 5 minutos em cache volátil do processo. Ao escolher um resultado, sua comparação é aberta em uma rota dedicada e identificada pelo App ID; a oferta GOG é procurada pelo título retornado pela Steam, com cache apenas de metadados de identificação por até 5 minutos e sem persistência.
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