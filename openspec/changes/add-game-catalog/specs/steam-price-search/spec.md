# Spec Delta

## MODIFIED Requirements

### Requirement: Busca pública de jogos na Steam
O sistema SHALL permitir que uma pessoa sem autenticação pesquise jogos pelo nome na Steam. A busca SHALL consultar dados atuais da Steam quando for executada e SHALL apresentar opções identificáveis para que a pessoa escolha o jogo correto. Quando a pessoa chega de uma pesquisa submetida no catálogo, o campo de busca SHALL ser preenchido com o termo encaminhado; a busca na Steam SHALL continuar sendo executada pela ação de pesquisa existente.

#### Scenario: Busca com correspondências
- **WHEN** uma pessoa informa um nome de jogo válido e executa a busca
- **THEN** o sistema consulta a Steam e apresenta os jogos correspondentes para escolha, sem exigir login

#### Scenario: Busca sem correspondências
- **WHEN** a Steam não encontra jogo correspondente ao nome pesquisado
- **THEN** o sistema informa que nenhum resultado foi encontrado e permite uma nova busca

#### Scenario: Busca sem texto
- **WHEN** a pessoa tenta executar a busca sem informar texto após remover espaços em branco
- **THEN** o sistema informa que é necessário preencher o nome e não consulta a Steam

#### Scenario: Termo recebido do catálogo
- **WHEN** a pessoa submete uma pesquisa no catálogo e chega à rota `/buscar`
- **THEN** o campo de busca apresenta o termo encaminhado e a pessoa pode executar a busca existente
