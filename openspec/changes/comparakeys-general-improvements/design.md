# Design

## Context

Consulte [proposal.md](./proposal.md) para motivação e escopo e os delta specs para contratos observáveis. O projeto usa Reflex em Python, Xano para autenticação, busca pública Steam/GOG e ofertas CheapShark/Frankfurter em módulos separados. O catálogo é protegido; `/buscar` e `/comparar` são públicos. O estado de autenticação fica no servidor Reflex e as chamadas Xano existentes usam Bearer.

Os modelos atuais de Steam e GOG não carregam logotipo ou horário de atualização do preço. O parser CheapShark usa nome e preço da loja, mas não retém os metadados de imagens da resposta `/stores`; o cliente Frankfurter retorna somente o valor Decimal, embora a resposta testada contenha também data. A comparação já carrega as integrações em estados separados e isola falhas, e CheapShark tem timeout, retry transitório e cache volátil. Não há implementação de histórico ou favoritos no app: o change ativo `evolucao-comparakeys-quatro-fases` os planeja em F3/F4 e deixa pendente a validação de execução/browser da F2.

Há uma divergência no contexto de `openspec/config.yaml`: ele descreve login obrigatório, somente BRL e histórico no banco Reflex; o código, a documentação atual e a mudança ativa descrevem busca pública, conversão USD/BRL e autenticação Xano. Esta proposta segue o código/documentos atuais e a decisão de consolidar a mudança ativa. Uma tarefa sincronizará o contexto OpenSpec antes da implementação, sem migrar contas nem trocar a arquitetura.

## Goals / Non-Goals

**Goals:**

- Fazer a pessoa distinguir preço regional, valor original em USD, conversão aproximada, taxa usada e data/hora de origem.
- Manter as comparações isoladas por loja, com nome/logo acessível, ordenação e destaque coerentes.
- Incorporar histórico e favoritos autenticados no Xano sem persistir preços, expor tokens ou confiar em identidade enviada pelo cliente.
- Organizar carregamento, erro, ausência de resultados e nova tentativa sem permitir que uma integração indisponível esconda resultados de outra.
- Reutilizar Reflex, módulos HTTP, cache TTL, tokens visuais e rotas existentes.

**Non-Goals:**

- Migrar o login do Xano, introduzir uma nova stack ou persistir dados monetários.
- Publicar XanoScript, adicionar novos provedores de preços, compra no site ou fazer scraping.
- Transformar a taxa Frankfurter em cotação de transação ou classificar automaticamente uma loja como segura.
- Substituir a lista atual de jogos do catálogo por um novo catálogo comercial ou alterar a política de acesso público à busca.

## Decisions

### Consolidar sem reimplementar o que já existe

Usar a implementação F1/F2 atual como baseline. Antes de funcionalidades novas, reconciliar as verificações ainda pendentes da mudança ativa (especialmente execução do app e teste visual), sem marcar sucesso se o ambiente não permitiu verificar. A nova mudança é a fonte de implementação futura para F2 restante, F3 e F4; não aplicar as duas mudanças em paralelo nem alterar o diretório da mudança anterior durante esta proposta.

Na primeira inspeção, o servidor de desenvolvimento existente apresentou falhas de conexão Reflex. Após autorização para reiniciá-lo, a compilação e a inicialização em produção concluíram com sucesso em porta isolada. O smoke test navegou pela landing e por `/comparar?app_id=369000`, que carregou os preços, logos, cotação, datas e links reais das lojas. A validação em viewport de 320 px confirmou barra superior em uma linha, cards empilhados e ausência de rolagem horizontal. A suíte completa e o build de produção também passaram. As tarefas 2.5 e 2.8 da mudança anterior permanecem sem alteração; não há necessidade de duplicar a integração CheapShark.

Alternativa considerada: continuar a mudança antiga e criar uma segunda proposta só para novos itens. Foi rejeitada porque repetiria requisitos de ofertas, histórico e favoritos e poderia fazer duas listas de tarefas divergirem.

### Normalizar dados de cada oferta mantendo a origem

Cada oferta em memória deve conservar loja, URL de logo validada, moeda e preço originais, valor comparável em BRL quando houver, origem temporal e estado de menor preço. Steam/GOG permanecem em BRL regional; CheapShark só é convertida se não indicar BRL e uma taxa válida estiver disponível. Somente preços BRL válidos participam da ordenação/comparação numérica. O formato renderizado não altera os valores usados no destaque verde.

Usar os caminhos de logo devolvidos pelo catálogo CheapShark quando válidos e estáveis. Steam e GOG devem usar ativos locais aprovados quando disponíveis; sem imagem válida, manter nome textual e texto alternativo. Não renderizar URLs arbitrárias recebidas do cliente.

Alternativa considerada: usar somente texto ou bandeiras de moeda. Foi rejeitada porque não identifica suficientemente a marca da loja e não atende ao pedido de logotipo; fallback textual continua necessário para acessibilidade e falha de imagem.

### Preservar a cotação completa e rotular o horário corretamente

