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
A aplicação oferece cadastro e login por e-mail e senha para encaminhar usuários autenticados às áreas protegidas. A conta fica no banco SQLite próprio da aplicação Reflex; a senha é armazenada como hash com salt, nunca em texto puro. Os formulários em `/` e `/cadastro` são centralizados e usam espaçamento compacto para caber em telas comuns sem rolagem; em viewports baixos, a página continua rolável sem cortar controles. O cabeçalho apresenta “Entrar” sem sessão e “Sair” com sessão autenticada; a saída encerra a identidade da sessão e retorna à página de login, inclusive a partir da busca pública. A marca ComparaKeys no cabeçalho e no cadastro leva ao catálogo; no login, permanece sem link. O catálogo continua protegido e redireciona pessoas sem sessão para `/`.
A cada carregamento, o catálogo protegido sorteia oito jogos de uma lista fixa de pelo menos 12 exemplos com capas; um deles aparece em destaque e os demais em uma grade. Esses exemplos são ilustrativos e não representam popularidade, preços ou promoções atuais. As capas têm texto alternativo e exibem um fallback com o nome do jogo quando a imagem falha. Todos os cards, inclusive o destaque, abrem a comparação pelo App ID Steam do jogo. Após a grade, o catálogo mostra um breve texto institucional e um link para `/buscar`.
A busca Steam e a comparação Steam/GOG ficam disponíveis publicamente, sem exigir login e sem persistir buscas ou preços. A pessoa pode iniciar a busca pelo campo “Comparar Preços” no catálogo; o termo abre `/buscar` preenchido e os resultados são carregados automaticamente. Na busca, os resultados da Steam são atualizados conforme a pessoa digita. Ao selecionar um jogo, a aplicação abre `/comparar?app_id=<id>`, uma rota dedicada que carrega os preços atuais, inclusive quando acessada diretamente. A GOG prioriza o título normalizado idêntico e, se não houver, aceita somente uma correspondência única por prefixo/contenção após ignorar qualificadores comuns de edição. Ausência, ambiguidade e preço não disponível em BRL têm mensagens próprias; nesses casos, a oferta Steam continua visível. A página inicial `/` é o login, e `/cadastro` apresenta a criação de conta.
Fora do escopo desta etapa: Epic Games Store, compra dentro do site, conversão cambial, persistência/histórico de preços, recuperação de senha, login externo e papéis/permissões administrativas.
Fora do escopo inicial: compra direta dentro do site (o usuário é redirecionado à loja escolhida); sistema de avaliação/reputação de lojas.

## 6. Principais funcionalidades
- Cadastro/login de usuário por e-mail e senha para funcionalidades protegidas.
- Catálogo de jogos de exemplo protegido por autenticação, com capas e acesso à busca Steam.
- Busca pública ao vivo de jogo por nome na Steam e seleção entre resultados semelhantes.
- Comparação em rota dedicada do preço regional atual da Steam com uma correspondência única da busca pública GOG, em BRL, distinguindo jogos gratuitos e preços indisponíveis.
- Processo para uma loja solicitar inclusão no sistema.
- Aprovação/gerenciamento de lojas solicitantes.

## 7. Requisitos e restrições importantes
- A busca Steam usa a API pública da Steam (lista de apps + preço por App ID); a busca GOG usa o catálogo público JSON da GOG.
- Uma comparação GOG requer título equivalente sem ambiguidade e preço regional em BRL; ausência, ambiguidade, falha ou falta de preço em BRL não impedem a exibição da Steam.
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
