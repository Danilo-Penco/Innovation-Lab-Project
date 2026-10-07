# Project Overview — ComparaKeys

## 1. Visão geral
Site que permite ao usuário pesquisar um jogo e comparar preços de lojas digitais. A primeira tela funcional consulta a Steam em tempo real e apresenta o preço regional atual para o Brasil.

## 2. Problema
Para encontrar o menor preço de uma key de jogo, o usuário hoje precisa visitar manualmente várias lojas diferentes, comparando preços um a um — algo demorado e pouco prático.

## 3. Objetivos
- Permitir a busca pública de jogos pelo nome e consultar o preço atual na Steam em BRL.
- Preparar a comparação com outras lojas para uma etapa futura.
- Indicar claramente qual loja oferece o menor preço.
- Permitir que novas lojas solicitem inclusão no sistema de comparação.

## 4. Público-alvo / usuários
- Jogadores que querem comprar jogos pelo menor preço possível.
- Lojas/distribuidoras de keys de jogos que desejam ser incluídas na comparação.

## 5. Escopo
Escopo desta primeira funcionalidade: busca de jogos e consulta do preço atual na Steam, em BRL, sem exigir login e sem persistir buscas ou preços. O login continua aplicável às demais funcionalidades que exigirem autenticação.
Fora do escopo desta funcionalidade: outras lojas, comparação de ofertas, persistência/histórico de preços e autenticação na tela de busca.
Fora do escopo inicial: compra direta dentro do site (o usuário é redirecionado à loja escolhida); sistema de avaliação/reputação de lojas.

## 6. Principais funcionalidades
- Cadastro/login de usuário para funcionalidades protegidas.
- Busca pública de jogo por nome e seleção entre resultados semelhantes.
- Exibição do preço regional atual da Steam em BRL, distinguindo jogos gratuitos e preços indisponíveis.
- Processo para uma loja solicitar inclusão no sistema.
- Aprovação/gerenciamento de lojas solicitantes.

## 7. Requisitos e restrições importantes
- A busca de preço na Steam usa a API pública da Steam (lista de apps + preço por App ID).
- Nem toda loja tem todo jogo; o sistema deve lidar com ausência de oferta em algumas lojas.
- Novas lojas podem exigir cadastro manual até que uma automação específica seja desenvolvida para elas.

## 8. Arquitetura tecnológica
- Backend: Xano (XanoScript) para autenticação, persistência e lógica de negócio das demais funcionalidades.
- Aplicação web: Reflex (Python); nesta busca pública, a chamada HTTP à Steam é executada no servidor Reflex.
- Integração externa: API pública da Steam para busca de App ID e preço.
- A busca de preço na Steam não grava no Xano e não mantém cache ou histórico persistente.

## 9. Princípios de desenvolvimento
- Priorizar a busca/comparação de preços como núcleo do sistema antes de recursos secundários.
- Desenvolvimento incremental, guiado pelo OpenSpec.

## 10. Segurança e integridade
- Funcionalidades protegidas exigem login; a busca de preço da Steam é pública.
- Regras de autorização (ex.: quem pode aprovar lojas) devem ser aplicadas no backend (Xano), nunca só no frontend.

## 11. Estratégia de desenvolvimento
- Desenvolvimento incremental via OpenSpec, começando pela funcionalidade central (busca e comparação de preços).

## 12. Fonte de verdade e documentação
- Este documento e o `domain-model.md` são a referência de contexto do projeto. Mudanças de escopo devem ser refletidas aqui.
