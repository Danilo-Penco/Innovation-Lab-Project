# Design

## Context

Consulte `proposal.md` para motivação e `specs/steam-price-search/spec.md` para o contrato observável. A rota pública `/buscar` já lista jogos via busca Steam e, após a seleção pelo App ID, consulta preço BRL. O serviço Steam já valida respostas externas, usa timeout, converte falhas de transporte em erro recuperável e representa preços pagos, grátis e indisponíveis; o estado Reflex protege respostas assíncronas contra seleções antigas por identificadores de requisição. Os preços não são persistidos.

## Goals / Non-Goals

**Goals:**
- Estender o fluxo de seleção existente para consultar uma oferta pública da GOG e exibir apenas uma correspondência inequívoca.
- Isolar a integração GOG e manter a oferta Steam visível quando a GOG estiver indisponível.
- Manter preços em unidades inteiras de centavos de BRL e reutilizar a formatação monetária existente.
- Renderizar cartões acessíveis com links externos controlados e adaptação a telas estreitas.

**Non-Goals:**
- Implementar busca independente de jogos na GOG, login na GOG, compra, histórico ou cache.
- Integrar a Epic Games Store, fazer conversão cambial, aproximar títulos por similaridade ou selecionar manualmente entre resultados GOG.
- Alterar autenticação, banco de dados ou outras rotas.

## Decisions

1. **Usar o resultado Steam selecionado como origem da comparação.** A pessoa continua pesquisando e escolhendo um jogo pelo identificador Steam existente. Só depois dessa escolha a aplicação consulta a GOG com o nome resolvido pela Steam. Isso evita comparar títulos ainda ambíguos da busca inicial e preserva o fluxo atual.

2. **Usar o catálogo público JSON da GOG, sem scraping.** A busca anônima `GET https://catalog.gog.com/v1/catalog` foi verificada com HTTP 200 usando `limit`, `order=desc:trending`, `productType=in:game`, `query`, `locale=en-US`, `currencyCode=BRL` e `countryCode=BR`. Um resultado de teste para Baldur's Gate 3 forneceu `id`, `title`, `productType=game`, `storeLink=https://www.gog.com/en/game/baldurs_gate_iii`, `coverHorizontal=https://images.gog-statics.com/<hash>.png` e `price.finalMoney={amount:"199.99",currency:"BRL"}`. O `storeLink`, capa e valor devem ser validados; consultar o catálogo novamente a cada seleção, sem cache. `locale=pt-BR` retornou lista vazia no teste, portanto usar `en-US` para localizar títulos e manter `countryCode=BR`/`currencyCode=BRL` para o preço brasileiro. Não adicionar dependência se `httpx` existente for suficiente. Se a forma do endpoint mudar ou os dados necessários deixarem de ser públicos, interromper para rever o escopo em vez de substituir silenciosamente a busca por scraping.

3. **Aceitar somente correspondência única de título normalizado.** Normalizar removendo espaços externos, condensando espaços consecutivos e ignorando diferenças de maiúsculas/minúsculas; não remover palavras, pontuação ou edições do título. Zero ou mais de um resultado exato não é correspondência segura. Essa regra reduz o risco de exibir o preço de uma edição ou jogo diferente; a alternativa de correspondência aproximada foi descartada por poder comparar produtos incorretos.

4. **Manter falhas GOG isoladas da oferta Steam.** Representar separadamente ausência/ambiguidade/preço não comparável e falha técnica GOG, convertendo ambos em aviso visível no estado da interface sem apagar a Steam. A falha da própria Steam continua seguindo o tratamento atual. As chamadas e atualizações de estado devem preservar os identificadores de requisição existentes para que uma resposta tardia não substitua a seleção mais recente.

5. **Comparar valores numéricos em centavos, sem conversão.** Tratar preço pago como centavos de BRL e jogo grátis como zero. Destacar o menor preço em verde apenas quando os dois valores forem comparáveis; em empate, destacar ambos. Se um valor estiver indisponível, não declarar vencedor. Reutilizar a formatação BRL existente.

6. **Usar links de loja canônicos e validar destinos externos.** Construir o link Steam a partir do App ID selecionado. Para GOG, usar o destino fornecido pelo resultado público somente após validar HTTPS e o domínio esperado da loja. Abrir os links em nova aba com `noopener`/`noreferrer`; o texto do nome do jogo é o controle acessível.

7. **Adaptar a composição à largura disponível.** Apresentar os cartões em duas colunas lado a lado quando houver espaço e empilhá-los em telas estreitas, sem mudar a identidade preta e roxa existente. A comparação continua sendo um único resultado de busca, sem estado persistido.

## Risks / Trade-offs

- [A busca pública ou o preço regional da GOG pode mudar de formato ou não disponibilizar BRL] → manter parsing estrito, testes com respostas válidas/inválidas e fallback explícito para Steam; confirmar os campos reais do endpoint antes de codificar o adaptador.
- [Títulos iguais podem representar edições diferentes] → exigir correspondência única do título normalizado e não usar correspondência aproximada.
- [A consulta adicional aumenta latência e pode falhar independentemente da Steam] → executar a consulta GOG de modo independente e manter o cartão Steam com aviso caso a GOG falhe.
- [Links externos vindos da resposta da GOG podem ser inválidos ou inesperados] → validar esquema e domínio e construir o link Steam localmente a partir do App ID.
- [No layout estreito, duas colunas podem ficar ilegíveis] → mudar para cartões empilhados em larguras pequenas e validar a interface responsiva.

## Migration Plan

Não há migração de dados nem alteração de armazenamento. Implantar o adaptador e a apresentação sem modificar os contratos existentes da busca Steam. Para rollback, remover a consulta GOG e retornar à apresentação Steam atual; nenhuma informação persistida exige limpeza.
