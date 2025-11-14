import os
from nba_api.stats.endpoints import commonallplayers
import pandas as pd

print("--- Debugging CommonAllPlayers columns ---")

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

try:
    player_data = commonallplayers.CommonAllPlayers(
        is_only_current_season=1,
        headers=headers,
        timeout=30
    )
    player_df = player_data.common_all_players.get_data_frame()
    
    if player_df.empty:
        print("!!! Error: The DataFrame is empty.")
    else:
        # This is the command that will give us the answer
        print("\n--- SUCCESS! Found DataFrame. Here are the available columns: ---")
        print(player_df.columns.tolist())
    
    print("\n--- Debug complete ---")
    
except Exception as e:
    print(f"\n--- An error occurred ---")
    print(e)