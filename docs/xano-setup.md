# Contrato da API Xano

Este documento versiona o contrato consumido pelo cliente Reflex. Os caminhos e formatos abaixo são os usados por `Projeto/xano.py` e por seus testes; não são uma exportação do workspace Xano. O arquivo `xano/workspace/danilo_penco.xs` contém metadados do workspace, não as definições das rotas ou tabelas. Confirme qualquer alteração no ambiente de teste antes de publicá-la.

## Configuração

O cliente e `scripts/check_xano.py` leem `XANO_API_URL` do ambiente. O checker também exige `XANO_TEST_EMAIL` e `XANO_TEST_PASSWORD`. Configure essas variáveis somente em `.env` local, use uma instância descartável de teste e nunca versione esse arquivo. Não informe valores reais em documentação, issue, log ou saída do checker.

`XANO_API_URL` é a base de API à qual o cliente acrescenta os caminhos `auth/signup`, `auth/login` e `auth/me`. Não inclua token ou credencial na URL.

## Conta de usuário

O domínio identifica a tabela `user` como persistência das contas. Os campos de usuário que o cliente consome em `auth/me` são:

| Campo | Tipo esperado pelo cliente | Uso |
|---|---|---|
| `id` | inteiro | Identificador da conta |
| `created_at` | inteiro (timestamp) | Data de criação retornada pelo Xano |
| `name` | texto | Nome exibido/associado à conta |
| `email` | texto | E-mail normalizado |
| `role` | texto | Papel retornado pelo Xano; autorização deve ocorrer no servidor |

O cliente envia a senha somente a `auth/signup` e `auth/login`; o Xano é responsável por armazenar credenciais de forma segura. Senha e hash não fazem parte das respostas documentadas. A resposta de login/cadastro contém `user_id`, enquanto `auth/me` retorna `id`.

## Endpoints atuais

### `POST auth/signup`

Cadastro de conta; `name` é obrigatório no cliente e deve ser validado também no endpoint.

Entrada:

```json
{
  "name": "<nome>",
  "email": "<email>",
  "password": "<senha>"
}
```

Saída de sucesso HTTP 200:

```json
{
  "authToken": "<token>",
  "user_id": 123
}
```

O token é consumido somente pelo estado server-side Reflex. Não o imprima, não o inclua em URL e não o armazene no navegador.

### `POST auth/login`

Entrada:

```json
{
  "email": "<email>",
  "password": "<senha>"
}
```

Saída de sucesso HTTP 200:

```json
{
  "authToken": "<token>",
  "user_id": 123
}
```

### `GET auth/me`

Exige o token no header HTTP, exatamente no formato `Authorization: Bearer <token>`. Não aceite identidade enviada em query string ou corpo.

Saída de sucesso HTTP 200:

```json
{
  "id": 123,
  "created_at": 1762000000000,
  "name": "<nome>",
  "email": "<email>",
  "role": "<papel>"
}
```

Token ausente ou inválido deve ser recusado com HTTP 401. O cliente fecha o acesso protegido quando recebe esse status.

## Erros esperados pelo cliente

| Situação | Resposta esperada |
|---|---|
| Entrada inválida de cadastro | HTTP 400, `code: "ERROR_CODE_INPUT_ERROR"` e `payload.param` com o campo recusado |
| E-mail já cadastrado | HTTP 403, `code: "ERROR_CODE_ACCESS_DENIED"` |
| Credenciais de login inválidas | HTTP 403, `code: "ERROR_CODE_ACCESS_DENIED"` |
| Token inválido em `auth/me` | HTTP 401 |

Mensagens/payloads de erro não devem conter senha ou token. O cliente sanitiza mensagens antes de apresentá-las.

## Rotas que não devem existir

Os caminhos abaixo devem retornar HTTP 404. O checker envia corpo vazio às chamadas POST e não envia e-mail, token nem credenciais para essas rotas. Qualquer status diferente de 404 significa que a rota ainda existe; uma falha de rede ou status inesperado é reportado como SKIP.

| Método | Caminho |
|---|---|
| POST | `/message/send_welcome_email` |
| POST | `/reset/magic-link-login` |
| GET | `/reset/request-reset-link` |
| POST | `/reset/update_password` |

Solicitações e aprovação de lojas são funcionalidades futuras: não há endpoints ou tabelas dessas funcionalidades neste contrato atual. Quando implementadas, a identidade do solicitante e o papel administrativo devem ser derivados e verificados no servidor, nunca de `user_id` fornecido pelo cliente.

## Regras de segurança e escopo

- Chamadas protegidas enviam `Authorization: Bearer <token>`; não remover o prefixo `Bearer`.
- Nunca registrar, imprimir ou incluir token/senha em URL, exemplo com valor real ou resposta de erro.
- Validar autorização no backend; campos de identidade fornecidos pelo cliente não conferem autorização.
- Não persistir preços, histórico de preços, buscas ou metadados temporários.
- Alterações de endpoints, tabelas ou campos devem atualizar este documento e os testes do cliente.
