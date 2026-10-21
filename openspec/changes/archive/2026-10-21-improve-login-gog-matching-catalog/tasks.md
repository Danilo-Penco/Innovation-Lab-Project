# Tasks

## 1. Layout de autenticação

- [x] 1.1 Ajustar o layout dos cartões de login e cadastro para centralização responsiva e espaçamento vertical compacto, preservando rolagem quando necessária; verificar `/` e `/cadastro` em desktop e celular.
- [x] 1.2 Adicionar cobertura de regressão para o layout de autenticação e atualizar `docs/project-overview.md` se o comportamento descrito precisar de ajuste; verificar a cobertura e a documentação.

## 2. Correspondência GOG

- [x] 2.1 Implementar a consulta alternativa sem pontuação e a seleção de correspondências GOG: jogo exato primeiro, depois candidato aproximado único após remover qualificadores reconhecidos; adicionar testes incluindo “Hollow Knight: Silksong” e verificar `tests/test_gog.py`.
- [x] 2.2 Distinguir ausência, ambiguidade, preço BRL indisponível e falha técnica na resposta da comparação; adicionar testes de estado/mensagem e verificar `tests/test_search_state.py`.
- [x] 2.3 Atualizar `docs/project-overview.md` e `docs/domain-model.md` para refletir correspondência GOG aproximada única e mensagens específicas; verificar consistência com as specs.

## 3. Catálogo e navegação

- [x] 3.1 Tornar clicáveis os cards em destaque e da grade, ligando cada card ao `/comparar?app_id=<id>` de seu jogo; verificar IDs positivos e únicos e adicionar testes para os destinos.
- [x] 3.2 Acrescentar após a grade o rodapé institucional com link para `/buscar`; verificar a presença, posição final e destino do link.
- [x] 3.3 Atualizar `docs/project-overview.md` e `docs/domain-model.md` para descrever navegação direta e rodapé do catálogo; verificar consistência com as specs.

## 4. Verificação integrada

- [x] 4.1 Executar a suíte de testes relevante e `reflex compile --dry`; verificar que todos passam.
- [ ] 4.2 Verificar visualmente login e cadastro sem rolagem em tamanhos comuns de desktop/celular e validar navegação pelos cards do destaque e da grade até a comparação correta. Login/cadastro foram medidos em desktop e celular sem rolagem, e os testes confirmam os destinos dos cards; a interação no navegador segue pendente porque o servidor Reflex apresenta `Connection Error` e falha de transporte WebSocket.
