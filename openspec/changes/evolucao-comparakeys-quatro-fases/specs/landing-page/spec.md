# Spec Delta

## Purpose

Esta capacidade apresenta o ComparaKeys a visitantes e oferece caminhos claros para entrar ou cadastrar-se.

## ADDED Requirements

### Requirement: Página inicial pública de apresentação
Ao abrir `/`, o sistema SHALL apresentar uma landing page pública, não um formulário de login. A seção superior SHALL ocupar a tela inteira, com fundo preto e duas metades: à esquerda, SHALL centralizar horizontal e verticalmente o texto “Compara Keys”; à direita, SHALL apresentar uma capa visual abstrata roxa e preta no estilo “noite urbana com neon”, sem arte protegida de jogos. Uma barra diagonal `/` SHALL separar as metades, com uma extremidade no canto inferior esquerdo e a outra no canto superior direito. Em viewport móvel, as metades SHALL empilhar-se. Uma capa de jogo real é opcional e, se utilizada, SHALL vir da lista fixa do catálogo, ter texto alternativo e fallback visual.

#### Scenario: Visitante abre a página inicial
- **WHEN** uma pessoa abre `/`
- **THEN** o sistema apresenta a landing page pública com a composição principal e sem exigir autenticação

#### Scenario: Identidade visual sem arte protegida
- **WHEN** a landing page apresenta sua composição principal
- **THEN** o sistema usa grafismos abstratos próprios e não exibe arte protegida de jogos

### Requirement: Barra de navegação fixa e acessível
A landing page SHALL apresentar uma barra `position: sticky` no topo da janela, com altura estável de aproximadamente 64 px e `z-index` acima do conteúdo. A barra SHALL permanecer no fluxo do documento, de modo que o hero comece abaixo dela, sem cobrir “Compara Keys” nem o conteúdo inicial; o hero SHALL ajustar sua altura para manter barra e hero na primeira tela sem quebrar a composição ou o corte diagonal. O fundo SHALL usar o token sólido `--ck-black` como fallback e, quando houver suporte, um preto quase opaco com `backdrop-filter` blur. Uma linha inferior de 1 px SHALL usar o token roxo discreto `--ck-purple-border`. O comportamento SHALL ser somente CSS, sem handlers Reflex ou chamadas ao servidor durante a rolagem.

À esquerda, a barra SHALL exibir somente o ícone de controle usado na marca das telas de autenticação, como link para `/` com o nome acessível “ComparaKeys — início”. À direita, SHALL mostrar “Entrar” para `/entrar` e “Cadastrar” para `/cadastro` sem sessão; com sessão autenticada, SHALL mostrar “Ir para o catálogo” para `/catalogo` e “Sair”. A barra SHALL existir somente na landing page; as outras páginas SHALL manter o cabeçalho atual. “Entrar” SHALL ter borda roxa e fundo transparente; “Cadastrar” SHALL ter fundo roxo sólido. A landing SHALL terminar após os dois cards institucionais e SHALL NOT conter barra, título, campo ou botão de busca. A barra SHALL ter foco visível, contraste WCAG AA e navegação por teclado. Em largura de 320 px, SHALL permanecer em uma linha, sem rolagem horizontal e sem sobrepor o conteúdo.

#### Scenario: Navegação da landing sem sessão
- **WHEN** uma pessoa sem sessão abre `/`
- **THEN** o ícone acessível leva a `/`, “Entrar” leva a `/entrar` e “Cadastrar” leva a `/cadastro`

#### Scenario: Navegação da landing com sessão
- **WHEN** uma pessoa autenticada abre `/`
- **THEN** a barra mostra “Ir para o catálogo” e “Sair” em vez das ações de visitante

#### Scenario: Barra da landing em 320 px
- **WHEN** uma pessoa abre `/` em viewport de 320 px
- **THEN** a barra permanece em uma linha, não cria rolagem horizontal nem encobre o conteúdo do hero

#### Scenario: Barra fixa durante a rolagem
- **WHEN** uma pessoa rola a landing page
- **THEN** a barra permanece no topo da janela por CSS, sem eventos de rolagem Reflex ou chamadas ao servidor

### Requirement: Apresentação institucional e chamadas de ação
A landing page SHALL apresentar abaixo da seção principal uma linha horizontal preta fina e dois quadrados pretos lado a lado, com borda roxa sutil e os títulos EXATOS “Quem somos” e “Objetivo do site e por que usar”. O primeiro SHALL descrever o projeto acadêmico do grupo e seu público de jogadores sem inventar nomes, números ou depoimentos. O segundo SHALL explicar que o site compara o preço do mesmo jogo em várias lojas, destaca o menor preço e oferece links às lojas, sem realizar compras. As ações de autenticação SHALL permanecer somente na barra superior. Depois dos cards, a landing SHALL terminar sem outra seção. Em viewport móvel, os quadrados SHALL ficar um abaixo do outro.

#### Scenario: Conteúdo institucional
- **WHEN** uma pessoa percorre a landing page até os cards institucionais
- **THEN** encontra os dois títulos e descrições sem dados, nomes ou depoimentos inventados

#### Scenario: Ações para visitante
- **WHEN** uma pessoa sem sessão vê as chamadas de ação
- **THEN** “Entrar” abre `/entrar` e “Cadastrar” abre `/cadastro`

#### Scenario: Ações para pessoa autenticada
- **WHEN** uma pessoa autenticada vê as chamadas de ação
- **THEN** a ação de autenticação é substituída por “Ir para o catálogo”, que abre `/catalogo`

### Requirement: Layout responsivo e acessível da landing page
A landing page SHALL permanecer utilizável de 320 px a larguras desktop, sem rolagem horizontal. Em viewports estreitos, as metades da seção principal SHALL empilhar-se e os cards SHALL aparecer um abaixo do outro. O conteúdo SHALL atender contraste WCAG AA, controles SHALL ter nomes acessíveis e foco de teclado visível, e a página SHALL respeitar `prefers-reduced-motion`.

#### Scenario: Landing page em viewport estreito
- **WHEN** uma pessoa abre `/` em viewport de 320 px ou mais estreito que o breakpoint desktop
- **THEN** as metades e os cards empilham-se sem corte, sobreposição ou rolagem horizontal

#### Scenario: Teclado, contraste e movimento reduzido
- **WHEN** uma pessoa navega pela landing page com teclado ou dispositivo configurado para movimento reduzido
- **THEN** os controles têm foco visível, textos e controles mantêm contraste AA e animações decorativas são reduzidas sem ocultar conteúdo
