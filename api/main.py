import os
from fastapi import FastAPI, HTTPException
from dotenv import load_dotenv
from supabase import create_client, Client
from fastapi.middleware.cors import CORSMiddleware

# --- 1. SETUP & CONFIG ---
load_dotenv()
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)
app = FastAPI()

# --- 2. CORS MIDDLEWARE ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 3. API ENDPOINTS ---
@app.get("/")
def read_root():
    return {"message": "Player Asset Market API is running"}

# GET /players
@app.get("/players")
def get_players():
    try:
        # --- ⭐️ UPDATED: Added 'headshot_url' ---
        response = supabase.table('players').select(
            'id, full_name, team_name, position, headshot_url'
        ).execute()
        return response.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# GET /featured-players
@app.get("/featured-players")
def get_featured_players():
    try:
        # --- ⭐️ UPDATED: Changed 'position' to '"position"' and added 'headshot_url' ---
        response = supabase.rpc('get_featured_players').select(
            'player_id, full_name, team_name, "position", latest_value, headshot_url'
        ).execute()
        return response.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# GET /player/<player_id>
@app.get("/player/{player_id}")
def get_player_info(player_id: str):
    try:
        # --- ⭐️ UPDATED: Added 'headshot_url' ---
        response = supabase.table('players').select('*').eq('id', player_id).single().execute()
        return response.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# GET /player/<player_id>/value_history
@app.get("/player/{player_id}/value_history")
def get_player_value_history(player_id: str):
    try:
        response = supabase.table('player_value_index').select('value_date, value_score').eq('player_id', player_id).order('value_date').execute()
        return response.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# GET /player/<player_id>/stats
@app.get("/player/{player_id}/stats")
def get_player_stats(player_id: str):
    try:
        response = supabase.table('daily_player_stats').select('*').eq('player_id', player_id).order('game_date', desc=True).limit(5).execute()
        return response.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# GET /player/<player_id>/news
@app.get("/player/{player_id}/news")
def get_player_news(player_id: str):
    try:
        response = supabase.table('daily_player_sentiment').select('article_date, headline_text, sentiment_score').eq('player_id', player_id).order('article_date', desc=True).limit(5).execute()
        return response.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# GET /market-movers
@app.get("/market-movers")
def get_market_movers():
    try:
        # --- ⭐️ UPDATED: Added 'headshot_url' to the function call ---
        response = supabase.rpc('get_market_movers').execute()
        all_movers = response.data
        all_movers.sort(key=lambda x: x['value_change'], reverse=True)
        risers = all_movers[:5]
        fallers = all_movers[-5:]
        fallers.reverse()
        return {"risers": risers, "fallers": fallers}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))