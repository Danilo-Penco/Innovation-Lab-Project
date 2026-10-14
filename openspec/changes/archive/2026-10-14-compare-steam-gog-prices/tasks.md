# Tasks

## 1. Integração pública da GOG

- [x] 1.1 Confirmar a busca pública GOG em JSON e os campos reais para título, página, capa, disponibilidade e preço BRL sem autenticação; registrar no design o endpoint e um exemplo sanitizado de resposta, e interromper para decisão se esses dados não forem fornecidos publicamente.
- [x] 1.2 Implementar um serviço GOG isolado com timeout, parsing validado, preços em centavos de BRL e correspondência única por título normalizado; adicionar testes HTTP simulados para resultado válido, jogo grátis, ausência/ambiguidade, moeda ausente ou diferente e respostas/erros inválidos.

## 2. Comparação no fluxo de busca

- [x] 2.1 Integrar a consulta GOG à seleção do jogo Steam e obter a capa Steam dos dados do produto; preservar a oferta Steam quando a GOG não puder ser comparada e impedir que respostas assíncronas antigas substituam a seleção atual; testar metadados, sucesso, fallback e seleção concorrente sem chamadas reais às lojas.
- [x] 2.2 Renderizar os cartões Steam e GOG com capa acessível, preço BRL, link seguro em nova aba, destaque do menor preço incluindo grátis e empate, aviso de fallback e layout responsivo; verificar estados comparáveis e indisponíveis em teste de interface.

## 3. Documentação do produto

- [x] 3.1 Atualizar `docs/project-overview.md` e `docs/domain-model.md` para documentar a comparação pública Steam/GOG, o comportamento sem oferta GOG e a Epic fora do escopo; verificar que os documentos não descrevem mais a consulta de preço como exclusiva da Steam.

## 4. Verificação integrada

- [x] 4.1 Executar a suíte de testes e `reflex compile --dry`; validar no navegador `/buscar` sem autenticação, comparação com duas ofertas, fallback Steam quando a GOG não responde ou não corresponde, abertura dos links em nova aba e legibilidade em tela estreita.
