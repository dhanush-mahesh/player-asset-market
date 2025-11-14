import os
import requests
from dotenv import load_dotenv
from supabase import create_client, Client
import datetime
import time
# --- ⭐️ 1. IMPORT THE NEW API ENDPOINT ---
from nba_api.stats.endpoints import scoreboardv2, boxscoretraditionalv3, playerdashboardbyyearoveryear
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
    # (This function is unchanged)
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
    season_stats_list = [] # --- ⭐️ 2. LIST TO HOLD NEW SEASON STATS ---
    
    try:
        boxscore = boxscoretraditionalv3.BoxScoreTraditionalV3(game_id=game_id, headers=headers, timeout=10)
        player_stats_df = boxscore.player_stats.get_data_frame()
        if player_stats_df.empty:
            print(f"  No player stats found for game {game_id}.")
            return [], [], []
        
        for index, row in player_stats_df.iterrows():
            if not row['minutes'] or row['minutes'].startswith('PT00M'):
                continue
            
            nba_api_id = int(row['personId'])
            player_name = f"{row['firstName']} {row['familyName']}"
            team_name = row['teamName']
            position = row['position'] or "N/A"
            headshot_url = f"https://cdn.nba.com/headshots/nba/latest/1040x760/{nba_api_id}.png"
            
            # --- This is for 'daily_player_stats' (unchanged) ---
            stat_line = {
                "nba_api_id_temp": nba_api_id,
                "game_date": game_date.isoformat(),
                "points": int(row['points'] or 0),
                "rebounds": int(row['reboundsTotal'] or 0),
                "assists": int(row['assists'] or 0),
                "steals": int(row['steals'] or 0),
                "blocks": int(row['blocks'] or 0),
                "turnovers": int(row['turnovers'] or 0)
            }
            player_stats_list.append(stat_line)
            player_info_list.add((nba_api_id, player_name, team_name, position, headshot_url))
            
            # --- ⭐️ 3. FETCH THIS PLAYER'S NEW SEASON AVERAGES ---
            try:
                # This API call gets stats for the current season
                seas_stats = playerdashboardbyyearoveryear.PlayerDashboardByYearOverYear(
                    player_id=nba_api_id,
                    season="2025-26", # Hardcoded for this season
                    per_mode_detailed="PerGame",
                    headers=headers,
                    timeout=10
                )
                seas_df = seas_stats.overall_player_dashboard.get_data_frame()
                
                if not seas_df.empty:
                    latest_seas = seas_df.iloc[0] # Get the first (and only) row
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
                    season_stats_list.append(season_obj)
                
                time.sleep(0.5) # Be polite to the API
            except Exception as e:
                print(f"    Error fetching season stats for {player_name}: {e}")
            
        print(f"    Processed {len(player_stats_list)} players for game {game_id}.")
        return player_stats_list, list(player_info_list), season_stats_list # <-- ⭐️ 4. RETURN NEW LIST
        
    except Exception as e:
        print(f"  Error fetching/parsing box score for game {game_id}: {e}")
        return [], [], []

# --- 3. MAIN EXECUTION ---
def run_stats_pipeline():
    print("\n--- STAGE 1: Fetching Existing Players ---")
    player_map = {} # Maps {nba_api_id: supabase_id}
    try:
        response = supabase.table('players').select('id, nba_api_id').execute()
        if response.data:
            for player in response.data:
                player_map[player['nba_api_id']] = player['id']
            print(f"Found {len(player_map)} players in database.")
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
    all_season_stats = [] # <-- ⭐️ 5. LIST TO HOLD ALL SEASON STATS
    
    for game_id in game_ids:
        new_stats, new_player_info, new_season_stats = get_stats_from_game_id(game_id, game_date) # <-- ⭐️ 6. GET NEW LIST
        all_scraped_stats.extend(new_stats)
        all_scraped_players_info.update(new_player_info)
        all_season_stats.extend(new_season_stats) # <-- ⭐️ 7. ADD TO MAIN LIST
        time.sleep(1) # Unchanged
    
    print(f"\nTotal stat lines scraped: {len(all_scraped_stats)}")
    print(f"Total season stats updated: {len(all_season_stats)}")

    # --- STAGE 4: Upserting New Players (Unchanged) ---
    print("\n--- STAGE 4: Upserting New Players ---")
    new_players_to_insert = []
    for nba_api_id, full_name, team_name, position, headshot_url in all_scraped_players_info:
        if nba_api_id not in player_map:
            new_players_to_insert.append({
                "nba_api_id": nba_api_id, "full_name": full_name, 
                "team_name": team_name, "position": position, "headshot_url": headshot_url
            }) 
    if new_players_to_insert:
        print(f"Upserting {len(new_players_to_insert)} new players...")
        try:
            response = supabase.table('players').upsert(new_players_to_insert, on_conflict='nba_api_id').execute()
            if response.data:
                for player_data in response.data:
                    player_map[player_data['nba_api_id']] = player_data['id']
                print("New players upserted and local map updated.")
        except Exception as e:
            print(f"Error upserting new players: {e}")
    else:
        print("No new players to insert.")

    # --- STAGE 5: Upserting Daily Stats (Unchanged) ---
    print("\n--- STAGE 5: Upserting Daily Stats ---")
    final_stats_to_insert = []
    for stat_line in all_scraped_stats:
        nba_api_id = stat_line.pop('nba_api_id_temp')
        player_id = player_map.get(nba_api_id)
        if player_id:
            stat_line['player_id'] = player_id
            final_stats_to_insert.append(stat_line)
        else:
            print(f"Could not find Supabase ID for NBA ID {nba_api_id}. Skipping stat line.")
    if final_stats_to_insert:
        print(f"\nUpserting {len(final_stats_to_insert)} stat lines into 'daily_player_stats'...")
        try:
            response = supabase.table('daily_player_stats').upsert(final_stats_to_insert, on_conflict='player_id, game_date').execute()
            if response.data:
                 print(f"Successfully upserted {len(response.data)} stat lines.")
            print("--- STATS SCRAPE COMPLETE ---")
        except Exception as e:
            print(f"Error upserting stats: {e}")
    else:
        print("\nNo new stats to insert.")
        
    # --- ⭐️ 8. NEW STAGE 6: UPSERT SEASON STATS ---
    print("\n--- STAGE 6: Upserting Season Stats ---")
    final_season_stats_to_insert = []
    for stat_line in all_season_stats:
        nba_api_id = stat_line.pop('nba_api_id_temp')
        player_id = player_map.get(nba_api_id)
        if player_id:
            stat_line['player_id'] = player_id
            final_season_stats_to_insert.append(stat_line)
    
    if final_season_stats_to_insert:
        print(f"\nUpserting {len(final_season_stats_to_insert)} records into 'player_season_stats'...")
        try:
            response = supabase.table('player_season_stats').upsert(
                final_season_stats_to_insert,
                on_conflict='player_id, season'
            ).execute()
            if response.data:
                print(f"Successfully upserted {len(response.data)} season stat records.")
            print("--- SEASON STATS UPDATE COMPLETE ---")
        except Exception as e:
            print(f"Error upserting season stats: {e}")
    else:
        print("\nNo new season stats to insert.")

if __name__ == "__main__":
    run_stats_pipeline()