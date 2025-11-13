import os
from nba_api.stats.endpoints import boxscoretraditionalv3

game_id = '0022500207' # From your log
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

print(f"--- Debugging DataFrame columns for game {game_id} ---")

try:
    # 1. Create the boxscore object
    boxscore = boxscoretraditionalv3.BoxScoreTraditionalV3(
        game_id=game_id,
        headers=headers,
        timeout=10
    )
    
    # 2. Get the DataFrame we found in the last step
    player_stats_df = boxscore.player_stats.get_data_frame()
    
    # 3. Check if it's empty
    if player_stats_df.empty:
        print("!!! Error: The 'player_stats' DataFrame is empty.")
    else:
        # 4. THIS IS THE KEY: Print the list of all column names
        print("\n--- SUCCESS! Found DataFrame. Here are the available columns: ---")
        print(player_stats_df.columns.tolist())
    
    print("\n--- Debug complete ---")
    
except Exception as e:
    print(f"\n--- An error occurred ---")
    print(e)