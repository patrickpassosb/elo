# Phase 2: AI Refinement (Legislative Specialization)

## Branch
`feature/hackathon-phase2-ai`

## Objetivo
Ajustar o prompt do ELO para explicar leis e PLs de forma simples (como um "Neto Digital").

## Tarefas
- [ ] Modificar `src/ai/brain.py`:
  - Adicionar função `explain_law(law_text: str) -> str`
  - Criar prompt especializado em simplificar "burocratês"
- [ ] Criar `src/ai/legislative_prompts.py` com templates:
  - `SIMPLIFY_LAW_PROMPT`
  - `SUMMARIZE_BILL_PROMPT`
- [ ] Adicionar testes em `tests/test_brain.py`:
  - Testar simplificação de um PL real (ex: PL 2338/2023)
- [ ] Atualizar `src/config.py` se necessário (novos parâmetros)

## Dependências
- Nenhuma (trabalha em paralelo com Phase 1)

## Entregável
- Função `explain_law()` funcional
- Prompt otimizado para legislação
- Testes passando

## Exemplo de Uso Esperado
```python
from src.ai.brain import explain_law

texto_pl = "Art. 1º Esta Lei estabelece normas gerais..."
explicacao = explain_law(texto_pl)
# Retorna: "Essa lei cria regras para..."
```

## Referência de Tom
- **Antes:** "O artigo 5º da Constituição Federal estabelece..."
- **Depois:** "Olha, essa parte da lei diz que você tem direito a..."
