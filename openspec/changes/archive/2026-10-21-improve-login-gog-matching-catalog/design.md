# Design

## Context

Ver a motivação em `proposal.md` e os contratos em `specs/`.

- Os formulários de login e cadastro são centralizados por `rx.center` com altura mínima de `100vh`; os cartões usam espaçamento fixo de `2rem`.
- `CatalogGame` já contém `app_id` para todos os jogos da lista fixa. Os cards atuais não são links; o catálogo termina após a grade.
- A comparação GOG usa `https://catalog.gog.com/v1/catalog`, consulta até 50 produtos do tipo jogo com região BRL e só aceita título igual após normalização de espaços e caixa. O estado atual reduz tanto ausência quanto ambiguidade a `None`, e a interface mostra avisos genéricos.

### Diagnóstico ao vivo da GOG

Em 21/10/2026, consultei o endpoint público da GOG com os mesmos parâmetros usados pelo cliente (`limit=50`, `order=desc:trending`, `productType=in:game`, `locale=en-US`, `currencyCode=BRL`, `countryCode=BR`) e `query=Hollow Knight: Silksong`. A resposta trouxe 50 produtos, todos do tipo `game`, mas nenhum título continha “Hollow” ou “Silksong”; os primeiros foram `Concubine` (R$ 24,75), `Leisure Suit Larry - Wet Dreams Dry Twice` (R$ 3,99), `Leisure Suit Larry - Wet Dreams Don't Dry` (R$ 3,49), `Heroes of Might and Magic® 3: Complete` (R$ 19,99) e `The Witcher 2: Assassins of Kings Enhanced Edition` (R$ 8,99), todos com preço em BRL. Portanto, para esse termo pontuado, a resposta observada se comportou como a lista em tendência, sem trazer o produto solicitado.

Repeti a busca com `query=Hollow Knight Silksong`, sem os dois-pontos: a resposta trouxe um produto, `Hollow Knight: Silksong`, `productType=game`, ID `1558393671`, com preço final em BRL de R$ 59,99. `query=Hollow Knight` trouxe dois jogos: `Hollow Knight` (R$ 46,99) e `Hollow Knight: Silksong` (R$ 59,99). Esses preços são uma fotografia da resposta consultada, não valores fixos nem garantidos. A causa observada combina a consulta pontuada, que retornou resultados em tendência sem o alvo, com o parser estrito, que só aceitava igualdade exata; a busca sem pontuação encontrou o título desejado.

## Goals / Non-Goals

**Goals:**

- Preservar o layout escuro e roxo e tornar os formulários compactos e centralizados em viewports comuns.
- Fazer o cliente GOG recuperar resultados relevantes para títulos pontuados e classificar correspondência exata, única aproximada, ausente ou ambígua antes de avaliar a disponibilidade do preço.
- Manter a Steam como resultado principal/fallback e preservar a distinção entre consulta indisponível e resposta válida sem preço BRL.
- Reutilizar os App IDs já presentes na lista do catálogo para acessar a comparação existente.

**Non-Goals:**

- Adicionar lojas, alterar a rota existente de comparação, persistir preço ou dados de busca, ou integrar a mudança ao Xano.
- Garantir que uma tela caiba em viewports excepcionalmente baixos; nesses casos, manter rolagem normal em vez de cortar conteúdo.

## Decisions

1. **Normalizar a consulta GOG somente como segunda tentativa.** Manter a busca original e, quando ela não produzir correspondência exata, repetir a consulta com pontuação convertida em separadores de palavras. A observação de `Hollow Knight: Silksong` versus `Hollow Knight Silksong` justifica a tentativa, enquanto o primeiro resultado mantém o caminho atual para títulos já atendidos. Avaliar somente `productType=game`. Alternativa considerada: usar sempre o termo sem pontuação; rejeitada por alterar desnecessariamente consultas que já funcionam.

2. **Resolver correspondências em duas etapas e não escolher por ordenação.** Primeiro procurar título normalizado idêntico; uma correspondência exata única prevalece mesmo se existirem resultados aproximados, e duplicatas exatas permanecem ambíguas. Somente sem resultado exato, remover qualificadores reconhecidos de edição/lançamento (por exemplo, “Deluxe Edition”, “Definitive Edition”, “Game of the Year”, “GOTY”, “Complete” e “Enhanced Edition”) e comparar por prefixo ou contenção. Preservar palavras distintivas do título — por exemplo, “Silksong” — em vez de remover todo texto após dois-pontos. Aceitar apenas um candidato aproximado; zero ou vários candidatos não expõem preço GOG. Alternativa considerada: escolher o primeiro resultado ordenado pela API; rejeitada porque a ordenação de tendência não prova equivalência.

3. **Representar separadamente o estado da correspondência e a oferta.** A busca deve distinguir ausência, ambiguidade, correspondência encontrada e falha técnica; uma oferta encontrada pode ainda estar sem preço BRL. Isso permite avisos específicos sem mudar o fallback: somente a oferta Steam permanece visível em ausência, ambiguidade ou falta de preço GOG. Erros de rede/API continuam no aviso recuperável de indisponibilidade.

4. **Manter links de card na rota de comparação existente.** Associar cada card, incluindo o destaque, a `/comparar?app_id=<id>` usando `CatalogGame.app_id`; não duplicar IDs em uma nova camada ou criar uma rota alternativa. Inserir o rodapé depois do bloco da grade. Alternativa considerada: encaminhar o clique para `/buscar`; rejeitada porque o pedido é comparar diretamente o jogo selecionado.

5. **Centralizar o conteúdo de autenticação por layout responsivo, sem altura fixa.** Usar a área disponível da viewport para centralizar os cartões com padding adaptável e reduzir o espaço vertical interno nos viewports estreitos. Preservar a altura mínima de tela e o fluxo normal de rolagem quando o conteúdo não couber, evitando cortar formulário, mensagens de erro ou controles. Validar visualmente login e cadastro em desktop e celular.

## Risks / Trade-offs

- [A GOG pode continuar retornando uma lista em tendência ou alterar o comportamento do endpoint] → Repetir a busca com termo normalizado em caso de ausência exata, validar tipo e títulos localmente e cobrir a situação com respostas simuladas determinísticas.
- [Prefixo/contenção pode aproximar jogos diferentes] → Filtrar produtos do tipo jogo, priorizar igualdade exata, ignorar apenas qualificadores reconhecidos e exigir um único candidato aproximado.
- [Rótulos de edição não cobrem todas as variações comerciais] → Manter comparação conservadora; correspondências não resolvidas continuam mostrando somente a Steam e uma mensagem explicativa.
- [Uma tela de celular muito baixa não comporta todo o formulário] → Compactar espaçamentos em viewports estreitos e permitir rolagem apenas quando necessária, sem esconder conteúdo.
- [Link envolvendo todo o card pode mudar foco/estilo padrão] → Preservar o estilo existente e validar navegação por teclado, foco visível e destino do destaque e da grade.

## Migration Plan

Sem migração de dados. As alterações são compatíveis com a lista de jogos e a rota de comparação existentes. Reverter as mudanças de interface e a lógica de consulta não exige transformação ou recuperação de dados persistidos.
