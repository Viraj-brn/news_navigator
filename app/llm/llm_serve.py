from groq import Groq
from dotenv import load_dotenv
import os

load_dotenv()

def get_client():
    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise ValueError("GROQ_API_KEY not set")

    return Groq(api_key=api_key)