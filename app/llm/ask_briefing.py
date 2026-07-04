from dotenv import load_dotenv

from langgraph.prebuilt import create_react_agent
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from app.llm.llm_serve import get_langchain_client
from app.rag.vector_store import retrieve_relevant_context
from app.llm.token_tracker import tracker

load_dotenv()

# Max conversation history to send — prevents context window bloat
MAX_HISTORY_MESSAGES = 6  # 3 Q&A pairs


def ask_briefing(
    briefing: dict,
    topic: str,
    conversation_history: list[dict],
    new_question: str,
) -> str:

    client = get_langchain_client()

    # Define the tool, capturing `topic` in the closure
    @tool
    def search_knowledge_base(query: str) -> str:
        """Search the detailed articles underlying this briefing for specific facts and context."""
        return retrieve_relevant_context(topic=topic, query=query, top_k=4)

    system_prompt = f"""You are F.A.I.T's intelligence assistant for Finance, AI & Tech news.
Answer follow-up questions about: '{topic}'.

- Use your search tool to find specific details from articles.
- IMPORTANT: Use the native function calling API to invoke the tool. Do NOT output raw XML tags.
- If the tool returns nothing relevant, state that clearly.
- Keep answers analytical, brief, and data-driven."""

    # Build the LangGraph ReAct agent
    agent = create_react_agent(client, tools=[search_knowledge_base])

    # Convert conversation history — limit to last N messages for token efficiency
    recent_history = conversation_history[-MAX_HISTORY_MESSAGES:]
    messages = [SystemMessage(content=system_prompt)]
    for msg in recent_history:
        if msg["role"] == "user":
            messages.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "assistant":
            messages.append(AIMessage(content=msg["content"]))

    # Add new question
    messages.append(HumanMessage(content=new_question))

    # Invoke the agent
    response = agent.invoke({"messages": messages})

    # The final message from the agent is the last message in the state
    final_message = response["messages"][-1].content

    # Track token usage
    tracker.log_usage("ask_briefing", system_prompt + new_question, final_message)

    return final_message