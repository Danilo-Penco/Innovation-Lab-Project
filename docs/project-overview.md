# Project Overview — ComparaKeys

## 1. Visão geral
Site que permite ao usuário pesquisar um jogo e visualizar, em um só lugar, os preços desse jogo em várias lojas de keys de jogos online e distribuidoras oficiais, facilitando a escolha da oferta mais barata.

## 2. Problema
Para encontrar o menor preço de uma key de jogo, o usuário hoje precisa visitar manualmente várias lojas diferentes, comparando preços um a um — algo demorado e pouco prático.

## 3. Objetivos
- Permitir que o usuário busque um jogo pelo nome e veja o preço em várias lojas simultaneamente.
- Indicar claramente qual loja oferece o menor preço.
- Permitir que novas lojas solicitem inclusão no sistema de comparação.

## 4. Público-alvo / usuários
- Jogadores que querem comprar jogos pelo menor preço possível.
- Lojas/distribuidoras de keys de jogos que desejam ser incluídas na comparação.

## 5. Escopo
Escopo inicial: comparação de preços de jogos disponíveis na Steam (via API pública da Steam) e em lojas de keys parceiras cadastradas no sistema. Login de usuário é obrigatório para usar o site.
Fora do escopo inicial: compra direta dentro do site (o usuário é redirecionado à loja escolhida); sistema de avaliação/reputação de lojas.

## 6. Principais funcionalidades
- Cadastro/login de usuário.
- Busca de jogo por nome.
- Exibição do preço do jogo em todas as lojas cadastradas, destacando a mais barata.
- Processo para uma loja solicitar inclusão no sistema.
- Aprovação/gerenciamento de lojas solicitantes.

## 7. Requisitos e restrições importantes
- A busca de preço na Steam usa a API pública da Steam (lista de apps + preço por App ID).
- Nem toda loja tem todo jogo; o sistema deve lidar com ausência de oferta em algumas lojas.
- Novas lojas podem exigir cadastro manual até que uma automação específica seja desenvolvida para elas.

## 8. Arquitetura tecnológica
- Backend: Xano (XanoScript), incluindo banco de dados e lógica de negócio.
- Frontend: HTML/CSS/JavaScript (sem framework, por simplicidade inicial).
- Integração externa: API pública da Steam para busca de App ID e preço.
- A lógica de busca de preço na Steam (hoje prototipada em Python) será reimplementada em XanoScript ou chamada como serviço.

## 9. Princípios de desenvolvimento
- Priorizar a busca/comparação de preços como núcleo do sistema antes de recursos secundários.
- Desenvolvimento incremental, guiado pelo OpenSpec.

## 10. Segurança e integridade
- Login de usuário obrigatório para usar o site.
- Regras de autorização (ex.: quem pode aprovar lojas) devem ser aplicadas no backend (Xano), nunca só no frontend.

## 11. Estratégia de desenvolvimento
- Desenvolvimento incremental via OpenSpec, começando pela funcionalidade central (busca e comparação de preços).

## 12. Fonte de verdade e documentação
- Este documento e o `domain-model.md` são a referência de contexto do projeto. Mudanças de escopo devem ser refletidas aqui.
