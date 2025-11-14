import os
from dotenv import load_dotenv
from supabase import create_client, Client
from nba_api.stats.endpoints import commonallplayers, commonplayerinfo # <-- Import new endpoint
import pandas as pd
import time

# --- 1. SETUP ---
print("Starting player backfill script (Full Roster + Position)...")
load_dotenv()
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")

if not url or not key:
    print("Error: Supabase credentials not found.")
    exit()

try:
    supabase: Client = create_client(url, key)
    print("Successfully connected to Supabase.")
except Exception as e:
    print(f"Error connecting to Supabase: {e}")
    exit()

headers = {
    'Host': 'stats.nba.com',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:72.0) Gecko/20100101 Firefox/72.0',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'en-US,en;q=0.5',
    'x-nba-stats-origin': 'stats',
    'x-nba-stats-token': 'true',
    'Connection': 'keep-alive',
    'Referer': 'https://stats.nba.com/',
}

# --- 2. FETCH ALL PLAYERS ---
print("Fetching all active NBA players from nba_api (CommonAllPlayers)...")
try:
    player_data = commonallplayers.CommonAllPlayers(
        is_only_current_season=1,
        headers=headers,
        timeout=30
    )
    player_df = player_data.common_all_players.get_data_frame()
    if player_df.empty:
        print("Could not fetch player list from API.")
        exit()
    print(f"Found {len(player_df)} active players.")
    
except Exception as e:
    print(f"Error fetching from nba_api: {e}")
    exit()
    
# --- 3. TRANSFORM DATA (with Position) ---
players_to_insert = []
print("Now fetching position for each player (this will take 5-10 minutes)...")

for index, player in player_df.iterrows():
    nba_api_id = player['PERSON_ID']
    full_name = player['DISPLAY_FIRST_LAST']
    team_name = player['TEAM_NAME'] or "N/A"
    position = "N/A" # Default
    
    try:
        # --- ⭐️ THIS IS THE FIX ⭐️ ---
        # Make a second API call to get detailed info for this player
        info = commonplayerinfo.CommonPlayerInfo(
            player_id=nba_api_id,
            headers=headers,
            timeout=10
        )
        info_df = info.common_player_info.get_data_frame()
        
        if not info_df.empty:
            # Get the position from the new data
            # The column is 'POSITION' (all caps)
            position = info_df.iloc[0]['POSITION'] or "N/A"
        
        print(f"  Processed {full_name} ({position})")
        
    except Exception as e:
        print(f"  Error fetching position for {full_name}: {e}. Setting to N/A.")
    
    players_to_insert.append({
        "nba_api_id": nba_api_id,
        "full_name": full_name,
        "team_name": team_name,
        "position": position,
        "headshot_url": f"https://cdn.nba.com/headshots/nba/latest/1040x760/{nba_api_id}.png"
    })
    
    # --- ⭐️ IMPORTANT: Add a delay to avoid API rate limiting ---
    time.sleep(0.5) # Half a second delay per player

# --- 4. UPSERT INTO DATABASE ---
if players_to_insert:
    print(f"\nUpserting {len(players_to_insert)} players into 'players' table...")
    try:
        # This will UPDATE all your existing players with the correct position
        response = supabase.table('players').upsert(
            players_to_insert, 
            on_conflict='nba_api_id'
        ).execute()
        
        if response.data:
            print(f"Successfully upserted {len(response.data)} players.")
        print("--- PLAYER BACKFILL COMPLETE ---")
    except Exception as e:
        print(f"Error upserting players: {e}")
else:
    print("No new players to insert.")