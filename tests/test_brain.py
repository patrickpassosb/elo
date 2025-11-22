import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from src.ai.brain import process_message, explain_law, summarize_bill, explain_article

@pytest.mark.asyncio
async def test_process_message_success():
    with patch("src.ai.brain.with_message_history") as mock_chain:
        # Mock the ainvoke method to be an AsyncMock
        mock_chain.ainvoke = AsyncMock()
        mock_response = MagicMock()
        mock_response.content = "Hello human"
        mock_chain.ainvoke.return_value = mock_response
        
        response = await process_message("session1", "Hello")
        
        assert response == "Hello human"
        mock_chain.ainvoke.assert_called_once()

@pytest.mark.asyncio
async def test_process_message_failure():
    with patch("src.ai.brain.with_message_history") as mock_chain:
        mock_chain.ainvoke = AsyncMock()
        mock_chain.ainvoke.side_effect = Exception("AI Error")
        
        response = await process_message("session1", "Hello")
        
        assert "Desculpe" in response

# Tests for Legislative Functions

@pytest.mark.asyncio
async def test_explain_law_simple():
    """Test explain_law with a simple legal article."""
    with patch("src.ai.brain.llm") as mock_llm:
        mock_llm.ainvoke = AsyncMock()
        mock_response = MagicMock()
        mock_response.content = "Olha, essa lei cria regras para proteger suas informações pessoais na internet."
        mock_llm.ainvoke.return_value = mock_response
        
        law_text = "Art. 1º Esta Lei estabelece normas gerais sobre proteção de dados pessoais."
        result = await explain_law(law_text)
        
        # Verify the response is simplified
        assert "Olha" in result or "olha" in result.lower()
        assert len(result) > 0
        mock_llm.ainvoke.assert_called_once()

@pytest.mark.asyncio
async def test_explain_law_complex():
    """Test explain_law with complex legal text (PL 2338/2023 excerpt)."""
    with patch("src.ai.brain.llm") as mock_llm:
        mock_llm.ainvoke = AsyncMock()
        mock_response = MagicMock()
        mock_response.content = "Veja só, essa lei quer criar regras para que as empresas de internet sejam mais responsáveis pelo que as pessoas postam."
        mock_llm.ainvoke.return_value = mock_response
        
        complex_law = """
        Art. 1º Esta Lei estabelece normas sobre a responsabilidade civil de provedores 
        de aplicações de internet por danos decorrentes de conteúdo gerado por terceiros.
        """
        result = await explain_law(complex_law)
        
        # Check that technical terms are simplified
        assert "responsabilidade civil" not in result or "responsáveis" in result.lower()
        assert len(result) > 0

@pytest.mark.asyncio
async def test_explain_law_tone():
    """Test that explain_law uses accessible, warm tone."""
    with patch("src.ai.brain.llm") as mock_llm:
        mock_llm.ainvoke = AsyncMock()
        mock_response = MagicMock()
        # Simulate a response with the "Neto Digital" tone
        mock_response.content = "Olha, vou te explicar de um jeito simples: essa lei diz que você tem direito a saber como suas informações são usadas. 📝"
        mock_llm.ainvoke.return_value = mock_response
        
        law_text = "Art. 5º O titular dos dados pessoais tem direito à informação clara sobre o tratamento."
        result = await explain_law(law_text)
        
        # Check for warm, accessible language markers
        warm_markers = ["olha", "veja", "você", "sua", "seu"]
        assert any(marker in result.lower() for marker in warm_markers)

@pytest.mark.asyncio
async def test_explain_law_empty():
    """Test explain_law with empty input."""
    with patch("src.ai.brain.llm") as mock_llm:
        mock_llm.ainvoke = AsyncMock()
        mock_response = MagicMock()
        mock_response.content = "Não recebi nenhum texto de lei para explicar. Pode me mandar o artigo ou a lei que você quer entender?"
        mock_llm.ainvoke.return_value = mock_response
        
        result = await explain_law("")
        assert len(result) > 0

@pytest.mark.asyncio
async def test_explain_law_error_handling():
    """Test explain_law handles errors gracefully."""
    with patch("src.ai.brain.llm") as mock_llm:
        mock_llm.ainvoke = AsyncMock()
        mock_llm.ainvoke.side_effect = Exception("API Error")
        
        law_text = "Art. 1º Test"
        result = await explain_law(law_text)
        
        # Should return a friendly error message
        assert "Desculpe" in result or "desculpe" in result.lower()

@pytest.mark.asyncio
async def test_summarize_bill():
    """Test summarize_bill function."""
    with patch("src.ai.brain.llm") as mock_llm:
        mock_llm.ainvoke = AsyncMock()
        mock_response = MagicMock()
        mock_response.content = "📌 O que esse PL quer fazer? Criar regras para proteger dados pessoais.\n💡 Como isso me afeta? Suas informações ficam mais seguras."
        mock_llm.ainvoke.return_value = mock_response
        
        bill_text = "PL 2338/2023 - Estabelece normas sobre proteção de dados..."
        result = await summarize_bill(bill_text)
        
        assert len(result) > 0
        mock_llm.ainvoke.assert_called_once()

@pytest.mark.asyncio
async def test_explain_article():
    """Test explain_article function."""
    with patch("src.ai.brain.llm") as mock_llm:
        mock_llm.ainvoke = AsyncMock()
        mock_response = MagicMock()
        mock_response.content = "Esse artigo fala sobre o seu direito de saber como suas informações são usadas. Entendeu ou quer que eu explique melhor?"
        mock_llm.ainvoke.return_value = mock_response
        
        article_text = "Art. 5º O titular dos dados tem direito à informação."
        result = await explain_article(article_text)
        
        assert "artigo" in result.lower() or "fala sobre" in result.lower()
        assert len(result) > 0

