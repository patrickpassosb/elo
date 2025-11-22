# Phase 1: Data Integration (API Services)

## Branch
`feature/hackathon-phase1-data`

## Objetivo
Criar serviços para integrar APIs externas de dados legislativos e governamentais.

## Tarefas
- [ ] Criar `src/services/__init__.py`
- [ ] Criar `src/services/camara_api.py` com funções:
  - `get_proposicoes(tema: str)` - Busca PLs por tema
  - `get_deputado(id: int)` - Informações de um deputado
  - `get_votacoes(proposicao_id: int)` - Votações de um PL
- [ ] Criar `src/services/querido_diario_api.py` com funções:
  - `search_gazette(city: str, query: str)` - Busca no Diário Oficial
- [ ] Adicionar testes em `tests/test_camara_api.py`
- [ ] Adicionar testes em `tests/test_querido_diario_api.py`
- [ ] Atualizar `pyproject.toml` com dependências: `httpx`, `python-dateutil`

## Dependências
- Nenhuma (pode começar imediatamente)

## APIs de Referência
- Câmara: https://dadosabertos.camara.leg.br/swagger/api.html
- Querido Diário: https://queridodiario.ok.org.br/api/docs

## Entregável
- Funções que retornam dados das APIs em formato JSON/dict
- Testes unitários passando
- Documentação básica (docstrings)

## Exemplo de Uso Esperado
```python
from src.services.camara_api import get_proposicoes

pls = get_proposicoes(tema="educação")
# Retorna: [{"id": 123, "ementa": "...", "autor": "..."}]
```
