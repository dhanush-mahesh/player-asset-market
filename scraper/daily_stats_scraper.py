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

if not url or not key:
    print("Error: SUPABASE_URL or SUPABASE_KEY not found in .env file.")
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
    'Accept-Encoding': 'gzip, deflate, br',
    'x-nba-stats-origin': 'stats',
    'x-nba-stats-token': 'true',
    'Connection': 'keep-alive',
    'Referer': 'https://stats.nba.com/',
    'Pragma': 'no-cache',
    'Cache-Control': 'no-cache',
}

# --- 2. NBA API FUNCTIONS ---

def get_game_ids_for_yesterday():
    """ Fetches all game IDs for yesterday from the NBA scoreboard. """
    yesterday = datetime.date.today() - datetime.timedelta(days=1)
    game_date = yesterday
    print(f"Fetching game IDs for {game_date.strftime('%Y-%m-%d')}...")
    
    try:
        scoreboard = scoreboardv2.ScoreboardV2(
            game_date=game_date.strftime('%m/%d/%Y'),
            headers=headers,
            timeout=10
        )
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
    """ Fetches the full box score for a single game ID. """
    print(f"  Fetching box score for game: {game_id}")
    player_stats_list = []
    player_names_found = set()
    
    try:
        boxscore = boxscoretraditionalv3.BoxScoreTraditionalV3(
            game_id=game_id,
            headers=headers,
            timeout=10
        )
        
        player_stats_df = boxscore.player_stats.get_data_frame()
        
        if player_stats_df.empty:
            print(f"  No player stats found for game {game_id}.")
            return [], []

        # We can use the teamName from the box score, it's easier
        
        for index, row in player_stats_df.iterrows():
            
            # Use the 'minutes' column to check for DNP
            if not row['minutes'] or row['minutes'].startswith('PT00M'):
                continue
                
            # --- ⭐️ CHANGED: Use the correct column names from your log ---
            player_name = f"{row['firstName']} {row['familyName']}"
            team_name = row['teamName']
            
            stat_line = {
                "player_name": player_name,
                "team_name": team_name,
                "game_date": game_date.isoformat(),
                "points": int(row['points'] or 0),
                "rebounds": int(row['reboundsTotal'] or 0),
                "assists": int(row['assists'] or 0),
                "steals": int(row['steals'] or 0),
                "blocks": int(row['blocks'] or 0),
                "turnovers": int(row['turnovers'] or 0)
            }
            
            player_stats_list.append(stat_line)
            player_names_found.add((player_name, team_name))
            
        print(f"    Processed {len(player_stats_list)} players for game {game_id}.")
        return player_stats_list, list(player_names_found)
        
    except Exception as e:
        print(f"  Error fetching/parsing box score for game {game_id}: {e}")
        return [], []

# --- 3. MAIN EXECUTION ---
def run_stats_pipeline():
    print("\n--- STAGE 1: Fetching Existing Players ---")
    player_map = {} # Maps {full_name: supabase_id}
    try:
        response = supabase.table('players').select('id, full_name').execute()
        if response.data:
            for player in response.data:
                player_map[player['full_name']] = player['id']
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
        
    print(f"\n--- STAGE 3: Fetching All Box Scores ({len(game_ids)} games) ---")
    all_scraped_stats = []
    all_scraped_players = set()
    
    for game_id in game_ids:
        new_stats, new_players = get_stats_from_game_id(game_id, game_date)
        all_scraped_stats.extend(new_stats)
        all_scraped_players.update(new_players)
        time.sleep(1.5) # Be polite to the API
    
    print(f"\nTotal stat lines scraped: {len(all_scraped_stats)}")

    print("\n--- STAGE 4: Inserting New Players ---")
    new_players_to_insert = []
    for player_name, team_name in all_scraped_players:
        if player_name not in player_map:
            new_players_to_insert.append({
                "full_name": player_name, 
                "team_name": team_name,
                "position": "N/A" # Position is in the data, but let's keep it simple
            }) 
            
    if new_players_to_insert:
        print(f"Inserting {len(new_players_to_insert)} new players...")
        try:
            response = supabase.table('players').insert(new_players_to_insert).execute()
            if response.data:
                for player_data in response.data:
                    player_map[player_data['full_name']] = player_data['id']
                print("New players inserted and local map updated.")
            else:
                print("Error: Inserted new players but received no data back.")
        except Exception as e:
            print(f"Error inserting new players: {e}")
    else:
        print("No new players to insert.")

    print("\n--- STAGE 5: Inserting Daily Stats ---")
    final_stats_to_insert = []
    for stat_line in all_scraped_stats:
        player_name = stat_line.pop('player_name')
        stat_line.pop('team_name')
        player_id = player_map.get(player_name)
        
        if player_id:
            stat_line['player_id'] = player_id
            final_stats_to_insert.append(stat_line)
        else:
            print(f"Could not find ID for {player_name}. Skipping stat line.")
            
    if final_stats_to_insert:
        print(f"\nInserting {len(final_stats_to_insert)} stat lines into 'daily_player_stats'...")
        try:
            response = supabase.table('daily_player_stats').insert(final_stats_to_insert).execute()
            if response.data:
                 print(f"Successfully inserted {len(response.data)} stat lines.")
            print("--- STATS SCRAPE COMPLETE ---")
        except Exception as e:
            print(f"Error inserting stats: {e}")
    else:
        print("\nNo new stats to insert.")

if __name__ == "__main__":
    run_stats_pipeline()