import os
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory

from config import settings
from logging_config import logger
from storage import session_store
from ai.legislative_prompts import SIMPLIFY_LAW_PROMPT, SUMMARIZE_BILL_PROMPT, EXPLAIN_ARTICLE_PROMPT

# Store for session histories is now handled by SessionStore

def get_session_history(session_id: str) -> BaseChatMessageHistory:
    """Retrieve or create a ChatMessageHistory for a given session using SessionStore."""
    return session_store.get_history(session_id)

# Initialize LLM with settings
llm = ChatOpenAI(
    model=settings.llm_model,
    temperature=settings.llm_temperature,
    api_key=settings.openai_api_key
)

# System Prompt - "Neto Digital"
system_prompt = """
Você é o ELO, um "Neto Digital" muito paciente, acolhedor e brasileiro.
Sua missão é ajudar idosos e pessoas com dificuldade de leitura a entenderem documentos, leis e textos complexos.

Diretrizes de Personalidade:
- Fale de forma simples, clara e carinhosa, mas sem ser infantil.
- Use analogias do dia a dia para explicar termos difíceis.
- Evite "juridiquês" ou termos técnicos. Se precisar usar, explique o que significa logo em seguida.
- Seja breve. Textos muito longos cansam.
- Se o usuário mandar uma imagem de carta ou documento, explique o que é e o que ele precisa fazer (ex: "É só um aviso, não precisa pagar nada" ou "Vó, essa conta vence amanhã").
- Sempre termine perguntando se a pessoa entendeu ou se precisa de mais ajuda.

Lembre-se: Você é o elo entre a burocracia e o cidadão.
"""

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system_prompt),
        MessagesPlaceholder(variable_name="history"),
        ("human", "{input}"),
    ]
)

chain = prompt | llm

with_message_history = RunnableWithMessageHistory(
    chain,
    get_session_history,
    input_messages_key="input",
    history_messages_key="history",
)

async def process_message(session_id: str, user_input: str):
    """
    Processes a message through the LangChain chain with memory asynchronously.
    """
    logger.info(f"Processing message for session {session_id}")
    try:
        response = await with_message_history.ainvoke(
            {"input": user_input},
            config={"configurable": {"session_id": session_id}},
        )
        return response.content
    except Exception as e:
        logger.error(f"Error processing message for session {session_id}: {e}", exc_info=True)
        return "Desculpe, tive um problema para pensar na resposta. Pode tentar de novo?"

async def explain_law(law_text: str) -> str:
    """
    Simplifies legal text using the ELO "Neto Digital" persona.
    
    This function takes complex legal jargon and converts it into simple,
    accessible Portuguese that anyone can understand.
    
    Args:
        law_text (str): Raw legal text (article, law excerpt, bill text, etc.)
        
    Returns:
        str: Simplified explanation in plain Portuguese
        
    Example:
        >>> law = "Art. 1º Esta Lei estabelece normas gerais..."
        >>> explanation = await explain_law(law)
        >>> print(explanation)
        "Olha, essa lei cria regras para..."
    """
    logger.info("Simplifying legal text")
    try:
        # Format the prompt with the law text
        formatted_prompt = SIMPLIFY_LAW_PROMPT.format(law_text=law_text)
        
        # Use the LLM to generate the explanation
        response = await llm.ainvoke(formatted_prompt)
        
        return response.content
    except Exception as e:
        logger.error(f"Error explaining law: {e}", exc_info=True)
        return "Desculpe, tive dificuldade para simplificar esse texto. Pode tentar de novo ou me mandar em pedaços menores?"

async def summarize_bill(bill_text: str) -> str:
    """
    Summarizes a bill (PL) in simple, accessible language.
    
    Args:
        bill_text (str): Full or partial text of a bill/PL
        
    Returns:
        str: Summary with key points and practical impact
    """
    logger.info("Summarizing bill")
    try:
        formatted_prompt = SUMMARIZE_BILL_PROMPT.format(bill_text=bill_text)
        response = await llm.ainvoke(formatted_prompt)
        return response.content
    except Exception as e:
        logger.error(f"Error summarizing bill: {e}", exc_info=True)
        return "Desculpe, tive dificuldade para resumir esse projeto de lei. Pode tentar de novo?"

async def explain_article(article_text: str) -> str:
    """
    Explains a specific article from a law in simple terms.
    
    Args:
        article_text (str): Text of a specific article (e.g., "Art. 5º...")
        
    Returns:
        str: Simple explanation of what the article means
    """
    logger.info("Explaining article")
    try:
        formatted_prompt = EXPLAIN_ARTICLE_PROMPT.format(article_text=article_text)
        response = await llm.ainvoke(formatted_prompt)
        return response.content
    except Exception as e:
        logger.error(f"Error explaining article: {e}", exc_info=True)
        return "Desculpe, tive dificuldade para explicar esse artigo. Pode tentar de novo?"
