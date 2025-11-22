"""
Câmara dos Deputados API Client.

This module provides functions to interact with the Brazilian Chamber of Deputies Open Data API.
API Documentation: https://dadosabertos.camara.leg.br/swagger/api.html
"""

import httpx
from typing import List, Dict, Optional
from src.logging_config import logger


BASE_URL = "https://dadosabertos.camara.leg.br/api/v2"
TIMEOUT = 30.0


async def get_proposicoes(tema: str, limit: int = 5) -> List[Dict]:
    """
    Search for legislative proposals (PLs) by topic.
    
    Args:
        tema: Topic to search for (e.g., "educação", "saúde")
        limit: Maximum number of results to return
        
    Returns:
        List of proposals with id, ementa (summary), autor (author), and other metadata
        
    Example:
        >>> pls = await get_proposicoes(tema="educação")
        >>> print(pls[0]["ementa"])
    """
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            params = {
                "keywords": tema,
                "ordem": "DESC",
                "ordenarPor": "id",
                "itens": limit
            }
            
            response = await client.get(f"{BASE_URL}/proposicoes", params=params)
            response.raise_for_status()
            
            data = response.json()
            proposicoes = data.get("dados", [])
            
            # Simplify the response
            result = []
            for prop in proposicoes:
                result.append({
                    "id": prop.get("id"),
                    "tipo": prop.get("siglaTipo"),
                    "numero": prop.get("numero"),
                    "ano": prop.get("ano"),
                    "ementa": prop.get("ementa"),
                    "autor": prop.get("autor", {}).get("nome") if isinstance(prop.get("autor"), dict) else None,
                    "url": prop.get("urlInteiroTeor")
                })
            
            logger.info(f"Found {len(result)} propositions for topic '{tema}'")
            return result
            
    except httpx.HTTPError as e:
        logger.error(f"HTTP error fetching propositions: {e}")
        return []
    except Exception as e:
        logger.error(f"Error fetching propositions: {e}", exc_info=True)
        return []


async def get_deputado(deputado_id: int) -> Optional[Dict]:
    """
    Get information about a specific deputy.
    
    Args:
        deputado_id: The deputy's ID
        
    Returns:
        Dictionary with deputy information (name, party, state, photo, etc.)
        
    Example:
        >>> dep = await get_deputado(178957)
        >>> print(f"{dep['nome']} - {dep['partido']}/{dep['estado']}")
    """
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.get(f"{BASE_URL}/deputados/{deputado_id}")
            response.raise_for_status()
            
            data = response.json()
            deputado = data.get("dados", {})
            
            result = {
                "id": deputado.get("id"),
                "nome": deputado.get("nomeCivil"),
                "nome_parlamentar": deputado.get("ultimoStatus", {}).get("nome"),
                "partido": deputado.get("ultimoStatus", {}).get("siglaPartido"),
                "estado": deputado.get("ultimoStatus", {}).get("siglaUf"),
                "foto": deputado.get("ultimoStatus", {}).get("urlFoto"),
                "email": deputado.get("ultimoStatus", {}).get("email"),
                "gabinete": deputado.get("ultimoStatus", {}).get("gabinete", {})
            }
            
            logger.info(f"Fetched deputy info: {result['nome_parlamentar']}")
            return result
            
    except httpx.HTTPError as e:
        logger.error(f"HTTP error fetching deputy {deputado_id}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error fetching deputy {deputado_id}: {e}", exc_info=True)
        return None


async def get_votacoes(proposicao_id: int) -> List[Dict]:
    """
    Get voting records for a specific proposal.
    
    Args:
        proposicao_id: The proposal's ID
        
    Returns:
        List of voting records with date, result, and vote counts
        
    Example:
        >>> votacoes = await get_votacoes(2338023)
        >>> for v in votacoes:
        ...     print(f"{v['data']}: {v['aprovacao']}")
    """
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.get(f"{BASE_URL}/proposicoes/{proposicao_id}/votacoes")
            response.raise_for_status()
            
            data = response.json()
            votacoes = data.get("dados", [])
            
            result = []
            for vot in votacoes:
                result.append({
                    "id": vot.get("id"),
                    "data": vot.get("dataHoraRegistro"),
                    "descricao": vot.get("descricao"),
                    "aprovacao": vot.get("aprovacao"),
                    "votos_sim": vot.get("placarSim"),
                    "votos_nao": vot.get("placarNao"),
                    "votos_outros": vot.get("placarOutros")
                })
            
            logger.info(f"Found {len(result)} voting records for proposal {proposicao_id}")
            return result
            
    except httpx.HTTPError as e:
        logger.error(f"HTTP error fetching votes for proposal {proposicao_id}: {e}")
        return []
    except Exception as e:
        logger.error(f"Error fetching votes for proposal {proposicao_id}: {e}", exc_info=True)
        return []


async def search_deputados(nome: str, limit: int = 5) -> List[Dict]:
    """
    Search for deputies by name.
    
    Args:
        nome: Name to search for
        limit: Maximum number of results
        
    Returns:
        List of deputies matching the search
    """
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            params = {
                "nome": nome,
                "ordem": "ASC",
                "ordenarPor": "nome",
                "itens": limit
            }
            
            response = await client.get(f"{BASE_URL}/deputados", params=params)
            response.raise_for_status()
            
            data = response.json()
            deputados = data.get("dados", [])
            
            result = []
            for dep in deputados:
                result.append({
                    "id": dep.get("id"),
                    "nome": dep.get("nome"),
                    "partido": dep.get("siglaPartido"),
                    "estado": dep.get("siglaUf"),
                    "foto": dep.get("urlFoto"),
                    "email": dep.get("email")
                })
            
            logger.info(f"Found {len(result)} deputies matching '{nome}'")
            return result
            
    except httpx.HTTPError as e:
        logger.error(f"HTTP error searching deputies: {e}")
        return []
    except Exception as e:
        logger.error(f"Error searching deputies: {e}", exc_info=True)
        return []
