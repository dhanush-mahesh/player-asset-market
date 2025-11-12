import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

# Supabase URL and key
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")

# create supabase client
supabase: Client = create_client(url, key)

print("Connecting to Supabase...")

try:
    # test new player
    print("Inserting test player...")
    data, count = supabase.table('players').insert({
        "full_name": "Test Player", 
        "team_name": "TEST", 
        "position": "G"
    }).execute()

    print("Success! Data inserted:")
    print(data)

except Exception as e:
    print(f"Error connecting or inserting data: {e}")