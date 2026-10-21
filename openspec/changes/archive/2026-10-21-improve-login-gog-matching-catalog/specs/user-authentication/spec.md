# Spec Delta

## MODIFIED Requirements

### Requirement: Página inicial de login
O sistema SHALL apresentar a tela de login como primeira página do site, com campos de e-mail e senha, uma ação explícita para entrar e o botão “Cadastrar-se” imediatamente abaixo do campo de senha. A interface de autenticação SHALL usar um fundo com cores preto e roxo e SHALL ser utilizável em telas estreitas e largas. Os formulários de login e cadastro SHALL ficar centralizados na área visível da tela, com espaçamento superior reduzido, sem exigir rolagem vertical em tamanhos comuns de desktop e celular.

#### Scenario: Acesso inicial sem sessão
- **WHEN** uma pessoa sem sessão autenticada abre a raiz do site
- **THEN** o sistema apresenta o formulário de login e o botão “Cadastrar-se” abaixo do campo de senha

#### Scenario: Abrir cadastro
- **WHEN** a pessoa seleciona “Cadastrar-se”
- **THEN** o sistema apresenta o formulário de criação de conta com campos de e-mail e senha e uma ação para concluir o cadastro

#### Scenario: Formulário centralizado em desktop
- **WHEN** uma pessoa abre a tela de login ou cadastro em uma janela desktop comum
- **THEN** o formulário aparece centralizado vertical e horizontalmente e fica visível sem rolagem vertical

#### Scenario: Formulário centralizado em celular
- **WHEN** uma pessoa abre a tela de login ou cadastro em uma tela de celular comum
- **THEN** o formulário usa espaçamento compacto, aparece centralizado e fica visível sem rolagem vertical
