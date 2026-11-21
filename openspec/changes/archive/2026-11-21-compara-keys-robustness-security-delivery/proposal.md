# Proposal

## Why

O ComparaKeys já integra autenticação pelo Xano e oferece busca pública Steam/GOG, mas ainda precisa de maior resiliência do cliente Xano, cache transitório sem preços, sessão confiável após recarga e orientação acessível nos formulários. A mudança também padroniza a auditoria de interface e automatiza a verificação/documentação do contrato Xano sem depender de export manual do workspace.

## What Changes

- Auditar `/`, `/cadastro`, `/catalogo`, `/buscar` e `/comparar`; registrar no `design.md` os problemas observados de UX, texto, responsividade e acessibilidade, e corrigir os pequenos.
- Usar chamadas autenticadas compartilhadas com `Authorization: Bearer <token>`, conforme validado no Xano real; testar o formato. Repetir uma única vez apenas em erro de rede/timeout, nunca em 4xx; mapear erros com mensagens próprias, sem prints de debug nem mensagem genérica que esconda a causa.
- Em 401 de rota protegida, encerrar a sessão e redirecionar ao login com aviso. Manter a validação local de senha com pelo menos uma letra e mapear `400` com `param=password` para mensagem específica.
- Adicionar cache volátil, limitado e com TTL máximo de 5 minutos para resultados de busca e metadados Steam/GOG; nunca cachear preços, que devem ser consultados atualizados em cada comparação.
- Exibir nos formulários de login e cadastro a regra da senha (mínimo 8 caracteres e pelo menos uma letra) e um controle acessível para mostrar/ocultar a senha.
- Verificar se a sessão sobrevive a recarregar a página; se não, adotar persistência server-side segura que não exponha o token ao JavaScript.
- Criar `docs/xano-agent-prompts.md` com prompts prontos para o Xano Agent: exigir `name` no signup, remover endpoints `reset/*` e `message/*`, e criar tabelas/endpoints de funcionalidades futuras documentadas, sempre derivando o usuário autenticado do token.
- Criar `scripts/check_xano.py`, que lê `XANO_API_URL`, `XANO_TEST_EMAIL` e `XANO_TEST_PASSWORD` do `.env`, imprime PASS/FAIL por endpoint, verifica signup sem `name`, 401 de endpoints autenticados sem token e ausência dos endpoints `reset/*` e `message/*`; nunca imprime senha ou token. Documentar o uso no README.
- Manter `docs/xano-setup.md` como contrato versionado no GitHub, com tabelas, campos, endpoints e exemplos de entrada e saída. Regenerar o código do grupo de API é opcional; não exigir export manual do workspace.
- Não incluir novas lojas, e-mail ou notificações push.

## Capabilities

### New Capabilities

Nenhuma.

### Modified Capabilities

- `user-authentication`: especificar uso de token Bearer, chamadas autenticadas compartilhadas, retry apenas de rede/timeout, mapeamentos próprios, encerramento de sessão e aviso em 401 protegido, validação local de senha e continuidade segura após recarga.
- `steam-price-search`: especificar cache temporário de resultados/metadados sem preços e estados de busca/comparação acessíveis.
- `game-catalog`: manter os requisitos de responsividade e acessibilidade identificados na auditoria das telas.

## Impact

- Código futuro: `Projeto/xano.py`, `Projeto/Projeto.py`, `Projeto/steam.py`, `Projeto/gog.py` e `scripts/check_xano.py`.
- Testes futuros: cliente Xano, autenticação/sessão, cache Steam/GOG, telas e contrato automatizado Xano.
- Documentação versionada: `docs/xano-setup.md`, `docs/xano-agent-prompts.md`, README e documentos de arquitetura/domínio; export Xano manual não é pré-requisito.
- Serviços: endpoints existentes `auth/signup`, `auth/login` e `auth/me`, APIs públicas Steam/GOG e futuros endpoints documentados; nenhum segredo deve ser registrado, exibido ou incluído no código.
