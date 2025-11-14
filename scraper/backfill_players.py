import os
from dotenv import load_dotenv
from supabase import create_client, Client
from nba_api.stats.endpoints import commonallplayers, playerdashboardbyyearoveryear, commonplayerinfo
import pandas as pd
import time
import requests

# --- 1. SETUP ---
print("Starting MASTER player backfill script (Roster + Season Stats)...")
print("This will run VERY SLOWLY (approx 1 hour) to avoid rate limits.")
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

# --- 2. FETCH ALL PLAYERS (Fast) ---
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
    print(f"Found {len(player_df)} total active players.")
    
except Exception as e:
    print(f"Error fetching from nba_api: {e}")
    exit()
    
# --- 3. FIND OUT WHO IS LEFT TO PROCESS ---
try:
    print("Fetching players who already have season stats...")
    
    # --- ⭐️ THIS IS THE NEW LOGIC ⭐️ ---
    # 1. Get all players from our 'players' table
    response = supabase.table('players').select('id, nba_api_id').execute()
    if not response.data:
        print("No players found in your 'players' table. Run ./run_all.sh first.")
        exit()
    player_map_supabase = {p['id']: p['nba_api_id'] for p in response.data}
    
    # 2. Get all stats from 'player_season_stats' table
    response = supabase.table('player_season_stats').select('player_id').execute()
    
    processed_player_ids_supabase = set()
    if response.data:
        processed_player_ids_supabase = {s['player_id'] for s in response.data}
    
    # 3. Convert Supabase UUIDs back to NBA API IDs
    processed_player_nba_ids = {player_map_supabase[uuid] for uuid in processed_player_ids_supabase if uuid in player_map_supabase}
    
    print(f"Found {len(processed_player_nba_ids)} players who are already complete.")
    
    # 4. Filter the main DataFrame to only include players we haven't processed
    original_count = len(player_df)
    player_df = player_df[~player_df['PERSON_ID'].isin(processed_player_nba_ids)]
    print(f"Remaining players to process: {len(player_df)} (out of {original_count})")
    
    if player_df.empty:
        print("All players are already processed. Exiting.")
        exit()
        
except Exception as e:
    print(f"Error checking for processed players: {e}")
    exit()
    
# --- 4. TRANSFORM DATA (Slow, in Chunks) ---
# (This section is identical to the previous file)
players_to_insert = []
season_stats_to_insert = []
chunk_size = 100 

print("Now fetching position AND season stats for remaining players...")

for start_index in range(0, len(player_df), chunk_size):
    end_index = start_index + chunk_size
    print(f"\n--- PROCESSING CHUNK: {start_index+1} to {min(end_index, len(player_df))} of remaining players ---")
    
    player_chunk = player_df.iloc[start_index:end_index]
    
    chunk_players_list = []
    chunk_season_stats_list = []

    for index, player in player_chunk.iterrows():
        nba_api_id = player['PERSON_ID']
        full_name = player['DISPLAY_FIRST_LAST']
        team_name = player['TEAM_NAME'] or "N/A"
        position = "N/A"
        
        retries = 3
        while retries > 0:
            try:
                info = commonplayerinfo.CommonPlayerInfo(player_id=nba_api_id, headers=headers, timeout=30)
                info_df = info.common_player_info.get_data_frame()
                if not info_df.empty:
                    position = info_df.iloc[0]['POSITION'] or "N/A"
                
                time.sleep(2) 
                
                seas_stats = playerdashboardbyyearoveryear.PlayerDashboardByYearOverYear(
                    player_id=nba_api_id, season="2025-26", per_mode_detailed="PerGame", headers=headers, timeout=30
                )
                seas_df = seas_stats.overall_player_dashboard.get_data_frame()
                
                print(f"  ({index+1}/{len(player_df)}) Processed {full_name} ({position})")
                
                if not seas_df.empty:
                    latest_seas = seas_df.iloc[0]
                    season_obj = {
                        "nba_api_id_temp": nba_api_id,
                        "season": latest_seas['GROUP_VALUE'],
                        "games_played": int(latest_seas['GP'] or 0),
                        "minutes_avg": float(latest_seas['MIN'] or 0),
                        "points_avg": float(latest_seas['PTS'] or 0),
                        "rebounds_avg": float(latest_seas['REB'] or 0),
                        "assists_avg": float(latest_seas['AST'] or 0),
                        "steals_avg": float(latest_seas['STL'] or 0),
                        "blocks_avg": float(latest_seas['BLK'] or 0),
                        "turnovers_avg": float(latest_seas['TOV'] or 0)
                    }
                    chunk_season_stats_list.append(season_obj)
                
                break 
                
            except requests.exceptions.ReadTimeout as e:
                retries -= 1
                if retries > 0:
                    print(f"    !!! Read Timeout for {full_name}. Retries left: {retries}. Cooling down for 60s...")
                    time.sleep(60)
                else:
                    print(f"    !!! FAILED to process {full_name} after 3 retries. Skipping.")
            except Exception as e:
                print(f"    Error processing {full_name}: {e}")
                break
        
        chunk_players_list.append({
            "nba_api_id": nba_api_id,
            "full_name": full_name,
            "team_name": team_name,
            "position": position,
            "headshot_url": f"https://cdn.nba.com/headshots/nba/latest/1040x760/{nba_api_id}.png"
        })
        
        time.sleep(4)
    
    # --- 5. UPSERT CHUNK DATA ---
    print(f"\n--- UPSERTING DATA FOR CHUNK {start_index+1} ---")
    if chunk_players_list:
        try:
            player_response = supabase.table('players').upsert(chunk_players_list, on_conflict='nba_api_id').execute()
            print(f"Successfully upserted {len(player_response.data)} player records.")
            
            if player_response.data and chunk_season_stats_list:
                # We need to get the *full* map, not just the chunk map
                full_player_map_resp = supabase.table('players').select('id, nba_api_id').execute()
                player_map = {p['nba_api_id']: p['id'] for p in full_player_map_resp.data}

                final_season_stats_to_insert = []
                for stat_line in chunk_season_stats_list:
                    nba_api_id = stat_line.pop('nba_api_id_temp')
                    player_id = player_map.get(nba_api_id)
                    if player_id:
                        stat_line['player_id'] = player_id
                        final_season_stats_to_insert.append(stat_line)
                
                if final_season_stats_to_insert:
                    stats_response = supabase.table('player_season_stats').upsert(
                        final_season_stats_to_insert, on_conflict='player_id, season'
                    ).execute()
                    print(f"Successfully upserted {len(stats_response.data)} season stat records.")
        
        except Exception as e:
            print(f"!!! Error upserting chunk data: {e}. Skipping to next chunk.")
            
    if end_index < len(player_df):
        print("\n--- CHUNK COMPLETE. Cooling down for 5 minutes (300s) ---")
        time.sleep(300)

print("\n--- PLAYER BACKFILL COMPLETE ---")