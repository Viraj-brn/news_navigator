from dotenv import load_dotenv

from langgraph.prebuilt import create_react_agent
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from app.llm.llm_serve import get_langchain_client
from app.rag.vector_store import retrieve_relevant_context

load_dotenv()

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
        
    system_prompt = f"""You are an AI intelligence assistant for Economic Times.
Your job is to answer the user's follow-up questions about the topic: '{topic}'.

- You must use your provided search tool to find specific details from the articles if you don't already know the answer.
- IMPORTANT: Use the native function calling API to invoke the tool. Do NOT output raw `<function>` XML tags.
- If the tool doesn't return relevant information, state that you don't have enough information.
- Keep the answer analytical, brief, and to the point.
"""

    # Build the LangGraph ReAct agent
    agent = create_react_agent(client, tools=[search_knowledge_base])
    
    # Convert conversation history
    messages = [SystemMessage(content=system_prompt)]
    for msg in conversation_history:
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
    return final_message