# Tarefas

## 1. Busca ao vivo

- [x] 1.1 Atualizar o estado e o campo de busca para consultar a Steam automaticamente após uma pausa curta na digitação, sem botão de envio; verificar com testes que uma consulta válida ocorre automaticamente e que a pausa não gera uma chamada por tecla.
- [x] 1.2 Limpar resultados quando o termo ficar vazio e proteger estado, carregamento e erros contra respostas fora de ordem; verificar com testes de termo vazio, falha da Steam e resposta tardia.
- [x] 1.3 Iniciar automaticamente a busca quando `/buscar` recebe um termo do catálogo e atualizar a documentação do fluxo; verificar com teste do termo encaminhado e conferir a descrição em `docs/project-overview.md`.

## 2. Rota dedicada de comparação

- [x] 2.1 Fazer a seleção de um resultado validar seu App ID e navegar para `/comparar?app_id=<id>`; verificar que a seleção não renderiza a comparação na página de busca e que a URL contém o App ID selecionado.
- [x] 2.2 Carregar a comparação ao abrir diretamente a rota, consultando Steam antes de usar o nome retornado na busca GOG, e apresentar estados de carregamento e falha recuperável; verificar jogos pagos, gratuitos, preço indisponível, falha GOG e App ID inválido em testes.
- [x] 2.3 Reutilizar os cartões e regras visuais existentes na rota dedicada e atualizar a documentação do fluxo de pesquisa e comparação; verificar visualmente ambas as rotas e conferir `docs/project-overview.md` e `docs/domain-model.md`.

## 3. Verificação integrada

- [x] 3.1 Executar os testes direcionados de busca, catálogo, Steam e comparação, além da verificação de compilação do Reflex; confirmar que busca ao vivo, links do catálogo e comparação direta funcionam sem persistir termos ou preços.
