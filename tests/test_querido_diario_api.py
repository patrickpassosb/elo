"""
Tests for Querido Diário API client.
"""

import pytest
from src.services.querido_diario_api import (
    search_gazette,
    get_recent_gazettes,
    _get_territory_id
)
import httpx


@pytest.mark.asyncio
async def test_search_gazette():
    """Test searching gazettes for a specific city and query."""
    # Using São Paulo as it's likely to have data
    result = await search_gazette(
        city="São Paulo",
        query="educação",
        limit=2
    )
    
    assert isinstance(result, list)
    
    if len(result) > 0:
        entry = result[0]
        assert "date" in entry
        assert "city" in entry
        assert "territory_id" in entry
        assert "url" in entry


@pytest.mark.asyncio
async def test_get_recent_gazettes():
    """Test fetching recent gazettes from a city."""
    result = await get_recent_gazettes(
        city="São Paulo",
        days=30,
        limit=3
    )
    
    assert isinstance(result, list)
    
    if len(result) > 0:
        gaz = result[0]
        assert "date" in gaz
        assert "city" in gaz
        assert "territory_id" in gaz


@pytest.mark.asyncio
async def test_get_territory_id():
    """Test getting territory ID for a city."""
    async with httpx.AsyncClient() as client:
        # Test with a known city
        territory_id = await _get_territory_id("São Paulo", client)
        
        # São Paulo's IBGE code is 3550308
        if territory_id:
            assert isinstance(territory_id, str)
            assert len(territory_id) > 0


@pytest.mark.asyncio
async def test_search_gazette_invalid_city():
    """Test that searching for an invalid city returns empty list gracefully."""
    result = await search_gazette(
        city="CidadeInexistente123",
        query="test",
        limit=1
    )
    
    assert isinstance(result, list)
    assert len(result) == 0


@pytest.mark.asyncio
async def test_get_recent_gazettes_invalid_city():
    """Test that fetching gazettes for invalid city returns empty list gracefully."""
    result = await get_recent_gazettes(
        city="CidadeInexistente123",
        days=7,
        limit=1
    )
    
    assert isinstance(result, list)
    assert len(result) == 0