Representar a taxa Frankfurter em memória como valor mais data da resposta, mantendo TTL de uma hora; exibir os dois junto à conversão. Quando a loja informar explicitamente a atualização do preço, mostrar esse instante com rótulo de origem. Caso contrário, capturar o instante de recebimento da resposta e mostrar “Consultado pelo ComparaKeys”. Renderizar datas em `America/Sao_Paulo`, sem chamar a hora de consulta de “atualização da loja”.

Uma leitura do cache CheapShark mantém o instante original de obtenção; não renovar o timestamp durante uma leitura. Respeitar o TTL atual de cinco minutos. Após a expiração, consultar a fonte novamente; se a consulta falhar sem cache válido, mostrar erro/indisponibilidade, não um preço antigo como atual. A data da cotação cambial nunca substitui a data/hora da oferta.

Alternativa considerada: usar a hora da renderização para cada preço. Foi rejeitada porque faria dados cacheados parecerem mais novos do que são. Também não se presume que a data Frankfurter seja a data de alteração do preço da loja.

### Resiliência por integração, sem retentativas ocultas

Continuar carregando Steam, GOG, CheapShark e câmbio como fontes independentes, com estado próprio de carregamento/erro. Harmonizar limites, mensagens e controles de tentativa explícita sem capturas amplas. Em GETs repetíveis, admitir no máximo uma repetição somente para rede/timeout; não repetir erro HTTP e respeitar `Retry-After`. Toda tentativa explícita é iniciada pela pessoa e não por cada tecla/card. Reutilizar cache somente em memória, com a política definida por fonte.

Alternativa considerada: mostrar uma falha global quando uma integração falhar. Foi rejeitada porque apagaria ofertas válidas de outras lojas; usar estado específico preserva resultados parciais.

### Manter histórico e favoritos no contrato Xano autenticado

Usar o grupo Authentication e o `XANO_API_URL` existentes. `POST/GET/DELETE /history` e `GET/POST/DELETE /favorites` seguem os contratos já registrados na mudança ativa; todos usam `Authorization: Bearer <token>` e o proprietário vem de `$auth.id`. A busca continua pública: somente a abertura autenticada de uma comparação registra histórico, sem preço. Listas são carregadas uma vez por visita, sem chamadas por card ou tecla.

Como o plano Xano não permite publicar XanoScript, documentar campos, endpoints, exemplos e prompts do Xano Agent; configurar manualmente uma instância de teste e executar `scripts/check_xano.py` com contas descartáveis, 401 sem token, isolamento e idempotência antes de integrar o Reflex. Não automatizar nem contornar publicação de XanoScript.

Alternativa considerada: persistir histórico no banco Reflex. Foi rejeitada para manter os contratos existentes e a autorização por token de usuário no Xano; a divergência do contexto OpenSpec será corrigida como documentação, não como migração de dados.

### Preservar componentes, rotas e sessão

Estender componentes e tokens de tema existentes, mantendo `/`, `/entrar`, `/cadastro`, `/catalogo`, `/buscar`, `/comparar`, `/historico` e `/favoritos`. O backend Reflex valida sessão nas rotas protegidas; HTTP 401 limpa a sessão e encaminha a `/entrar`. Validação de formulários deve corresponder aos contratos Xano, ter mensagens associadas aos campos e nunca revelar credenciais ou tokens.

## Risks / Trade-offs

- [APIs podem não fornecer data de atualização do preço] → exibir o horário de consulta do ComparaKeys com rótulo explícito; nunca afirmar que ele é a atualização da loja.
- [A taxa de referência pode diferir do valor de compra] → exibir taxa/data exatas, manter aviso de aproximação e conservar o preço original em USD.
- [URLs de logo podem mudar ou falhar] → validar origem/protocolo, usar texto alternativo e fallback pelo nome.
- [Uma falha de loja pode deixar comparação parcial] → manter estados independentes e avisos recuperáveis; não esconder preços válidos das outras fontes.
- [Xano Free exige configuração manual] → bloquear integração Reflex até contrato, prompt e checker confirmarem 401, Bearer, isolamento e idempotência em ambiente de teste.
- [A mudança ativa já contém implementação parcialmente aplicada] → fazer inventário por tarefa e por comportamento antes de editar; manter a mudança antiga intacta até a substituição ser validada.

## Migration Plan

1. Sincronizar o contexto OpenSpec com a arquitetura e o comportamento vigentes; revisar o status real de F2 e manter os dados e contas existentes intactos.
2. Estender contratos e modelos de oferta, cotação e timestamp; validar logos, moeda, menor preço, cache e falhas com respostas simuladas.
3. Atualizar documentação Xano e prompts; criar e verificar endpoints de histórico em workspace de teste antes da integração Reflex.
4. Integrar `/historico`, recentes no catálogo e limpeza autenticada; verificar isolamento por duas contas e ausência de preços persistidos.
5. Criar e verificar endpoints de favoritos em workspace de teste; integrar carregamento em lote, controles acessíveis e `/favoritos`.
6. Padronizar catálogo/busca/autenticação, executar testes, compilação e smoke tests responsivos; reconciliar/arquivar a mudança anterior somente após os gates passarem.

Rollback de mudanças de interface pode desabilitar os novos blocos e chamadas Reflex sem remover tabelas ou registros Xano. Nenhum passo de rollback deve apagar históricos ou favoritos de usuários.
