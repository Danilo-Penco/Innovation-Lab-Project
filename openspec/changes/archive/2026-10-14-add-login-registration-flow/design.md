# Design

## Context

Veja [proposal.md](./proposal.md) para motivação e [specs/user-authentication/spec.md](./specs/user-authentication/spec.md) para o contrato observável. Hoje a raiz (`/`) renderiza a busca pública Steam em `Projeto/Projeto.py`, e `rxconfig.py` registra tema/plugins sem configurar conexão de banco. O projeto usa Reflex 0.9.12; a documentação Reflex atual recomenda SQLModel/SQLAlchemy diretamente para novos modelos, pois `rx.Model` foi descontinuado a partir da versão 0.9.2.

## Goals / Non-Goals

**Goals:**

- Armazenar contas em SQLite gerenciado pela aplicação Reflex, validar a identidade no backend e não expor senhas ou confiar em dados editáveis do navegador para autorizar o catálogo.
- Preservar a implementação da busca Steam sem autenticação, movendo sua página para uma rota distinta da raiz.
- Minimizar novas dependências e manter a autenticação separada da integração Steam.

**Non-Goals:**

- Usar Xano, OIDC, login social, serviço externo de identidade ou autenticação empresarial.
- Criar confirmação de e-mail, recuperação de senha, papéis administrativos, permissões ou conteúdo real para o catálogo.
- Acrescentar suporte a múltiplas instâncias com banco compartilhado ou estratégia de autenticação distribuída.

## Decisions

1. **Usar o banco SQLite configurado pela aplicação Reflex e SQLModel/SQLAlchemy.** Configurar explicitamente o `db_url` SQLite do app, usar uma sessão de banco curta por operação de cadastro/login e preparar a migração do modelo. A documentação Reflex recomenda SQLModel/SQLAlchemy para modelos novos; `rx.Model` é legado e foi descontinuado em Reflex 0.9.2. A alternativa de usar Xano ou a integração enterprise de autenticação foi descartada porque o requisito determina persistência Reflex e não contempla identidade externa.

2. **Separar as rotas públicas e autenticadas.** Manter `/` como login, usar `/cadastro` para criação de conta, `/catalogo` como placeholder protegido e transferir a busca Steam atual para `/buscar`. Essa separação preserva a especificação pública existente sem tornar a página de entrada ambígua. A proteção deve validar a sessão no backend na carga da rota e em qualquer evento futuro que forneça dados protegidos; ocultar links na interface não é controle de acesso.

3. **Manter somente a identidade mínima na sessão Reflex.** Após verificar credenciais, guardar no estado server-side da sessão apenas o identificador da conta (sem senha, hash ou salt). Ao acessar catálogo, validar a identidade contra o banco e redirecionar sessões ausentes/inválidas para `/`. Não aceitar um identificador de usuário vindo como parâmetro de evento para decidir autorização, nem usar `localStorage` como fonte de verdade. A alternativa de armazenar tokens próprios de sessão persistentes exigiria rotação, revogação e expiração que não fazem parte deste escopo.

4. **Persistir e comparar credenciais com segurança.** Normalizar e-mail removendo espaços externos e convertendo-o para minúsculas, aplicar uma restrição única no valor normalizado e repetir a checagem por restrição do banco para lidar com cadastros concorrentes. Armazenar salt aleatório por conta e derivação da senha por PBKDF2-HMAC (biblioteca padrão), comparando os valores derivados com comparação de tempo constante. Nunca registrar a senha em state persistente nem em logs. Para login inválido, apresentar mensagem genérica; para cadastro duplicado, informar que o endereço já está em uso.

5. **Representar o cadastro e o login como formulários Reflex servidos pelo backend.** A raiz mostra login; “Cadastrar-se” abre `/cadastro`, com uma navegação clara de retorno. Os handlers limpam as entradas de senha e tratam estados de submissão/erro explicitamente. O layout responsivo compartilha a paleta preta/roxa entre login, cadastro e splash.

6. **Fazer a splash antes de navegar ao catálogo.** Depois de autenticar no servidor, marcar a sessão como autenticada e renderizar uma splash temporária; um temporizador breve dispara a navegação a `/catalogo`. A navegação não deve ocorrer antes da resposta de sucesso, e erro de validação ou autenticação não deve ativar a splash. A duração exata pode ser ajustada durante validação visual sem alterar o contrato de que a transição é breve.

7. **Manter o escopo de instalação e migração limitado ao esquema de usuário.** Inspecionar as dependências já instaladas antes de alterar `requirements.txt`; adicionar dependência somente se SQLModel/driver SQLite não estiver disponível. Criar e aplicar uma migração para a tabela de contas usando as ferramentas de banco Reflex. A tabela contém identificador, e-mail normalizado, salt e hash da senha; nenhum dado da busca Steam será migrado ou persistido.

## Risks / Trade-offs

- [Uma instalação SQLite local não atende múltiplos processos/instâncias em produção] → manter a solução adequada ao escopo atual e documentar que eventual escala horizontal exige banco compartilhado e estratégia de sessão em change separada.
- [O estado de autenticação pode ficar inconsistente se uma conta for removida do banco ou o processo reiniciar] → consultar novamente o identificador no banco ao carregar o catálogo e redirecionar se a conta não existir; aceitar nova autenticação quando a sessão Reflex for perdida.
- [Uma exceção na restrição única pode ocorrer em cadastro concorrente] → capturar somente a violação esperada de unicidade, converter em mensagem de endereço já utilizado e deixar falhas inesperadas do banco explícitas.
- [A raiz deixa de ser a busca Steam] → preservar integralmente seu handler/estado e validar que `/buscar` continue disponível anonimamente.
- [Ajustes no modelo podem deixar o esquema local fora de sincronia] → inspecionar a migração gerada e verificar inicialização/migração em banco de teste antes de aceitar a mudança.

## Migration Plan

1. Adicionar o modelo e o serviço de autenticação, configurar o SQLite do Reflex e gerar/revisar a migração da tabela de usuários.
2. Mover a página Steam para `/buscar`, criar `/`, `/cadastro` e `/catalogo`, aplicar proteção backend e compor a transição splash.
3. Aplicar a migração em banco limpo e validar cadastro, login, rejeições, persistência, rotas e a busca anônima; executar os testes existentes e compilação Reflex.
4. Rollback: restaurar a raiz como busca Steam e remover as rotas/handlers de autenticação; preservar a tabela enquanto houver contas que precisem ser mantidas ou removê-la somente se a reversão do banco for autorizada e segura.

