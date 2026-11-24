# ComparaKeys

Aplicação Reflex para comparar preços atuais de jogos na Steam e na GOG e consultar até cinco ofertas adicionais de lojas via CheapShark. A comparação identifica cada loja pelo nome e logotipo, destaca o menor preço comparável e informa a origem temporal do valor. Steam e GOG permanecem em BRL regional; ofertas CheapShark em USD exibem o valor original e, quando há cotação Frankfurter, o equivalente aproximado em BRL, a taxa exata e a data da cotação. Sem cotação, o preço permanece em US$. A rota pública `/` apresenta o projeto e oferece “Entrar” e “Cadastrar” a visitantes; o login fica em `/entrar` e o cadastro em `/cadastro`. A autenticação usa os endpoints Xano descritos no [contrato da API](docs/xano-setup.md); preços e cotações não são persistidos.

Steam e GOG não fornecem um horário específico de atualização do preço nos endpoints públicos consultados; nesses casos, a comparação mostra “Consultado pelo ComparaKeys” no fuso `America/Sao_Paulo`. A CheapShark fornece `lastChange` por oferta, e esse instante é apresentado como atualização informada pela fonte. A leitura do cache de ofertas de cinco minutos preserva o horário original da consulta. As integrações têm timeout de 10 segundos, no máximo uma repetição automática somente para erro de rede/timeout e tratamento de HTTP 429/`Retry-After`; cada falha mantém os resultados válidos das demais lojas e pode ser repetida explicitamente.

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
