# Design

## Context

Veja [proposal.md](./proposal.md) para a motivação e [specs/steam-price-search/spec.md](./specs/steam-price-search/spec.md) para o contrato observável. A página atual em `Projeto/Projeto.py` é um protótipo Reflex com formulário de login. O projeto também usa Xano, mas o workspace Xano disponível informa `allow_push: false`, impedindo publicar e testar novas operações. A busca e o preço são públicos, somente de leitura e não precisam de dados persistidos.

## Goals / Non-Goals

**Goals:**

- Consultar busca e detalhes da Steam a partir do servidor da aplicação Reflex, sem dependência de CORS no navegador nem novas operações Xano.
- Manter a consulta anônima, de leitura, atualizada a cada solicitação e sem cache/histórico persistente.
- Distinguir jogos pagos com preço BRL, jogos gratuitos e preços regionais indisponíveis.
- Preservar autenticação e operações Xano para outras funcionalidades do produto.

**Non-Goals:**

- Alterar Xano, implantar endpoints ou mudar autenticação de outras áreas.
- Integrar lojas diferentes da Steam, comparar ofertas ou criar histórico/favoritos.
- Garantir disponibilidade ou atualização mais rápida que a resposta fornecida pela própria Steam.

## Decisions

1. **Fazer a chamada externa em handlers do servidor Reflex.** O estado e os eventos da tela chamam uma pequena integração HTTP executada pelo servidor Reflex. A chamada direta do navegador foi considerada, mas dependeria de CORS e exporia a aplicação ao formato da Steam. Xano continua sendo o backend das demais regras de negócio; esta busca é uma exceção limitada porque o workspace atual não permite publicar novos endpoints.

2. **Separar busca de candidatos da consulta por App ID escolhido.** A busca pública da Steam Store fornece nome, App ID e campos de preço opcionais para apresentar candidatos; após a escolha, consultar detalhes do App ID com `cc=br` e idioma português para obter a situação mais atual. Isso evita inferir o jogo correto pelo primeiro resultado e evita chamadas de detalhe para todos os candidatos.

3. **Interpretar explicitamente os estados de preço.** `is_free` identifica jogos gratuitos. Para jogo pago, só apresentar `price_overview.final` quando `price_overview.currency` indicar BRL; o valor é fornecido em centavos. Preço ou moeda ausentes significam indisponibilidade, nunca conversão automática nem preço zero.

4. **Manter dados transitórios no estado Reflex, sem persistência.** O termo, candidatos, App ID selecionado e resultado são usados apenas para a interação atual. Uma nova busca limpa resultado e seleção anteriores. Cada solicitação de preço chama novamente a Steam; não criar tabela, cache, cookies ou armazenamento do lado do cliente.

5. **Tratar as chamadas externas como falíveis.** Usar cliente HTTP assíncrono e timeout limitado em handlers assíncronos, validar a estrutura da resposta e lidar explicitamente com timeout, erro de rede, status HTTP inválido e JSON malformado. Mensagens amigáveis permitem tentar novamente; detalhes técnicos não devem ser convertidos em sucesso ou em preço antigo.

6. **Validar a entrada antes de consultar.** Remover espaços nas pontas, rejeitar termo vazio e impor tamanho máximo razoável antes de fazer uma solicitação externa. Os parâmetros devem ser enviados como query parameters codificados pelo cliente HTTP, não concatenados manualmente na URL.

## Risks / Trade-offs

- [A interface pública da Steam pode mudar, aplicar limitação de frequência ou ficar indisponível] → encapsular parsing e chamadas numa integração pequena, usar timeout, apresentar erro recuperável e testar respostas simuladas representativas.
- [Busca retorna jogos homônimos, conteúdo não-jogo ou sem preço] → apresentar nome e App ID para escolha e confirmar detalhes após a seleção; tratar preço ausente como indisponível.
- [Uma aplicação pública pode ser usada para gerar muitas chamadas externas] → limitar comprimento da consulta, evitar consultas redundantes durante o mesmo evento e não iniciar requisições ao digitar cada caractere.
- [A chamada direta do servidor Reflex diverge da arquitetura padrão Xano] → documentar e manter a exceção confinada à busca pública; reavaliar a integração se um workspace Xano gravável estiver disponível.

## Migration Plan

1. Adicionar a integração Steam no servidor Reflex e testes unitários de parsing, BRL, estados de gratuidade e falhas.
2. Substituir o protótipo de login na página inicial pela busca anônima, seleção do resultado e exibição de preço.
3. Atualizar a documentação do produto e validar compilação, testes e consultas reais de busca/detalhe sem autenticação nem persistência.
4. Para rollback, retirar os handlers e restaurar a tela anterior. Não há dados ou preços persistidos para migrar ou limpar.
