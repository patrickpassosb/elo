"""
Tests for Câmara dos Deputados API client.
"""

import pytest
from src.services.camara_api import (
    get_proposicoes,
    get_deputado,
    get_votacoes,
    search_deputados
)


@pytest.mark.asyncio
async def test_get_proposicoes():
    """Test fetching proposals by topic."""
    result = await get_proposicoes(tema="educação", limit=3)
    
    assert isinstance(result, list)
    
    if len(result) > 0:
        prop = result[0]
        assert "id" in prop
        assert "ementa" in prop
        assert "tipo" in prop
        assert "numero" in prop
        assert "ano" in prop


@pytest.mark.asyncio
async def test_get_deputado():
    """Test fetching deputy information."""
    # Using a known deputy ID (this may need to be updated)
    result = await get_deputado(deputado_id=178957)
    
    if result:
        assert "id" in result
        assert "nome" in result
        assert "partido" in result
        assert "estado" in result


@pytest.mark.asyncio
async def test_get_votacoes():
    """Test fetching voting records for a proposal."""
    # First get a proposal
    proposicoes = await get_proposicoes(tema="educação", limit=1)
    
    if len(proposicoes) > 0:
        prop_id = proposicoes[0]["id"]
        result = await get_votacoes(proposicao_id=prop_id)
        
        assert isinstance(result, list)
        # Note: Not all proposals have voting records


@pytest.mark.asyncio
async def test_search_deputados():
    """Test searching for deputies by name."""
    result = await search_deputados(nome="Silva", limit=3)
    
    assert isinstance(result, list)
    
    if len(result) > 0:
        dep = result[0]
        assert "id" in dep
        assert "nome" in dep
        assert "partido" in dep


@pytest.mark.asyncio
async def test_get_proposicoes_empty_result():
    """Test that searching for a very specific/unlikely term returns empty list gracefully."""
    result = await get_proposicoes(tema="xyzabc123unlikely", limit=1)
    
    assert isinstance(result, list)
    assert len(result) == 0
