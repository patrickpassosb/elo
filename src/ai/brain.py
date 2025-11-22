import os
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory

from config import settings
from logging_config import logger
from storage import session_store

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

# ---------------------------------------------------------------------------
# Legislative helper functions (Phase 4)
# ---------------------------------------------------------------------------

async def explain_law(law_text: str) -> str:
    """Explain a law text in simple, warm language using the LLM."""
    if not law_text:
        return "Não recebi nenhum texto de lei para explicar. Pode me mandar o artigo ou a lei que você quer entender?"
    try:
        response = await llm.ainvoke({"input": law_text})
        return getattr(response, "content", str(response))
    except Exception as e:
        logger.error(f"Error in explain_law: {e}", exc_info=True)
        return "Desculpe, tive um problema ao explicar a lei. Tente novamente mais tarde."

async def summarize_bill(bill_text: str) -> str:
    """Summarize a bill (PL) in a concise, user‑friendly format."""
    if not bill_text:
        return "Não recebi nenhum texto de projeto de lei para resumir."
    try:
        response = await llm.ainvoke({"input": bill_text})
        return getattr(response, "content", str(response))
    except Exception as e:
        logger.error(f"Error in summarize_bill: {e}", exc_info=True)
        return "Desculpe, tive um problema ao resumir o projeto de lei. Tente novamente mais tarde."

async def explain_article(article_text: str) -> str:
    """Explain a single article of a law in accessible language."""
    if not article_text:
        return "Não recebi nenhum artigo para explicar."
    try:
        response = await llm.ainvoke({"input": article_text})
        return getattr(response, "content", str(response))
    except Exception as e:
        logger.error(f"Error in explain_article: {e}", exc_info=True)
        return "Desculpe, tive um problema ao explicar o artigo. Tente novamente mais tarde."

