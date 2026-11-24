# Project Overview — ComparaKeys

## 1. Visão geral
Site que permite ao usuário pesquisar um jogo e comparar preços de lojas digitais. A página inicial `/` é pública e apresenta o projeto; sua barra superior sticky oferece “Entrar” e “Cadastrar” para visitantes e “Ir para o catálogo” e “Sair” para pessoas autenticadas. Login e cadastro ficam em `/entrar` e `/cadastro`. A busca e comparação Steam/GOG e as ofertas adicionais CheapShark continuam disponíveis em rotas próprias sem autenticação.

## 2. Problema
Para encontrar o menor preço de uma key de jogo, o usuário hoje precisa visitar manualmente várias lojas diferentes, comparando preços um a um — algo demorado e pouco prático.

## 3. Objetivos
- Permitir a busca pública de jogos pelo nome e comparar os preços atuais da Steam e da GOG em BRL quando houver correspondência inequívoca, além de até cinco ofertas adicionais da CheapShark, identificadas por nome e logotipo.
- Converter somente ofertas USD da CheapShark para BRL aproximado usando Frankfurter; nunca converter os preços reais em BRL da Steam ou GOG.
- Indicar claramente qual loja oferece o menor preço.
- Permitir que novas lojas solicitem inclusão no sistema de comparação.

## 4. Público-alvo / usuários
- Jogadores que querem comprar jogos pelo menor preço possível.
- Lojas/distribuidoras de keys de jogos que desejam ser incluídas na comparação.

## 5. Escopo
A aplicação oferece cadastro e login por Nome, e-mail e senha para encaminhar usuários autenticados às áreas protegidas. As contas são persistidas na tabela `user` do Xano pelos endpoints existentes `auth/signup` e `auth/login`; o Reflex mantém o `authToken` apenas no estado server-side da sessão, que foi verificado após recarga completa do navegador, e valida o acesso ao catálogo com `auth/me` a cada carregamento protegido. O token Xano não é armazenado em `localStorage`, `sessionStorage` ou URL. Não há contas locais SQLite nem migração de contas. Os formulários em `/entrar` e `/cadastro` são centralizados e usam espaçamento compacto para caber em telas comuns sem rolagem; em viewports baixos, a página continua rolável sem cortar controles. O cabeçalho apresenta “Entrar” sem sessão e “Sair” com sessão autenticada; a saída limpa a sessão Reflex e retorna a `/entrar`, inclusive a partir da busca pública. A marca ComparaKeys leva a `/catalogo` com sessão autenticada e a `/` sem sessão, inclusive na landing page e nas telas de autenticação. O catálogo continua protegido e redireciona pessoas sem sessão válida para `/entrar`.
A cada carregamento, o catálogo protegido sorteia oito jogos de uma lista fixa de pelo menos 12 exemplos com capas; um deles aparece em destaque e os demais em uma grade. Esses exemplos são ilustrativos e não representam popularidade, preços ou promoções atuais. As capas têm texto alternativo e exibem um fallback com o nome do jogo quando a imagem falha. Todos os cards, inclusive o destaque, abrem a comparação pelo App ID Steam do jogo. Após a grade, o catálogo mostra um breve texto institucional e um link para `/buscar`.
As buscas e comparações Steam/GOG/CheapShark ficam disponíveis publicamente, sem exigir login e sem persistir buscas ou preços. A pessoa pode iniciar a busca pelo campo “Comparar Preços” no catálogo; o termo abre `/buscar` preenchido e os resultados são carregados automaticamente. A landing page termina após os cards institucionais e não contém campo de busca. Na rota `/buscar`, os resultados da Steam são atualizados conforme a pessoa digita. Ao selecionar um jogo, a aplicação abre `/comparar?app_id=<id>`, uma rota dedicada que carrega os preços atuais, inclusive quando acessada diretamente. A GOG prioriza o título normalizado idêntico e, se não houver, aceita somente uma correspondência única por prefixo/contenção após ignorar qualificadores comuns de edição. A comparação também consulta ofertas CheapShark de outras lojas para o mesmo Steam App ID. Cada cartão mostra nome e logotipo acessível; logos CheapShark vêm do campo `images.logo` do endpoint `/stores` e só são aceitos sob o caminho seguro `/img/stores/logos/`. A API CheapShark consultada com `country=BR` não identificou moeda e retornou as mesmas ofertas/preços observados com `country=US`; portanto valores USD usam Frankfurter para conversão aproximada, exibem o valor original, o valor convertido, a taxa exata e a data da cotação. Steam e GOG continuam em BRL real. A CheapShark informa `lastChange` em segundos Unix por oferta; Steam e GOG não retornam horário de atualização de preço nos endpoints públicos verificados, então a interface rotula explicitamente o horário de consulta do ComparaKeys em `America/Sao_Paulo`. Os horários originais são preservados em cache; cotação ausente ou inválida mantém a oferta em US$. Timeout, repetição única só para rede/timeout, HTTP 429/`Retry-After` e nova tentativa explícita são tratados por integração, sem remover preços válidos das demais fontes. Ausência, ambiguidade e preço não disponível em BRL na GOG têm mensagens próprias. A página inicial `/` é uma landing page pública, o login está em `/entrar`, e `/cadastro` apresenta a criação de conta.
Fora do escopo desta etapa: Epic Games Store, compra dentro do site, persistência/histórico de preços, recuperação de senha, login externo e papéis/permissões administrativas.
Fora do escopo inicial: compra direta dentro do site (o usuário é redirecionado à loja escolhida); sistema de avaliação/reputação de lojas.

