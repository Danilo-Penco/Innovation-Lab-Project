# Tasks

## 1. Persistência e serviços de autenticação

- [x] 1.1 Configurar o SQLite da aplicação Reflex e criar o modelo de conta com e-mail normalizado único, salt e hash de senha; gerar/revisar e aplicar a migração em um banco de teste e verificar que a tabela foi criada.
- [x] 1.2 Implementar normalização/validação de e-mail e senha, hash PBKDF2-HMAC e comparação de credenciais no backend; adicionar testes para entradas válidas/inválidas, duplicatas normalizadas, login correto/incorreto e garantir que nenhuma senha em texto puro seja persistida.
- [x] 1.3 Testar tratamento de conflitos de e-mail concorrentes e falhas inesperadas do banco; confirmar que somente a violação única esperada vira mensagem de duplicidade e que outras falhas não são tratadas como sucesso.

## 2. Fluxos, páginas e experiência visual

- [x] 2.1 Transferir a página de busca Steam atual para `/buscar` sem alterar seu comportamento público; executar `tests/test_steam.py` e verificar que os handlers de busca e preço continuam ligados à rota.
- [x] 2.2 Criar a página inicial de login e a página `/cadastro`, com campos e mensagens acessíveis, botão “Cadastrar-se” imediatamente abaixo da senha na página inicial e identidade responsiva preta/roxa; verificar visualmente em viewport estreita e larga.
- [x] 2.3 Conectar os formulários ao serviço de autenticação, limpar os campos de senha após a submissão e testar cadastro/login bem-sucedidos, erros recuperáveis e ausência de sessão em credenciais inválidas.
- [x] 2.4 Criar `/catalogo` como placeholder protegido por validação da sessão no backend, com redirecionamento à raiz para sessão ausente/inválida; testar acesso direto autenticado e não autenticado sem expor conteúdo protegido.
- [x] 2.5 Exibir a splash screen somente depois de autenticação bem-sucedida e encaminhar a sessão a `/catalogo` após breve temporização; testar que login e cadastro acionam a transição e que falhas permanecem no formulário.
- [x] 2.6 Atualizar `docs/project-overview.md` e `docs/domain-model.md` para documentar login inicial, armazenamento Reflex, catálogo protegido e exceção da busca pública `/buscar`; revisar os textos para não contradizer a navegação implementada.

## 3. Verificação integrada

- [x] 3.1 Executar os testes unitários relevantes e `reflex compile --dry`; corrigir falhas relacionadas a autenticação, migrações e rotas.
- [x] 3.2 Validar no navegador os fluxos sem sessão e com sessão: raiz/login, cadastro, splash→catálogo, bloqueio de acesso direto e busca Steam anônima em `/buscar`; confirmar a paleta preto/roxo e a renderização responsiva.
