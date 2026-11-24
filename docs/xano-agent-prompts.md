# Prompts para o Xano Agent

Use os prompts na ordem, um por vez, no workspace de teste. Cole no chat do Xano Agent apenas o texto do bloco de cada prompt. Compare o resultado com o contrato em [xano-setup.md](./xano-setup.md). Não inclua tokens, senhas, URLs privadas ou dados reais nos prompts ou nos resultados.

## Validar o contrato de histórico

Use somente um workspace de teste isolado e duas contas descartáveis distintas, ambas inicialmente sem histórico e sem uso concorrente. Configure `XANO_API_URL`, `XANO_TEST_EMAIL`, `XANO_TEST_PASSWORD`, `XANO_TEST_EMAIL_2` e `XANO_TEST_PASSWORD_2` em `.env` local, fora do Git. O checker não executa contra produção, não imprime credenciais e pula as operações mutáveis se qualquer histórico de teste já existir.

No PowerShell, execute:

```powershell
.\.venv\Scripts\python.exe scripts\check_xano.py
```

O checker mostra `PASS`, `FAIL` ou `SKIP` por cenário. Depois de confirmar que as duas contas estavam vazias, ele remove os registros sintéticos que criou por `DELETE /history` e verifica que ambas voltaram a ficar vazias. Não execute o comando com contas que contenham dados a preservar.

## 1. Tornar `name` obrigatório no cadastro

```
Atualize o endpoint existente POST auth/signup para exigir name, email e password no servidor. Recuse name ausente, vazio ou composto só por espaços com HTTP 400 e ERROR_CODE_INPUT_ERROR, com payload.param igual a name. Mantenha o formato de resposta de sucesso {"authToken": "...", "user_id": N}, o erro 403 de e-mail duplicado e o erro 400 de senha fraca com payload.param igual a password. Não altere auth/login nem auth/me. Não crie conta parcial nem retorne senha ou hash. Teste um cadastro válido e chamadas sem name, com name vazio e com name só de espaços. Mostre apenas endpoint, status e nome do campo; nunca mostre tokens ou senhas. Apague as contas de teste que criar.
```

## 2. Remover as rotas `reset/*` e `message/*`

```
Exclua estes quatro endpoints do grupo Authentication: POST message/send_welcome_email, POST reset/magic-link-login, GET reset/request-reset-link e POST reset/update_password. Não exclua auth/signup, auth/login nem auth/me. Não crie rotas equivalentes. Depois, liste os endpoints que restaram no grupo e confirme que são só os três de auth/*. Não imprima payloads, tokens ou credenciais.
```

Se o Agent não conseguir, exclua à mão: abra o endpoint, menu de três pontos, Delete.

## 3. Criar histórico de pesquisas autenticado

```
No grupo Authentication do workspace de teste, crie manualmente a tabela search_history e os endpoints POST /history, GET /history e DELETE /history. Não use, gere, publique ou faça push de XanoScript.

Tabela search_history:
- id: inteiro gerado pelo Xano.
- user: relação obrigatória com a tabela user; em todas as operações, preencher/filtrar exclusivamente com $auth.id.
- term: texto obrigatório, aparado, entre 1 e 100 caracteres.
- steam_app_id: inteiro obrigatório maior que zero.
- game_name: texto obrigatório, aparado, entre 1 e 200 caracteres.
- created_at: timestamp inteiro em milissegundos, gerado pelo servidor.
Crie índices para user e created_at. Não crie campos de preço, moeda, cotação ou user_id recebido do cliente.

Todos os endpoints devem exigir autenticação Bearer e retornar HTTP 401 sem token válido. Nunca aceite user_id em path, query ou corpo.

POST /history:
- Entrada exata: {"term":"Hades","steam_app_id":1145360,"game_name":"Hades"}.
- Valide todos os limites da tabela.
- Consulte o registro mais recente do $auth.id. Se o steam_app_id recebido for igual, atualize esse registro, incluindo term, game_name e created_at; não crie duplicata consecutiva. Caso contrário, crie um registro.
- Sucesso HTTP 200: {"id":321}, usando o id inserido ou atualizado.

GET /history:
- Não recebe corpo. Filtre por $auth.id, ordene por created_at decrescente e id decrescente em caso de empate, e limite a 20 itens.
- Sucesso HTTP 200: array de objetos no formato {"id":321,"term":"Hades","steam_app_id":1145360,"game_name":"Hades","created_at":1762000000000}.

DELETE /history:
- Não recebe corpo. Exclua somente linhas de $auth.id.
- Sucesso HTTP 200: {"deleted":1}, com a quantidade removida.

Teste em ambiente descartável com duas contas de teste distintas e inicialmente vazias: confirme 401 sem token em cada endpoint, header Authorization: Bearer <token>, formatos de resposta, deduplicação consecutiva e que cada conta lista e exclui somente seus próprios registros. Prepare as contas para que o checker possa remover somente os registros sintéticos que criar. Não exponha tokens, senhas nem corpos com credenciais na resposta. Os endpoints não devem gravar buscas por digitação, preços ou cotações.
```

## 4. Lojas, favoritos e alertas (NÃO USAR AGORA)

Os prompts para funcionalidades restantes serão adicionados quando seus contratos estiverem documentados no `xano-setup.md`. Não crie tabelas/endpoints antes disso.