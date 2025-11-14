import os
import requests
from dotenv import load_dotenv
from supabase import create_client, Client
import datetime
import time
from nba_api.stats.endpoints import scoreboardv2, boxscoretraditionalv3
from nba_api.stats.static import teams

# --- 1. SETUP ---
print("Starting Stats Scraper (Phase 2, Stage 1 - NBA.com API V3)...")
load_dotenv()
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)
print("Successfully connected to Supabase.")
    
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

# --- 2. NBA API FUNCTIONS ---

def get_game_ids_for_yesterday():
    yesterday = datetime.date.today() - datetime.timedelta(days=1)
    game_date = yesterday
    print(f"Fetching game IDs for {game_date.strftime('%Y-%m-%d')}...")
    try:
        scoreboard = scoreboardv2.ScoreboardV2(game_date=game_date.strftime('%m/%d/%Y'), headers=headers, timeout=10)
        games = scoreboard.game_header.get_data_frame()
        if games.empty:
            print("No games found for yesterday.")
            return [], None
        game_ids = games['GAME_ID'].tolist()
        print(f"Found {len(game_ids)} game IDs.")
        return game_ids, game_date
    except Exception as e:
        print(f"Error fetching scoreboard: {e}")
        return [], None

def get_stats_from_game_id(game_id: str, game_date: datetime.date):
    print(f"  Fetching box score for game: {game_id}")
    player_stats_list = []
    player_info_list = set()
    try:
        boxscore = boxscoretraditionalv3.BoxScoreTraditionalV3(game_id=game_id, headers=headers, timeout=10)
        player_stats_df = boxscore.player_stats.get_data_frame()
        if player_stats_df.empty:
            print(f"  No player stats found for game {game_id}.")
            return [], []
        
        for index, row in player_stats_df.iterrows():
            if not row['minutes'] or row['minutes'].startswith('PT00M'):
                continue
            
            # --- ⭐️ 1. GET ALL THE NEW DATA ---
            nba_api_id = int(row['personId'])
            player_name = f"{row['firstName']} {row['familyName']}"
            team_name = row['teamName']
            position = row['position'] or "N/A"
            # --- ⭐️ 2. CONSTRUCT THE HEADSHOT URL ---
            headshot_url = f"https://cdn.nba.com/headshots/nba/latest/1040x760/{nba_api_id}.png"
            
            stat_line = {
                "nba_api_id_temp": nba_api_id, # Temp key for linking
                "game_date": game_date.isoformat(),
                "points": int(row['points'] or 0),
                "rebounds": int(row['reboundsTotal'] or 0),
                "assists": int(row['assists'] or 0),
                "steals": int(row['steals'] or 0),
                "blocks": int(row['blocks'] or 0),
                "turnovers": int(row['turnovers'] or 0)
            }
            player_stats_list.append(stat_line)
            # Add all player info to our set
            player_info_list.add((nba_api_id, player_name, team_name, position, headshot_url))
            
        print(f"    Processed {len(player_stats_list)} players for game {game_id}.")
        return player_stats_list, list(player_info_list)
        
    except Exception as e:
        print(f"  Error fetching/parsing box score for game {game_id}: {e}")
        return [], []

# --- 3. MAIN EXECUTION ---
def run_stats_pipeline():
    print("\n--- STAGE 1: Fetching Existing Players ---")
    # --- ⭐️ 3. PLAYER MAP IS NOW BASED ON NBA_API_ID ---
    player_map = {} # Maps {nba_api_id: supabase_id}
    try:
        response = supabase.table('players').select('id, nba_api_id').execute()
        if response.data:
            for player in response.data:
                player_map[player['nba_api_id']] = player['id']
            print(f"Found {len(player_map)} players in database.")
        else:
            print("No players found in database.")
    except Exception as e:
        print(f"Error fetching players: {e}")
        return

    print("\n--- STAGE 2: Fetching Game IDs ---")
    game_ids, game_date = get_game_ids_for_yesterday()
    if not game_ids:
        print("No games to scrape. Exiting.")
        return
        
    print(f"\n--- STAGE 3: Fetching All Box Scores ---")
    all_scraped_stats = []
    all_scraped_players_info = set()
    for game_id in game_ids:
        new_stats, new_player_info = get_stats_from_game_id(game_id, game_date)
        all_scraped_stats.extend(new_stats)
        all_scraped_players_info.update(new_player_info)
        time.sleep(1.5)
    
    print(f"\nTotal stat lines scraped: {len(all_scraped_stats)}")

    print("\n--- STAGE 4: Upserting New Players ---")
    new_players_to_insert = []
    
    # --- ⭐️ 4. CREATE NEW PLAYER OBJECTS WITH ALL DATA ---
    for nba_api_id, full_name, team_name, position, headshot_url in all_scraped_players_info:
        if nba_api_id not in player_map:
            new_players_to_insert.append({
                "nba_api_id": nba_api_id,
                "full_name": full_name, 
                "team_name": team_name,
                "position": position,
                "headshot_url": headshot_url
            }) 
            
    if new_players_to_insert:
        print(f"Upserting {len(new_players_to_insert)} new players...")
        try:
            # --- ⭐️ 5. UPSERT ON THE NEW 'nba_api_id' COLUMN ---
            response = supabase.table('players').upsert(
                new_players_to_insert, 
                on_conflict='nba_api_id'
            ).execute()
            if response.data:
                for player_data in response.data:
                    player_map[player_data['nba_api_id']] = player_data['id']
                print("New players upserted and local map updated.")
        except Exception as e:
            print(f"Error upserting new players: {e}")
    else:
        print("No new players to insert.")

    print("\n--- STAGE 5: Upserting Daily Stats ---")
    final_stats_to_insert = []
    for stat_line in all_scraped_stats:
        # --- ⭐️ 6. LINK STATS USING THE 'nba_api_id_temp' ---
        nba_api_id = stat_line.pop('nba_api_id_temp')
        player_id = player_map.get(nba_api_id)
        
        if player_id:
            stat_line['player_id'] = player_id # This is the foreign key
            final_stats_to_insert.append(stat_line)
        else:
            print(f"Could not find Supabase ID for NBA ID {nba_api_id}. Skipping stat line.")
            
    if final_stats_to_insert:
        print(f"\nUpserting {len(final_stats_to_insert)} stat lines into 'daily_player_stats'...")
        try:
            response = supabase.table('daily_player_stats').upsert(
                final_stats_to_insert,
                on_conflict='player_id, game_date'
            ).execute()
            if response.data:
                 print(f"Successfully upserted {len(response.data)} stat lines.")
            print("--- STATS SCRAPE COMPLETE ---")
        except Exception as e:
            print(f"Error upserting stats: {e}")
    else:
        print("\nNo new stats to insert.")

if __name__ == "__main__":
    run_stats_pipeline()