"""
Check player risk levels based on current data
"""
import os
from dotenv import load_dotenv
from supabase import create_client, Client
import datetime
import numpy as np

load_dotenv()
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

def calculate_player_risk():
    """Calculate risk for all players"""
    
    today = datetime.date.today().isoformat()
    week_ago = (datetime.date.today() - datetime.timedelta(days=7)).isoformat()
    
    print("="*80)
    print("PLAYER RISK ANALYSIS")
    print("="*80)
    print(f"\nAnalyzing data from {week_ago} to {today}\n")
    
    # Get all players with recent data including today's value
    response = supabase.table('player_value_index').select(
        'player_id, value_date, value_score, confidence_score'
    ).gte('value_date', week_ago).order('player_id').order('value_date', desc=True).execute()
    
    if not response.data:
        print("No data found!")
        return
    
    # Group by player
    players_data = {}
    for record in response.data:
        player_id = record['player_id']
        if player_id not in players_data:
            players_data[player_id] = []
        players_data[player_id].append(record)
    
    print(f"Found {len(players_data)} players with data\n")
    
    # Analyze each player
    low_risk = []
    medium_risk = []
    high_risk = []
    insufficient_data = []
    
    for player_id, data in players_data.items():
        if len(data) < 2:
            insufficient_data.append(player_id)
            continue
        
        # Calculate trend
        values = [d['value_score'] for d in data]
        
        if len(values) >= 7:
            recent_avg = np.mean(values[:3])
            older_avg = np.mean(values[-3:])
            trend = ((recent_avg - older_avg) / older_avg) * 100 if older_avg > 0 else 0
        else:
            trend = ((values[0] - values[-1]) / values[-1]) * 100 if values[-1] > 0 else 0
        
        # Get latest confidence and value score
        confidence = data[0]['confidence_score']
        latest_value = data[0]['value_score']
        
        # Get player name
        try:
            player = supabase.table('players').select('full_name, team_name').eq('id', player_id).single().execute()
            player_name = player.data['full_name']
            team = player.data['team_name']
        except:
            player_name = f"Player {player_id}"
            team = "Unknown"
        
        # NEW RISK CLASSIFICATION
        # High Risk: Trend < -20% OR value score < 30
        # Medium Risk: Trend -20% to -5% OR value score 30-50
        # Low Risk: Trend >= -5% AND value score >= 50
        
        is_high_risk = trend < -20 or latest_value < 30
        is_medium_risk = (-20 <= trend < -5) or (30 <= latest_value < 50)
        is_low_risk = trend >= -5 and latest_value >= 50
        
        player_info = {
            'name': player_name,
            'team': team,
            'trend': trend,
            'value': latest_value,
            'confidence': confidence,
            'data_points': len(values)
        }
        
        if is_high_risk:
            high_risk.append(player_info)
        elif is_medium_risk:
            medium_risk.append(player_info)
        elif is_low_risk:
            low_risk.append(player_info)
        else:
            # Edge cases
            if latest_value >= 50:
                low_risk.append(player_info)
            else:
                medium_risk.append(player_info)
    
    # Print results
    print("="*90)
    print(f"LOW RISK PLAYERS (trend >= -5% AND value >= 50): {len(low_risk)}")
    print("="*90)
    if low_risk:
        low_risk.sort(key=lambda x: (x['value'], x['trend']), reverse=True)
        for i, player in enumerate(low_risk[:20], 1):
            print(f"{i:2d}. {player['name']:30s} ({player['team']:20s}) | "
                  f"Value: {player['value']:5.1f} | Trend: {player['trend']:+6.2f}% | "
                  f"Conf: {player['confidence']:.2f}")
    else:
        print("No low-risk players found!")
    
    print("\n" + "="*90)
    print(f"MEDIUM RISK PLAYERS (trend -20% to -5% OR value 30-50): {len(medium_risk)}")
    print("="*90)
    if medium_risk:
        medium_risk.sort(key=lambda x: (x['value'], x['trend']), reverse=True)
        for i, player in enumerate(medium_risk[:20], 1):
            print(f"{i:2d}. {player['name']:30s} ({player['team']:20s}) | "
                  f"Value: {player['value']:5.1f} | Trend: {player['trend']:+6.2f}% | "
                  f"Conf: {player['confidence']:.2f}")
    
    print("\n" + "="*90)
    print(f"HIGH RISK PLAYERS (trend < -20% OR value < 30): {len(high_risk)}")
    print("="*90)
    if high_risk:
        high_risk.sort(key=lambda x: (x['value'], x['trend']))
        for i, player in enumerate(high_risk[:20], 1):
            print(f"{i:2d}. {player['name']:30s} ({player['team']:20s}) | "
                  f"Value: {player['value']:5.1f} | Trend: {player['trend']:+6.2f}% | "
                  f"Conf: {player['confidence']:.2f}")
    
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    total = len(low_risk) + len(medium_risk) + len(high_risk)
    print(f"Total players analyzed: {total}")
    print(f"Low Risk:    {len(low_risk):3d} ({len(low_risk)/total*100:.1f}%)")
    print(f"Medium Risk: {len(medium_risk):3d} ({len(medium_risk)/total*100:.1f}%)")
    print(f"High Risk:   {len(high_risk):3d} ({len(high_risk)/total*100:.1f}%)")
    print(f"Insufficient data: {len(insufficient_data)}")
    print("="*80)

if __name__ == "__main__":
    calculate_player_risk()
