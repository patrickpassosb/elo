import os
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from dotenv import load_dotenv

load_dotenv()

# Store for session histories
store = {}

def get_session_history(session_id: str) -> BaseChatMessageHistory:
    if session_id not in store:
        store[session_id] = ChatMessageHistory()
    return store[session_id]

# Initialize LLM
llm = ChatOpenAI(model="gpt-4o", temperature=0.7)

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

def process_message(session_id: str, user_input: str):
    """
    Processes a message through the LangChain chain with memory.
    """
    response = with_message_history.invoke(
        {"input": user_input},
        config={"configurable": {"session_id": session_id}},
    )
    return response.content
