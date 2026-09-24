# AGENTS.md

## Documentação
Antes de realizar alterações significativas, consultar docs/project-overview.md e docs/domain-model.md.

## Arquitetura
Respeitar a arquitetura definida: backend em Xano/XanoScript, frontend em HTML/CSS/JavaScript. Não introduzir tecnologias alternativas de backend sem justificativa.

## Código
Reutilizar código existente quando apropriado. Evitar duplicação. Não modificar funcionalidades não relacionadas à mudança atual sem justificativa.

## Segurança
Regras de autorização (ex.: quem pode criar/aprovar lojas) devem ser aplicadas no backend (Xano), nunca apenas no frontend.

## Desenvolvimento
Mudanças devem utilizar o fluxo do OpenSpec (Explore -> Propose -> Review -> Apply -> Archive).

## Testes
Mudanças funcionais devem possuir estratégia de verificação (ex.: validar endpoints no Xano com o Xano Developer MCP antes de concluir).
