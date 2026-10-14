# Tasks

## 1. Catálogo e pesquisa

- [ ] 1.1 Substituir o placeholder por uma lista pequena de jogos fixos com capa, nome, texto alternativo e fallback visual; manter o catálogo condicionado ao estado autorizado. Verificar a lista e a renderização dos cards sem preços ou alegações de promoção.
- [ ] 1.2 Adicionar no topo a barra “Comparar Preços”, validar termo vazio e limite de caracteres e encaminhar o termo por navegação segura para `/buscar`. Testar que termos válidos navegam com o valor codificado e termos vazios permanecem no catálogo com mensagem.
- [ ] 1.3 Atualizar `docs/project-overview.md` e `docs/domain-model.md` para descrever o catálogo demonstrativo, sua proteção e a busca Steam pública; verificar que nenhum texto ainda descreve o catálogo como placeholder.

## 2. Recepção do termo na busca Steam

- [ ] 2.1 Inicializar `SearchState.search_term` ao carregar `/buscar` a partir do parâmetro de consulta recebido, limpando o campo quando não houver termo; manter a execução manual pelo botão “Buscar”. Testar rota com termo, rota sem parâmetro e termo editável.
- [ ] 2.2 Preservar validação, busca Steam e consulta de preço existentes ao aceitar o termo da rota. Executar `tests/test_steam.py` e os testes focados do estado/roteamento, confirmando que a busca pública continua sem autenticação.

## 3. Verificação integrada

- [ ] 3.1 Verificar no navegador o catálogo autenticado em larguras estreita e larga, o redirecionamento de usuário não autenticado, o envio do termo para `/buscar` e o fluxo manual de resultados/preço; confirmar fallback acessível para capa indisponível.
- [ ] 3.2 Executar `reflex compile --dry` e a suíte de testes relevante; corrigir apenas regressões relacionadas ao catálogo e confirmar que `/buscar` direto sem parâmetro começa sem termo.
