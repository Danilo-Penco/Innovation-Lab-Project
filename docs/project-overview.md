# Project Overview — ComparaKeys

## 1. Visão geral
Site que permite ao usuário pesquisar um jogo e comparar preços de lojas digitais. A página inicial oferece login/cadastro; a busca pública de preços Steam e GOG continua disponível em uma rota própria sem autenticação.

## 2. Problema
Para encontrar o menor preço de uma key de jogo, o usuário hoje precisa visitar manualmente várias lojas diferentes, comparando preços um a um — algo demorado e pouco prático.

## 3. Objetivos
- Permitir a busca pública de jogos pelo nome e comparar os preços atuais da Steam e da GOG em BRL quando houver correspondência inequívoca.
- Indicar claramente qual loja oferece o menor preço.
- Permitir que novas lojas solicitem inclusão no sistema de comparação.

## 4. Público-alvo / usuários
- Jogadores que querem comprar jogos pelo menor preço possível.
- Lojas/distribuidoras de keys de jogos que desejam ser incluídas na comparação.

## 5. Escopo
O site oferece cadastro e login por e-mail e senha para encaminhar usuários autenticados às áreas protegidas. A conta fica no banco SQLite próprio da aplicação Reflex; a senha é armazenada como hash com salt, nunca em texto puro. O catálogo protegido apresenta uma seleção fixa de jogos de exemplo com capas; esses exemplos não representam popularidade, preços ou promoções atuais.
A busca e comparação Steam/GOG ficam disponíveis publicamente em `/buscar`, sem exigir login e sem persistir buscas ou preços. A pessoa pode iniciar a busca pelo campo “Comparar Preços” no catálogo; o termo abre `/buscar` preenchido, e a pesquisa continua sendo executada pela ação dessa página. Após escolher um jogo Steam, o sistema compara a GOG somente quando encontra um único título equivalente; sem correspondência ou preço GOG em BRL, mantém a Steam e exibe um aviso. A página inicial `/` é o login, e `/cadastro` apresenta a criação de conta.
Fora do escopo desta etapa: Epic Games Store, compra dentro do site, conversão cambial, persistência/histórico de preços, recuperação de senha, login externo e papéis/permissões administrativas.
Fora do escopo inicial: compra direta dentro do site (o usuário é redirecionado à loja escolhida); sistema de avaliação/reputação de lojas.

## 6. Principais funcionalidades
- Cadastro/login de usuário por e-mail e senha para funcionalidades protegidas.
- Catálogo de jogos de exemplo protegido por autenticação, com capas e acesso à busca Steam.
- Busca pública de jogo por nome na Steam e seleção entre resultados semelhantes.
- Comparação do preço regional atual da Steam com uma correspondência única da busca pública GOG, em BRL, distinguindo jogos gratuitos e preços indisponíveis.
- Processo para uma loja solicitar inclusão no sistema.
- Aprovação/gerenciamento de lojas solicitantes.

## 7. Requisitos e restrições importantes
- A busca Steam usa a API pública da Steam (lista de apps + preço por App ID); a busca GOG usa o catálogo público JSON da GOG.
- Uma comparação GOG requer título equivalente sem ambiguidade e preço regional em BRL; ausência/falha GOG não impede a exibição da Steam.
- Nem toda loja tem todo jogo; o sistema deve lidar com ausência de oferta em algumas lojas.
- Novas lojas podem exigir cadastro manual até que uma automação específica seja desenvolvida para elas.

## 8. Arquitetura tecnológica
- Backend: Xano (XanoScript) para lógica de negócio das funcionalidades integradas ao Xano.
- Aplicação web: Reflex (Python); autenticação desta etapa, persistência de contas em SQLite e busca pública Steam são executadas no servidor Reflex.
- Integração externa: APIs públicas da Steam e do catálogo GOG para busca e preços regionais em BRL.
- As buscas e os preços Steam/GOG não são gravados no banco Reflex nem no Xano e não mantêm cache ou histórico persistente.

## 9. Princípios de desenvolvimento
- Priorizar a busca/comparação de preços como núcleo do sistema antes de recursos secundários.
- Desenvolvimento incremental, guiado pelo OpenSpec.

## 10. Segurança e integridade
- Funcionalidades protegidas exigem login validado no backend Reflex; a busca e comparação de preços Steam/GOG são públicas.
- Regras de autorização devem ser aplicadas no backend responsável pela funcionalidade (Reflex ou Xano), nunca só no frontend.

## 11. Estratégia de desenvolvimento
- Desenvolvimento incremental via OpenSpec, começando pela funcionalidade central (busca e comparação de preços).

## 12. Fonte de verdade e documentação
- Este documento e o `domain-model.md` são a referência de contexto do projeto. Mudanças de escopo devem ser refletidas aqui.
