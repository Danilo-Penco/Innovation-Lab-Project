# ComparaKeys

Aplicação Reflex para comparar preços atuais de jogos na Steam e na GOG. A autenticação usa os endpoints Xano descritos no [contrato da API](docs/xano-setup.md); buscas e preços não são persistidos.

## Ambiente local

Use Python e instale as dependências do projeto:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Crie um `.env` local, que é ignorado pelo Git, com os dados de uma instância Xano **de teste**:

```dotenv
XANO_API_URL=https://<host-de-teste>/api:auth
XANO_TEST_EMAIL=<email-de-teste>
XANO_TEST_PASSWORD=<senha-de-teste>
```

Substitua os marcadores localmente. Não coloque credenciais no código, README, issues ou logs, e não use conta de produção para o checker.

## Verificações

Execute os testes automatizados:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests
```

Para validar o contrato Xano na instância configurada:

```powershell
.\.venv\Scripts\python.exe scripts\check_xano.py
```

O checker usa as credenciais somente para login e validação de `auth/me`. Os probes das rotas legadas usam corpo vazio e nunca enviam e-mail, token ou senha a elas; o cadastro sem `name` também usa corpo vazio. O script não imprime token, senha ou respostas integrais e deve ser executado somente em uma instância de teste descartável. Consulte [xano-setup.md](docs/xano-setup.md) para os endpoints e formatos esperados.
