# Tasks

## 1. Autenticação no Xano

- [ ] 1.1 Verificar os recursos de autenticação e a configuração de hospedagem/origem do frontend no Xano; selecionar o transporte e ciclo de vida de sessão compatíveis e validar o fluxo em ambiente de teste antes de integrar a interface.
- [ ] 1.2 Configurar identidade e papel no Xano e implementar cadastro público; validar por chamadas diretas que novas contas recebem `usuario`, que papel enviado pelo cliente não concede privilégios, que e-mail duplicado é rejeitado e que a resposta não expõe a senha.
- [ ] 1.3 Implementar login usando a autenticação nativa do Xano; validar credenciais corretas e rejeição de credenciais inválidas sem diferenciar e-mail inexistente de senha incorreta.

## 2. Proteção e autorização no backend

- [ ] 2.1 Exigir autenticação nas operações do site que requerem login; validar diretamente no backend que chamadas anônimas são rejeitadas e que chamadas autenticadas são reconhecidas.
- [ ] 2.2 Aplicar verificação de papel `admin` na operação backend de aprovação de solicitações de loja; validar aprovação por admin e rejeição por usuario e chamada anônima, confirmando que as tentativas negadas não alteram a solicitação.
- [ ] 2.3 Documentar no modelo de domínio que o cadastro atribui `usuario` e que o primeiro admin é promovido manualmente por operador autorizado no Xano; validar que essa conta pode aprovar e que não existe autoelevação pelo cadastro público.

## 3. Fluxos de autenticação no frontend

- [ ] 3.1 Implementar formulários de cadastro e login integrados aos endpoints Xano; validar criação de conta, autenticação, mensagens de erro e apresentação dos estados autenticado/não autenticado.
- [ ] 3.2 Integrar o transporte de sessão definido em 1.1 sem colocar credenciais na URL ou em `localStorage`; validar chamadas protegidas e o comportamento de sessão após recarregar a página conforme o mecanismo escolhido.

## 4. Verificação integrada

- [ ] 4.1 Executar os cenários de cadastro, login, acesso autenticado e aprovação por papel com o Xano Developer MCP; validar XanoScript e confirmar que as verificações de autorização ocorrem no backend, independentemente da interface.