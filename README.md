# ComparaKeys

## 1. Apresentação

O ComparaKeys é um aplicativo web que compara o preço de jogos de PC em lojas digitais. O usuário pesquisa o nome de um jogo e vê, num só lugar, o valor na Steam e na GOG, em reais, com o menor preço destacado e um link direto para cada loja.

Problema que resolve: o mesmo jogo costuma ter preços diferentes em cada loja, e compará-los manualmente, um a um, é demorado e pouco prático.

Público-alvo: jogadores de PC que querem pagar menos e decidir a compra com mais informação.

Projeto acadêmico desenvolvido por Danilo Penco, Kauã Ornaghi e Luca Fusco.

## 2. Acesso ao aplicativo

O aplicativo roda localmente.

Requisitos: Python 3.11 ou superior e uma conta no Xano (plano gratuito) com a API de autenticação configurada.

    git clone https://github.com/Danilo-Penco/Innovation-Lab-Project
    cd Innovation-Lab-Project
    python -m venv .venv
    .venv\Scripts\activate
    pip install -r requirements.txt

Crie um arquivo .env na raiz com a URL da API do Xano:

    XANO_API_URL=https://[SUA-INSTANCIA].xano.io/api:[CODIGO-DO-GRUPO]

Inicie o aplicativo e acesse http://localhost:3000:

    python -m reflex run

O arquivo docs/xano-setup.md descreve as tabelas e os endpoints do Xano.

## 3. Perfis de usuários

- Visitante (sem login): vê a página inicial, pesquisa jogos e compara preços entre Steam e GOG.
- Usuário cadastrado: tudo o que o visitante faz, mais acesso ao catálogo de jogos.

## 4. Funcionalidades

- Página inicial pública com apresentação do projeto.
- Cadastro e login por nome, e-mail e senha, com os dados armazenados no Xano.
- Catálogo de jogos em ordem aleatória a cada carregamento, com um jogo em destaque e acesso direto à comparação.
- Busca de jogos pelo nome, com resultados que aparecem enquanto o usuário digita.
- Comparação de preços entre Steam e GOG em reais, com o menor preço em verde.
- Links diretos para a página do jogo em cada loja, abertos em nova aba.
- Mensagens específicas quando o jogo não é encontrado na GOG, quando há mais de uma correspondência ou quando não há preço em reais.
- Cabeçalho que muda conforme a sessão (Entrar ou Sair).
- Proteção do catálogo: sem login, o acesso redireciona para a tela de entrada.

## 5. Manual de utilização

### Jornada do visitante

1. Acesse a página inicial (/) e leia a apresentação do projeto.
2. Vá em /buscar e digite o nome de um jogo.
3. Escolha o jogo certo na lista de resultados.
4. Veja a comparação: preço na Steam, preço na GOG e o menor valor em verde.
5. Clique no nome do jogo para abrir a página dele na loja.

Resultado esperado: os preços aparecem em reais. Se a GOG não tiver o jogo, a tela mostra o preço da Steam com um aviso explicando o motivo.

### Jornada do usuário cadastrado

1. Clique em Cadastrar.
2. Informe nome, e-mail e uma senha com no mínimo 8 caracteres e pelo menos uma letra.
3. Após o cadastro, o sistema abre o catálogo.
4. Clique em qualquer jogo do catálogo para ver a comparação de preços.
5. Para sair, clique em Sair. Para voltar, use Entrar com o mesmo e-mail e a mesma senha.

Resultado esperado: o catálogo só abre com login. Uma senha sem letras, um e-mail já cadastrado ou credenciais erradas exibem mensagens próprias.

## 6. Exemplos de utilização

- Jogo em ambas as lojas: pesquise "The Witcher 3". Aparecem Steam e GOG, com o menor preço em verde.
- Jogo só na Steam: pesquise um título que a GOG não vende. A tela mostra o preço da Steam e avisa que não há correspondência na GOG.
- Senha sem letras: tente se cadastrar com 123456789. O sistema pede letras e números, por exemplo Senha12345.
- Acesso protegido: abra /catalogo sem estar logado e observe o redirecionamento para /entrar.

## 7. Limitações conhecidas

- O aplicativo roda localmente, a partir do repositório.
- A GOG é consultada pelo título do jogo. Quando o nome difere entre as lojas, o site mostra só a Steam, em vez de exibir uma correspondência incerta.
- Os jogos do catálogo são uma lista de exemplo e não representam promoções nem popularidade.
- Os preços são consultados no momento da busca e guardados em memória por até 5 minutos. Nenhum preço é gravado em banco de dados.
- Os dados dos usuários ficam no plano gratuito do Xano, que tem limite de requisições.
- A compra é feita na loja: o site leva o usuário até a página do jogo.
