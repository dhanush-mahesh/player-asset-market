"""
Fantasy Basketball Lineup Optimizer
"""
import os
from dotenv import load_dotenv
from supabase import create_client, Client
import datetime
import numpy as np
from typing import List, Dict

load_dotenv()

class FantasyOptimizer:
    """Optimize fantasy basketball lineups"""
    
    def __init__(self):
        self.today = datetime.date.today().isoformat()
        # Create fresh Supabase connection
        url: str = os.environ.get("SUPABASE_URL")
        key: str = os.environ.get("SUPABASE_KEY")
        self.supabase: Client = create_client(url, key)
    
    def calculate_fantasy_points(self, stats: Dict) -> float:
        """Calculate fantasy points (standard scoring)"""
        return (
            stats.get('points', 0) * 1.0 +
            stats.get('rebounds', 0) * 1.2 +
            stats.get('assists', 0) * 1.5 +
            stats.get('steals', 0) * 3.0 +
            stats.get('blocks', 0) * 3.0 -
            stats.get('turnovers', 0) * 1.0
        )
    
    def get_optimal_lineup(self, position: str = None, limit: int = 10) -> List[Dict]:
        """Get optimal fantasy picks for today"""
        try:
            # Get latest value data
            latest_date_response = self.supabase.table('player_value_index').select('value_date').order('value_date', desc=True).limit(1).execute()
            if not latest_date_response.data:
                print("⚠️  No player value data found")
                return []
            
            latest_date = latest_date_response.data[0]['value_date']
            
            # Get players with high value and momentum
            query = self.supabase.table('player_value_index').select(
                'player_id, value_score, stat_component, momentum_score'
            ).eq('value_date', latest_date).gte('stat_component', 20)
            
            response = query.execute()
            
            if not response.data:
                print("⚠️  No players found with sufficient stats")
                return []
            
            # Batch fetch all player details at once
            player_ids = [r['player_id'] for r in response.data]
            players_response = self.supabase.table('players').select(
                'id, full_name, team_name, position'
            ).in_('id', player_ids).execute()
            
            # Create player lookup map
            players_map = {p['id']: p for p in players_response.data}
            
            # Batch fetch recent stats for all players
            stats_response = self.supabase.table('daily_player_stats').select(
                'player_id, points, rebounds, assists, steals, blocks, turnovers, game_date'
            ).in_('player_id', player_ids).order('game_date', desc=True).execute()
            
            # Group stats by player (take last 5 games per player)
            stats_by_player = {}
            for stat in stats_response.data:
                pid = stat['player_id']
                if pid not in stats_by_player:
                    stats_by_player[pid] = []
                if len(stats_by_player[pid]) < 5:
                    stats_by_player[pid].append(stat)
            
            lineup_picks = []
            
            for record in response.data:
                player_id = record['player_id']
                player = players_map.get(player_id)
                stats = stats_by_player.get(player_id, [])
                
                if not player or len(stats) < 3:
                    continue
                
                if stats and len(stats) >= 3:
                    # Calculate average fantasy points
                    fantasy_scores = [self.calculate_fantasy_points(g) for g in stats]
                    avg_fantasy = np.mean(fantasy_scores)
                    consistency = 1 / (1 + np.std(fantasy_scores))
                    
                    # Projected fantasy points (weighted by momentum)
                    momentum_boost = 1 + (record['momentum_score'] * 0.1)
                    projected = avg_fantasy * momentum_boost
                    
                    lineup_picks.append({
                        'player_id': player_id,
                        'player_name': player['full_name'],
                        'team': player['team_name'],
                        'position': player['position'],
                        'projected_fantasy_points': round(projected, 1),
                        'avg_fantasy_points': round(avg_fantasy, 1),
                        'consistency_score': round(consistency, 2),
                        'momentum': record['momentum_score'],
                        'value_score': record['value_score'],
                        'recent_stats': {
                            'points': round(np.mean([g['points'] for g in stats]), 1),
                            'rebounds': round(np.mean([g['rebounds'] for g in stats]), 1),
                            'assists': round(np.mean([g['assists'] for g in stats]), 1)
                        }
                    })
            
            # Sort by projected fantasy points
            lineup_picks.sort(key=lambda x: x['projected_fantasy_points'], reverse=True)
            
            # Filter by position if specified
            if position:
                lineup_picks = [p for p in lineup_picks if position.lower() in p['position'].lower()]
            
            return lineup_picks[:limit]
            
        except Exception as e:
            print(f"❌ Error optimizing lineup: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def get_value_picks(self, limit: int = 10) -> List[Dict]:
        """Get best value picks (high performance, lower ownership)"""
        lineup = self.get_optimal_lineup(limit=50)
        
        # Filter for value plays (good stats but not superstars)
        value_picks = [
            p for p in lineup 
            if 40 <= p['value_score'] <= 70 and p['projected_fantasy_points'] > 30
        ]
        
        return value_picks[:limit]
