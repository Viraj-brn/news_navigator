from groq import Groq
from dotenv import load_dotenv
import os

load_dotenv()

def get_client():
    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise ValueError("GROQ_API_KEY not set")

    return Groq(api_key=api_key)

def get_langchain_client(model_name="llama-3.3-70b-versatile", temperature=0.2):
    from langchain_groq import ChatGroq
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY not set")
    return ChatGroq(groq_api_key=api_key, model_name=model_name, temperature=temperature)