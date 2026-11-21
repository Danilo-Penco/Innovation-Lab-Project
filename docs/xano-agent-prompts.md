# Prompts para o Xano Agent

Use os prompts na ordem, um por vez, no workspace de teste. Cole no chat do Xano Agent apenas o texto do bloco de cada prompt. Compare o resultado com o contrato em [xano-setup.md](./xano-setup.md). Não inclua tokens, senhas, URLs privadas ou dados reais nos prompts ou nos resultados.

## 1. Tornar `name` obrigatório no cadastro

```
Atualize o endpoint existente POST auth/signup para exigir name, email e password no servidor. Recuse name ausente, vazio ou composto só por espaços com HTTP 400 e ERROR_CODE_INPUT_ERROR, com payload.param igual a name. Mantenha o formato de resposta de sucesso {"authToken": "...", "user_id": N}, o erro 403 de e-mail duplicado e o erro 400 de senha fraca com payload.param igual a password. Não altere auth/login nem auth/me. Não crie conta parcial nem retorne senha ou hash. Teste um cadastro válido e chamadas sem name, com name vazio e com name só de espaços. Mostre apenas endpoint, status e nome do campo; nunca mostre tokens ou senhas. Apague as contas de teste que criar.
```

## 2. Remover as rotas `reset/*` e `message/*`

```
Exclua estes quatro endpoints do grupo Authentication: POST message/send_welcome_email, POST reset/magic-link-login, GET reset/request-reset-link e POST reset/update_password. Não exclua auth/signup, auth/login nem auth/me. Não crie rotas equivalentes. Depois, liste os endpoints que restaram no grupo e confirme que são só os três de auth/*. Não imprima payloads, tokens ou credenciais.
```

Se o Agent não conseguir, exclua à mão: abra o endpoint, menu de três pontos, Delete.

## 3. Lojas, histórico, favoritos e alertas (NÃO USAR AGORA)

Estes prompts serão gerados pelas fases F2 a F5 da evolução do site, depois que o contrato de cada tabela estiver definido no `xano-setup.md`. Criar tabelas no Xano antes disso deixaria o banco com estruturas que o Reflex não usa.