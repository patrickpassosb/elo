# Phase 4: User Experience (Commands & Interface)

## Branch
`feature/hackathon-phase4-ux`

## Objetivo
Melhorar comandos e interface do bot para o Hackathon.

## Tarefas
- [ ] Adicionar comando `/lei <tema>` em `src/telegram_bot/bot.py`:
  - Busca PLs sobre o tema usando `camara_api.py`
  - Explica o PL mais relevante
- [ ] Adicionar comando `/deputado <nome>` em `src/telegram_bot/bot.py`:
  - Busca info do deputado
  - Mostra votações recentes
- [ ] Adicionar comando `/diario <cidade> <assunto>`:
  - Busca no Querido Diário
  - Mostra resumo
- [ ] Melhorar mensagem de `/start` com exemplos de uso
- [ ] Adicionar tratamento de erros amigável

## Dependências
- **Phase 1** (APIs)
- **Phase 2** (função `explain_law`)

## Entregável
- 3 novos comandos funcionais
- Mensagens de erro amigáveis
- `/start` atualizado

## Exemplo de Fluxo
```
Usuário: /lei educação
Bot: 🔍 Encontrei 5 projetos sobre educação. Vou explicar o mais recente:

📜 PL 1234/2024 - Merenda Escolar
Essa lei quer garantir que todas as escolas públicas...

Você concorda? 👍 👎 🤷
```
