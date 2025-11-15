import os
from fastapi import FastAPI, HTTPException
from dotenv import load_dotenv
from supabase import create_client, Client
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
from typing import List
from pydantic import BaseModel

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

class CompareRequest(BaseModel):
    player_ids: List[str] 

# --- 3. API ENDPOINTS ---
@app.get("/")
def read_root():
    return {"message": "Sportfolio API is running"}

@app.get("/players")
def get_players():
    try:
        response = supabase.table('players').select(
            'id, full_name, team_name, position, headshot_url, nba_api_id'
        ).execute()
        return response.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/featured-players")
def get_featured_players():
    try:
        response = supabase.rpc('get_featured_players').execute()
        return response.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/player/{player_id}")
def get_player_info(player_id: str):
    try:
        response = supabase.table('players').select('*').eq('id', player_id).single().execute()
        return response.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/player/{player_id}/value_history")
def get_player_value_history(player_id: str):
    try:
        response = supabase.table('player_value_index').select('value_date, value_score').eq('player_id', player_id).order('value_date').execute()
        return response.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/player/{player_id}/stats")
def get_player_stats(player_id: str):
    try:
        response = supabase.table('daily_player_stats').select('*').eq('player_id', player_id).order('game_date', desc=True).limit(5).execute()
        return response.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/player/{player_id}/season_stats")
def get_player_season_stats(player_id: str):
    try:
        response = supabase.table('player_season_stats') \
            .select('*') \
            .eq('player_id', player_id) \
            .order('season', desc=True) \
            .limit(1) \
            .maybe_single() \
            .execute()
        return response.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/player/{player_id}/news")
def get_player_news(player_id: str):
    try:
        response = supabase.table('daily_player_sentiment').select('article_date, headline_text, sentiment_score').eq('player_id', player_id).order('article_date', desc=True).limit(5).execute()
        return response.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/market-movers")
def get_market_movers():
    try:
        response = supabase.rpc('get_market_movers').execute()
        all_movers = response.data
        all_movers.sort(key=lambda x: x['value_change'], reverse=True)
        risers = all_movers[:5]
        fallers = all_movers[-5:]
        fallers.reverse()
        return {"risers": risers, "fallers": fallers}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/players/compare")
def get_compare_data(request: CompareRequest):
    try:
        player_ids = request.player_ids
        
        info_res = supabase.table('players').select('*').in_('id', player_ids).execute()
        
        stats_res = supabase.table('player_season_stats') \
            .select('*').in_('player_id', player_ids) \
            .order('season', desc=True) \
            .execute()
            
        value_res = supabase.table('player_value_index') \
            .select('*') \
            .in_('player_id', player_ids).order('value_date').execute()

        player_data = {}
        for player in info_res.data:
            player_data[player['id']] = {
                "info": player,
                "season_stats": None, 
                "value_history": [] 
            }
        
        for stats in stats_res.data:
            player_id = stats['player_id']
            if player_id in player_data:
                if player_data[player_id]['season_stats'] is None:
                     player_data[player_id]['season_stats'] = stats
        
        for value in value_res.data:
            player_id = value['player_id']
            if player_id in player_data:
                player_data[player_id]['value_history'].append({
                    "value_date": value['value_date'],
                    "value_score": value['value_score']
                })
        
        return player_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- ⭐️ REMOVED /standings and /player/{id}/schedule ---