# Phase 3: Engagement Features (Feedback & Notifications)

## Branch
`feature/hackathon-phase3-engagement`

## Objetivo
Adicionar funcionalidades de feedback e notificações (MVP/mockup).

## Tarefas
- [ ] Criar `src/services/subscription_service.py`:
  - `subscribe_topic(user_id: int, topic: str)` - Inscrever em tema
  - `get_subscriptions(user_id: int)` - Listar inscrições
- [ ] Criar `src/services/feedback_service.py`:
  - `save_feedback(user_id: int, bill_id: str, sentiment: str)` - Salvar opinião
  - `get_sentiment_summary(bill_id: str)` - Resumo de sentimentos
- [ ] Adicionar comando `/fiscalizar <tema>` em `src/telegram_bot/bot.py`
- [ ] Adicionar pergunta de feedback após explicar um PL
- [ ] Testes em `tests/test_subscription_service.py`

## Dependências
- **Phase 1** (precisa da API da Câmara para buscar PLs por tema)

## Entregável
- Sistema de inscrições funcionando (salvar em `storage.py`)
- Coleta de feedback (mockup - não precisa enviar para lugar nenhum)
- Comando `/fiscalizar` funcional

## Exemplo de Fluxo
```
Usuário: /fiscalizar educação
Bot: Ótimo! Vou te avisar quando houver votações sobre educação. 📚

[Depois de explicar um PL]
Bot: Você concorda com essa lei? 
👍 Concordo | 👎 Discordo | 🤷 Neutro
```
