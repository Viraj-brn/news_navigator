import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

def get_supabase() -> Client:
    """Initializes and returns the Supabase client."""
    url: str = os.getenv("SUPABASE_URL")
    key: str = os.getenv("SUPABASE_KEY")
    
    if not url or not key:
        raise ValueError("Supabase URL and Key must be set in the .env file")
        
    return create_client(url, key)

# Create a singleton instance to use across your app
supabase = get_supabase()
