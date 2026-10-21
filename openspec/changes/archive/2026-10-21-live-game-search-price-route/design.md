# Design

## Contexto

Hoje `SearchState` reúne o termo, os resultados e os dados de comparação. A rota `/buscar` chama a busca somente por meio de um botão; a seleção usa os resultados em memória, consulta Steam e GOG e renderiza a comparação na mesma página. O serviço Steam já valida termos, consulta a API e identifica jogos por App ID; o serviço GOG já trata correspondência inequívoca e preço em BRL.

## Objetivos / Não objetivos

**Objetivos:**

- Atualizar resultados automaticamente sem submeter um formulário.
- Manter resultados e estados de erro coerentes com o termo mais recente, mesmo com respostas fora de ordem.
- Fazer a tela de busca e a tela de comparação terem rotas e responsabilidades visuais distintas.
- Permitir que a rota de comparação carregue um jogo válido sem depender dos resultados em memória da busca.

**Não objetivos:**

- Alterar as integrações, a seleção de lojas, a regra de correspondência Steam/GOG ou a apresentação dos preços.
- Persistir buscas, resultados ou preços, adicionar cache ou exigir autenticação para a busca pública.
- Mudar o fluxo de pesquisa do catálogo além de iniciar automaticamente a busca com o termo que ele encaminha.

## Decisões

1. **Disparar busca ao alterar o campo, com uma pausa curta de aproximadamente 300 ms.** A pausa reduz chamadas repetidas durante a digitação, mantendo a interação automática e sem botão. Um campo vazio invalida consultas pendentes e limpa resultados, erros e estados de ausência de correspondência. Uma consulta só pode atualizar a tela se ainda corresponder ao termo/request mais recente; a lógica de proteção contra respostas tardias já existe para buscas iniciadas pelo evento `search` e deve ser aplicada também às mudanças de termo.

2. **Usar `/comparar?app_id=<id>` como rota dedicada e identificador canônico.** A seleção de resultado valida o App ID contra os resultados da busca e navega para a rota, sem carregar os cartões de comparação em `/buscar`. A rota de comparação lê o App ID da URL e resolve os dados atuais por meio dos serviços existentes, permitindo atualização e acesso direto sem carregar o estado transitório da tela de busca.

3. **Resolver primeiro os dados Steam ao carregar uma comparação direta.** O App ID permite consultar o detalhe Steam, que fornece o nome validado necessário para consultar a GOG. Depois disso, a busca GOG usa o nome Steam, mantendo as regras atuais de correspondência e fallback. Esta ordem evita depender de um nome vindo do navegador ou de estado anterior. Como alternativa, passar o nome na URL ou depender do estado em memória evitaria essa etapa de resolução, mas seria menos confiável em links diretos e atualizações de página.

4. **Reutilizar os serviços e componentes existentes de preço.** O cartão de comparação e o tratamento de preços gratuitos, indisponíveis, erros e menor preço permanecem compartilhados; a nova rota apenas os apresenta no contexto dedicado. Não será introduzido backend Xano, dependência ou armazenamento para esse fluxo.

## Riscos / Trade-offs

- [A pausa de digitação pode parecer lenta ou, se muito curta, gerar chamadas demais] → Usar uma pausa curta e validar o comportamento com testes do disparo automático e da redução de chamadas consecutivas.
- [Respostas de uma busca anterior podem terminar depois de uma edição do termo] → Invalidar a geração da busca imediatamente ao editar/limpar o campo e só aplicar respostas que correspondam à geração e ao termo atuais.
- [A rota de comparação pode ser aberta com App ID ausente ou inválido] → Validar o parâmetro antes da consulta, exibir estado de erro recuperável e oferecer retorno à busca, sem reaproveitar preço ou jogo anterior.
- [A resolução Steam seguida da consulta GOG pode aumentar o tempo até a comparação completa] → Exibir carregamento desde o início, renderizar o resultado Steam assim que disponível e manter a GOG como comparação complementar sujeita ao fallback existente.

## Plano de migração

Não há migração de dados nem mudança de formato persistido. Implementar e testar a busca ao vivo, depois a navegação e o carregamento da rota `/comparar`; manter `/buscar?term=...` como ponto de entrada compatível para os links vindos do catálogo. Em caso de regressão, reverter a alteração de interface e roteamento sem alteração de banco de dados.