## 6. Principais funcionalidades
- Cadastro/login de usuário por e-mail e senha para funcionalidades protegidas.
- Catálogo de jogos de exemplo protegido por autenticação, com capas e acesso à busca Steam.
- Busca pública ao vivo de jogo por nome na Steam e seleção entre resultados semelhantes.
- Comparação em rota dedicada do preço regional atual da Steam com uma correspondência única da busca pública GOG, em BRL, distinguindo jogos gratuitos e preços indisponíveis.
- Até cinco ofertas CheapShark de lojas distintas de Steam e GOG, ordenadas por preço; valores USD podem ser exibidos em BRL aproximado com Frankfurter ou em US$ quando a cotação falha.
- Processo para uma loja solicitar inclusão no sistema.
- Aprovação/gerenciamento de lojas solicitantes.

## 7. Requisitos e restrições importantes
- A busca Steam usa a API pública da Steam (lista de apps + preço por App ID); a busca GOG usa o catálogo público JSON da GOG; ofertas adicionais vêm da API pública CheapShark e a cotação USD/BRL de Frankfurter v2, ambas sem chave.
- Uma comparação GOG requer título equivalente sem ambiguidade e preço regional em BRL; ausência, ambiguidade, falha ou falta de preço em BRL não impedem a exibição da Steam.
- A resposta CheapShark sem moeda explícita é tratada como USD conforme a API observada. Preços originais e valores comparáveis em BRL são mantidos separadamente em memória; taxas e datas Frankfurter e horários de oferta não são persistidos. As integrações de preço usam timeout de 10 s, uma repetição somente em erro de rede/timeout, respeitam HTTP 429/`Retry-After` e oferecem nova tentativa explícita. Ofertas usam cache volátil de até cinco minutos e taxa USD/BRL até uma hora.
- Nem toda loja tem todo jogo; o sistema deve lidar com ausência de oferta em algumas lojas.
- Novas lojas podem exigir cadastro manual até que uma automação específica seja desenvolvida para elas.

## 8. Arquitetura tecnológica
- Backend: Xano (XanoScript) para lógica de negócio das funcionalidades integradas ao Xano.
- Aplicação web: Reflex (Python); interface, estado de sessão, validação do token do catálogo por `auth/me` e busca pública Steam são executados no servidor Reflex. A autenticação e a persistência de usuários são fornecidas pelo Xano.
- Integração externa: APIs públicas da Steam e do catálogo GOG para busca e preços regionais reais em BRL, CheapShark para ofertas adicionais e Frankfurter v2 para câmbio de referência USD/BRL.
- Resultados de busca Steam, metadados de identificação GOG e ofertas CheapShark podem permanecer somente em cache limitado na memória do processo por até 5 minutos; a cotação USD/BRL, incluindo sua data, pode permanecer em memória por até uma hora. Preços Steam/GOG não são cacheados nem convertidos; nenhum preço ou cotação é gravado no banco Reflex, no Xano ou em arquivos. A interface preserva o instante de consulta dos resultados cacheados e o apresenta no fuso `America/Sao_Paulo`.

## 9. Princípios de desenvolvimento
- Priorizar a busca/comparação de preços como núcleo do sistema antes de recursos secundários.
- Desenvolvimento incremental, guiado pelo OpenSpec.

## 10. Segurança e integridade
- Funcionalidades protegidas exigem que o backend Reflex valide o `authToken` da sessão usando `auth/me`; falha de conexão não libera o catálogo. A busca e comparação de preços Steam/GOG/CheapShark são públicas.
- Regras de autorização devem ser aplicadas no backend responsável pela funcionalidade (Reflex ou Xano), nunca só no frontend.

## 11. Estratégia de desenvolvimento
- Desenvolvimento incremental via OpenSpec, começando pela funcionalidade central (busca e comparação de preços).

## 12. Fonte de verdade e documentação
- Este documento e o `domain-model.md` são a referência de contexto do projeto. Mudanças de escopo devem ser refletidas aqui.
