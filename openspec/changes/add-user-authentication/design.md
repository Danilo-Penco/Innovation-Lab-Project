# Design

## Context

Veja `proposal.md` para a motivação e `specs/user-auth/spec.md` para o contrato de comportamento. A arquitetura do projeto atribui autenticação, persistência e regras de negócio ao Xano; o frontend será HTML/CSS/JavaScript sem framework. A inspeção do workspace não encontrou endpoints, esquema de usuários ou interface implementados, portanto a integração parte de uma base ainda não materializada no repositório.

## Goals / Non-Goals

**Goals:**

- Usar a autenticação do Xano para cadastro, login e identidade das chamadas autenticadas.
- Fazer o papel efetivo da conta ser controlado pelo backend e aplicar a autorização nas operações protegidas.
- Tornar o provisionamento inicial de `admin` explícito e independente do cadastro público.

**Non-Goals:**

- Criar recuperação de senha, autenticação por provedores externos ou uma interface para administrar usuários e papéis.
- Definir neste change o fluxo completo de solicitação ou cadastro de lojas.
- Criar um serviço de autenticação próprio fora do Xano.

## Decisions

1. **Usar autenticação nativa do Xano.** Isso segue a arquitetura existente e evita implementar armazenamento de senha, emissão de credenciais e validação de sessão manualmente. Uma implementação customizada foi considerada, mas aumentaria a superfície de segurança sem benefício identificado. Durante a implementação, confirmar os recursos disponíveis no workspace Xano e não persistir nem retornar senhas em texto puro.

2. **Atribuir papéis exclusivamente no backend.** O cadastro público cria contas com papel `usuario`, ignorando qualquer valor de papel enviado pelo cliente. O papel `admin` é atribuído manualmente por operador autorizado no Xano; não há endpoint público de promoção ou seleção de papel. Uma interface para administração de papéis foi considerada, mas está fora do escopo.

3. **Aplicar autorização em cada operação no Xano.** Toda operação que exige login valida as credenciais no backend. A operação que aprova uma solicitação também verifica o papel atual da identidade autenticada e nega por padrão quando a identidade ou o papel não puderem ser validados. Ocultar botões no frontend pode melhorar a experiência, mas não concede nem substitui autorização.

4. **Usar as credenciais de sessão emitidas pelo Xano nas chamadas protegidas.** O frontend envia essas credenciais pelo mecanismo de autenticação suportado pelo Xano, nunca pela URL. A inspeção não revelou o domínio/origem de implantação do frontend nem a configuração de sessão do Xano; por isso, a estratégia segura de armazenamento e renovação no navegador precisa ser confirmada durante a implementação. Não armazenar tokens em `localStorage` como conveniência padrão.

## Risks / Trade-offs

- [A conta inicial não recebe o papel `admin` ou é promovida incorretamente] → documentar a promoção manual no Xano e validar com uma chamada positiva de admin e negativas de usuario e não autenticado antes da liberação.
- [Uma operação futura deixa de verificar autorização no backend] → proteger cada endpoint administrativo individualmente e incluir testes que chamem o backend diretamente, sem depender da interface.
- [O token de sessão é exposto ou permanece válido além do esperado] → usar o mecanismo de sessão do Xano, tráfego HTTPS e uma estratégia de armazenamento/expiração compatível com a implantação, a ser confirmada antes de integrar o frontend.
- [O esquema de autenticação do workspace Xano não oferece o comportamento esperado] → validar a configuração nativa e o formato de credenciais antes de fechar a integração; manter a autenticação dentro do Xano, conforme a arquitetura do projeto.

## Migration Plan

1. Configurar a autenticação e o papel de usuário no Xano, incluindo o cadastro público seguro e as operações de login.
2. Aplicar autenticação nas operações protegidas e autorização `admin` na operação de aprovação.
3. Validar os cenários de sucesso e negação diretamente no backend; provisionar manualmente a primeira conta administrativa.
4. Integrar os formulários e estados de sessão no frontend após confirmar domínio, transporte e ciclo de vida das credenciais.

Não há dados ou endpoints de autenticação existentes no repositório para migrar. Em caso de rollback, desabilitar a integração/rotas novas sem apagar contas criadas; reativar somente após corrigir e revalidar as permissões.

## Open Questions

- Qual é o domínio/origem de implantação do frontend e qual mecanismo de sessão do Xano permite armazenar e renovar credenciais sem expô-las a scripts do navegador? Resolver antes de implementar a integração frontend.