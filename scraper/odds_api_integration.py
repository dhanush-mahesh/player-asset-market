"""
Integration with The Odds API for real betting lines
Sign up at: https://the-odds-api.com/
Free tier: 500 requests/month
"""

import os
import requests
from dotenv import load_dotenv
from typing import Dict, List, Optional
import datetime

load_dotenv()

class OddsAPIClient:
    """Fetch real betting lines from The Odds API"""
    
    def __init__(self):
        self.api_key = os.environ.get("ODDS_API_KEY")
        self.base_url = "https://api.the-odds-api.com/v4"
        
    def get_player_props(self, sport: str = "basketball_nba") -> List[Dict]:
        """
        Get player props for NBA games
        
        Markets available:
        - player_points
        - player_rebounds
        - player_assists
        - player_threes
        - player_blocks
        - player_steals
        - player_turnovers
        - player_points_rebounds_assists
        """
        if not self.api_key:
            print("⚠️  ODDS_API_KEY not found in .env")
            return []
        
        # First, get list of events
        events_url = f"{self.base_url}/sports/{sport}/events"
        events_params = {
            "apiKey": self.api_key,
        }
        
        try:
            print("Fetching NBA events...")
            events_response = requests.get(events_url, params=events_params, timeout=10)
            events_response.raise_for_status()
            events = events_response.json()
            
            if not events:
                print("⚠️  No NBA games found today")
                return []
            
            print(f"Found {len(events)} NBA games")
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Error fetching events: {e}")
            return []
        
        # Now fetch props for each event
        # Available markets from The Odds API
        markets = [
            "player_points",
            "player_rebounds", 
            "player_assists",
            "player_threes",  # 3-pointers made
            "player_blocks",
            "player_steals",
            "player_turnovers",
            "player_points_rebounds_assists",  # PRA combo
            "player_points_rebounds",  # PR combo
            "player_points_assists",  # PA combo
            "player_rebounds_assists",  # RA combo
        ]
        all_props = []
        
        for event in events[:3]:  # Limit to first 3 games to save API calls
            event_id = event.get('id')
            
            for market in markets:
                url = f"{self.base_url}/sports/{sport}/events/{event_id}/odds"
                params = {
                    "apiKey": self.api_key,
                    "regions": "us",
                    "markets": market,
                    "oddsFormat": "american"
                }
                
                try:
                    response = requests.get(url, params=params, timeout=10)
                    response.raise_for_status()
                    data = response.json()
                    
                    # Parse the response
                    if 'bookmakers' in data:
                        for bookmaker in data['bookmakers']:
                            for market_data in bookmaker.get('markets', []):
                                # Group outcomes by player
                                outcomes_by_player = {}
                                for outcome in market_data.get('outcomes', []):
                                    player_name = outcome.get('description', '')
                                    if player_name not in outcomes_by_player:
                                        outcomes_by_player[player_name] = {}
                                    
                                    if outcome.get('name') == 'Over':
                                        outcomes_by_player[player_name]['over_odds'] = outcome.get('price')
                                        outcomes_by_player[player_name]['line'] = outcome.get('point')
                                    elif outcome.get('name') == 'Under':
                                        outcomes_by_player[player_name]['under_odds'] = outcome.get('price')
                                
                                # Create prop entries
                                for player_name, odds_data in outcomes_by_player.items():
                                    all_props.append({
                                        'player_name': player_name,
                                        'prop_type': market,
                                        'line': odds_data.get('line'),
                                        'over_odds': odds_data.get('over_odds'),
                                        'under_odds': odds_data.get('under_odds'),
                                        'bookmaker': bookmaker.get('title'),
                                        'game_time': event.get('commence_time'),
                                        'home_team': event.get('home_team'),
                                        'away_team': event.get('away_team')
                                    })
                    
                    print(f"✅ Fetched props for {market} in {event.get('home_team')} vs {event.get('away_team')}")
                    
                except requests.exceptions.RequestException as e:
                    print(f"⚠️  Error fetching {market} for event {event_id}: {e}")
                    continue
        
        print(f"✅ Total props fetched: {len(all_props)}")
        return all_props
    
    def get_player_line(self, player_name: str, prop_type: str = "player_points") -> Optional[Dict]:
        """Get the betting line for a specific player and prop type"""
        props = self.get_player_props()
        
        # Find matching player
        for prop in props:
            if player_name.lower() in prop['player_name'].lower() and prop['prop_type'] == prop_type:
                return prop
        
        return None
    
    def check_remaining_requests(self) -> Dict:
        """Check how many API requests you have left"""
        if not self.api_key:
            return {"error": "No API key"}
        
        url = f"{self.base_url}/sports"
        params = {"apiKey": self.api_key}
        
        try:
            response = requests.get(url, params=params, timeout=10)
            
            # The API returns remaining requests in headers
            remaining = response.headers.get('x-requests-remaining', 'Unknown')
            used = response.headers.get('x-requests-used', 'Unknown')
            
            return {
                "remaining": remaining,
                "used": used,
                "status": "active" if response.status_code == 200 else "error"
            }
        except Exception as e:
            return {"error": str(e)}


# Example usage
if __name__ == "__main__":
    client = OddsAPIClient()
    
    # Check API status
    print("Checking API status...")
    status = client.check_remaining_requests()
    print(f"API Status: {status}")
    
    # Get player props
    print("\nFetching player props...")
    props = client.get_player_props()
    
    if props:
        print(f"\nFound {len(props)} total props")
        print("\nSample props:")
        for prop in props[:5]:
            print(f"  {prop['player_name']}: {prop['prop_type']} - Line: {prop['line']}")
    else:
        print("No props found. Make sure ODDS_API_KEY is set in .env")
