import os
import datetime
from nba_api.stats.endpoints import boxscoretraditionalv3

# This is the Game ID that is failing
game_id = '0022500207'

# Standard headers
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

print(f"--- Debugging BoxScoreTraditionalV3 for game {game_id} ---")

try:
    # 1. Create the boxscore object
    boxscore = boxscoretraditionalv3.BoxScoreTraditionalV3(
        game_id=game_id,
        headers=headers,
        timeout=10
    )
    
    # 2. This is the magic command: 
    # Print all available attributes and methods on the object
    print("\n--- All available attributes: ---")
    print(dir(boxscore))
    
    # 3. Specifically, let's look for the data set names
    # (This might fail, but the `dir()` command above will work)
    try:
        print("\n--- Available data set names: ---")
        print(boxscore.get_data_frame_names())
    except:
        pass

    print("\n--- Debug complete ---")
    
except Exception as e:
    print(f"\n--- An error occurred ---")
    print(e)