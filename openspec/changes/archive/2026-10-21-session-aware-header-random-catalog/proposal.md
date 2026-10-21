# Proposta

## Por quê

O cabeçalho não reflete a sessão autenticada: continua mostrando “Entrar” mesmo depois do login e não oferece uma ação visível para encerrar a sessão. Além disso, o catálogo tem apenas quatro exemplos estáticos exibidos sempre na mesma grade, limitando a descoberta visual de jogos.

## O que muda

- Tornar as ações do cabeçalho dependentes do estado da sessão: mostrar “Entrar” sem login e “Sair” com login ativo. A saída encerra a sessão e retorna à tela de login, inclusive quando a pessoa está na rota pública `/buscar`.
- Ampliar a lista fixa do catálogo para pelo menos 12 jogos com nome e capa.
- A cada carregamento do catálogo, sortear uma seleção de jogos (por exemplo, oito), apresentar um deles em destaque no topo e os demais em uma grade abaixo.
- Fornecer texto alternativo para as capas e fallback com o nome do jogo quando uma imagem não carregar.
- Manter os exemplos explicitamente ilustrativos, sem alegações de preços, popularidade ou promoções atuais.

## Capacidades

### Novas capacidades

Nenhuma.

### Capacidades modificadas

- `user-authentication`: definir a apresentação das ações de autenticação do cabeçalho conforme a sessão e o comportamento de encerramento da sessão.
- `game-catalog`: ampliar a lista fixa de exemplos e especificar seleção aleatória por carregamento, destaque visual, fallback de capa e preservação do caráter ilustrativo dos dados.

## Impacto

- Interface Reflex, estado de autenticação, cabeçalho compartilhado e rotas protegidas/públicas em `Projeto/Projeto.py`.
- Lista de dados do catálogo em `Projeto/catalog.py`.
- Testes de autenticação, do cabeçalho/estado de sessão e do catálogo.
- Sem mudanças nas APIs de lojas, em persistência de ofertas ou no backend Xano.

## Fora do escopo

- Consultar preços, promoções ou popularidade reais para preencher o catálogo.
- Migrar autenticação, catálogo ou outras funcionalidades para o Xano.
