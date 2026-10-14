# Proposal

## Why

O ComparaKeys precisa autenticar os usuários antes de encaminhá-los às funcionalidades protegidas, e a experiência atual abre diretamente na busca pública da Steam. Esta mudança coloca login e cadastro como entrada do site e estabelece o fluxo autenticado que levará ao catálogo.

## What Changes

- Criar uma página inicial de login com campos de e-mail e senha e um botão “Cadastrar-se” logo abaixo do campo de senha.
- Implementar cadastro e autenticação com persistência no banco de dados próprio da aplicação Reflex, sem usar o Xano para credenciais ou sessões de usuário.
- Após login ou cadastro bem-sucedido, exibir brevemente uma splash screen e encaminhar o usuário autenticado para uma página de catálogo placeholder.
- Exigir autenticação no backend Reflex para acessar o catálogo e redirecionar sessões não autenticadas para login.
- Manter a busca pública Steam existente em uma rota própria, sem exigir autenticação para essa funcionalidade.
- Aplicar identidade visual em preto e roxo nas páginas de autenticação e no estado de transição.
- Deixar recuperação de senha, provedores de login externo e papéis/permissões de administrador fora do escopo.

## Capabilities

### New Capabilities

- `user-authentication`: cadastro e login por e-mail e senha, persistência local Reflex, controle de acesso às páginas protegidas e encaminhamento ao catálogo após uma transição breve.

### Modified Capabilities

Nenhuma. A capacidade `steam-price-search` permanece pública e acessível em sua própria rota.

## Impact

- Aplicação Reflex em `Projeto/Projeto.py`: novas rotas e telas de login, cadastro e placeholder do catálogo, preservando a rota existente de busca Steam.
- Persistência Reflex: novo modelo/tabela de usuário e armazenamento da sessão de autenticação; nenhuma credencial ou sessão será delegada ao Xano.
- Segurança e navegação: validação de credenciais, proteção de rotas no backend Reflex e redirecionamento após autenticação.
- Documentação e testes: registrar o fluxo, a separação da busca pública e a verificação de cadastro/login, sessão, acesso protegido e splash screen.
