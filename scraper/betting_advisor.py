"""
Sports Betting Advisor - Provides data-driven betting insights
"""
import os
from dotenv import load_dotenv
from supabase import create_client, Client
import datetime
from typing import List, Dict

load_dotenv()
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

class BettingAdvisor:
    """Provides betting insights based on player performance and trends"""
    
    # Class-level cache that persists across instances
    _lines_cache = {}
    _cache_timestamp = None
    _cache_duration = 300  # 5 minutes in seconds
    
    def __init__(self, use_real_lines: bool = False):
        self.today = datetime.date.today().isoformat()
        self.use_real_lines = use_real_lines
        self.real_lines_cache = {}
        
        # Try to load real betting lines if enabled
        if use_real_lines:
            try:
                from odds_api_integration import OddsAPIClient
                self.odds_client = OddsAPIClient()
                self._load_real_lines()
            except Exception as e:
                print(f"⚠️  Could not load real betting lines: {e}")
                self.use_real_lines = False
    
    def _normalize_name(self, name: str) -> str:
        """Normalize player name for matching"""
        # Remove periods, extra spaces, convert to lowercase
        # Also remove common suffixes like Jr., Sr., III, etc.
        normalized = name.lower().replace('.', '').replace('  ', ' ').strip()
        normalized = normalized.replace(' jr', '').replace(' sr', '').replace(' iii', '').replace(' ii', '')
        return normalized
    
    def _format_prop_name(self, prop_type: str) -> str:
        """Format prop type for display"""
        prop_names = {
            'points': 'Points',
            'rebounds': 'Rebounds',
            'assists': 'Assists',
            'threes': '3-Pointers',
            'blocks': 'Blocks',
            'steals': 'Steals',
            'turnovers': 'Turnovers',
            'points_rebounds_assists': 'Pts+Reb+Ast',
            'points_rebounds': 'Pts+Reb',
            'points_assists': 'Pts+Ast',
            'rebounds_assists': 'Reb+Ast',
        }
        return prop_names.get(prop_type, prop_type.capitalize())
    
    def _get_default_consistency_response(self) -> Dict:
        """Return default consistency response when data is insufficient"""
        return {
            'rating': 'Unknown',
            'std': 0,
            'matchup_adjusted': False,
            'explanation': 'Insufficient data'
        }
    
    def _get_matchup_aware_consistency(self, player_id: str, prop_type: str, opponent_team: str = None) -> Dict:
        """
        Calculate consistency that accounts for opponent strength and matchup history
        
        Returns:
            dict with 'rating' (High/Medium/Low), 'std' (standard deviation), 
            'matchup_adjusted' (bool), and 'explanation' (str)
        """
        try:
            import numpy as np
            
            # For combo props, we can't query them directly - calculate from components
            if prop_type in ['points_rebounds_assists', 'points_rebounds', 'points_assists', 'rebounds_assists']:
                # Get component stats
                try:
                    stats_response = supabase.table('daily_player_stats').select(
                        'points, rebounds, assists, game_date, opponent_team'
                    ).eq('player_id', player_id).order('game_date', desc=True).limit(10).execute()
                    has_opponent_data = True
                except:
                    stats_response = supabase.table('daily_player_stats').select(
                        'points, rebounds, assists, game_date'
                    ).eq('player_id', player_id).order('game_date', desc=True).limit(10).execute()
                    has_opponent_data = False
                
                if not stats_response.data or len(stats_response.data) < 3:
                    return self._get_default_consistency_response()
                
                # Calculate combo values
                games = stats_response.data
                if prop_type == 'points_rebounds_assists':
                    all_stats = [g['points'] + g['rebounds'] + g['assists'] for g in games if all(g.get(k) is not None for k in ['points', 'rebounds', 'assists'])]
                elif prop_type == 'points_rebounds':
                    all_stats = [g['points'] + g['rebounds'] for g in games if all(g.get(k) is not None for k in ['points', 'rebounds'])]
                elif prop_type == 'points_assists':
                    all_stats = [g['points'] + g['assists'] for g in games if all(g.get(k) is not None for k in ['points', 'assists'])]
                elif prop_type == 'rebounds_assists':
                    all_stats = [g['rebounds'] + g['assists'] for g in games if all(g.get(k) is not None for k in ['rebounds', 'assists'])]
            else:
                # Single stat - query directly
                # Get last 10 games - try with opponent_team first, fall back if column doesn't exist
                try:
                    stats_response = supabase.table('daily_player_stats').select(
                        f'{prop_type}, game_date, opponent_team'
                    ).eq('player_id', player_id).order('game_date', desc=True).limit(10).execute()
                    has_opponent_data = True
                except:
                    # Column doesn't exist, get stats without opponent info
                    stats_response = supabase.table('daily_player_stats').select(
                        f'{prop_type}, game_date'
                    ).eq('player_id', player_id).order('game_date', desc=True).limit(10).execute()
                    has_opponent_data = False
                
                if not stats_response.data or len(stats_response.data) < 3:
                    return self._get_default_consistency_response()
                
                games = stats_response.data
                all_stats = [g[prop_type] for g in games if g.get(prop_type) is not None]
            
            if len(all_stats) < 3:
                return self._get_default_consistency_response()
            
            # Calculate raw consistency
            raw_std = np.std(all_stats)
            
            # If we have opponent info and opponent_team column exists, adjust for matchup
            if opponent_team and has_opponent_data:
                # Find games against similar opponents (same team or similar defensive rating)
                matchup_games = [g for g in games if g.get('opponent_team') == opponent_team]
                
                if len(matchup_games) >= 2:
                    # We have head-to-head history
                    matchup_stats = [g[prop_type] for g in matchup_games if g.get(prop_type) is not None]
                    matchup_std = np.std(matchup_stats)
                    matchup_avg = np.mean(matchup_stats)
                    
                    # Use matchup-specific consistency
                    if matchup_std < 3:
                        rating = 'High'
                    elif matchup_std < 5:
                        rating = 'Medium'
                    else:
                        rating = 'Low'
                    
                    return {
                        'rating': rating,
                        'std': matchup_std,
                        'matchup_adjusted': True,
                        'matchup_avg': matchup_avg,
                        'matchup_games': len(matchup_games),
                        'explanation': f'vs {opponent_team}: {len(matchup_games)} game history'
                    }
            
            # Fallback to raw consistency
            if raw_std < 3:
                rating = 'High'
            elif raw_std < 5:
                rating = 'Medium'
            else:
                rating = 'Low'
            
            return {
                'rating': rating,
                'std': raw_std,
                'matchup_adjusted': False,
                'explanation': f'Last {len(all_stats)} games (no matchup data)'
            }
            
        except Exception as e:
            # Silently fall back to basic calculation
            import numpy as np
            try:
                # For combo props, calculate from components
                if prop_type in ['points_rebounds_assists', 'points_rebounds', 'points_assists', 'rebounds_assists']:
                    stats_response = supabase.table('daily_player_stats').select(
                        'points, rebounds, assists'
                    ).eq('player_id', player_id).order('game_date', desc=True).limit(5).execute()
                    
                    if stats_response.data and len(stats_response.data) >= 3:
                        if prop_type == 'points_rebounds_assists':
                            all_stats = [g['points'] + g['rebounds'] + g['assists'] for g in stats_response.data if all(g.get(k) is not None for k in ['points', 'rebounds', 'assists'])]
                        elif prop_type == 'points_rebounds':
                            all_stats = [g['points'] + g['rebounds'] for g in stats_response.data if all(g.get(k) is not None for k in ['points', 'rebounds'])]
                        elif prop_type == 'points_assists':
                            all_stats = [g['points'] + g['assists'] for g in stats_response.data if all(g.get(k) is not None for k in ['points', 'assists'])]
                        elif prop_type == 'rebounds_assists':
                            all_stats = [g['rebounds'] + g['assists'] for g in stats_response.data if all(g.get(k) is not None for k in ['rebounds', 'assists'])]
                        
                        if len(all_stats) >= 3:
                            raw_std = np.std(all_stats)
                            
                            if raw_std < 3:
                                rating = 'High'
                            elif raw_std < 5:
                                rating = 'Medium'
                            else:
                                rating = 'Low'
                            
                            return {
                                'rating': rating,
                                'std': raw_std,
                                'matchup_adjusted': False,
                                'explanation': f'Last {len(all_stats)} games'
                            }
                else:
                    # Single stat
                    stats_response = supabase.table('daily_player_stats').select(
                        f'{prop_type}'
                    ).eq('player_id', player_id).order('game_date', desc=True).limit(5).execute()
                    
                    if stats_response.data and len(stats_response.data) >= 3:
                        all_stats = [g[prop_type] for g in stats_response.data if g.get(prop_type) is not None]
                        
                        if len(all_stats) >= 3:
                            raw_std = np.std(all_stats)
                            
                            if raw_std < 3:
                                rating = 'High'
                            elif raw_std < 5:
                                rating = 'Medium'
                            else:
                                rating = 'Low'
                            
                            return {
                                'rating': rating,
                                'std': raw_std,
                                'matchup_adjusted': False,
                                'explanation': f'Last {len(all_stats)} games'
                            }
            except:
                pass
            
            return self._get_default_consistency_response()
    
    def _load_real_lines(self):
        """Load real betting lines from The Odds API (with caching)"""
        try:
            import time
            
            # Check if we have a valid cache
            if (BettingAdvisor._lines_cache and 
                BettingAdvisor._cache_timestamp and 
                time.time() - BettingAdvisor._cache_timestamp < BettingAdvisor._cache_duration):
                print(f"✅ Using cached lines ({len(BettingAdvisor._lines_cache)} players)")
                self.real_lines_cache = BettingAdvisor._lines_cache
                return
            
            print("🔄 Fetching fresh lines from Odds API...")
            try:
                props = self.odds_client.get_player_props()
            except Exception as e:
                print(f"❌ Error fetching from Odds API: {e}")
                print("   This might mean:")
                print("   - API credits exhausted (500/month limit)")
                print("   - Network issue")
                print("   - API key invalid")
                props = []
            
            if not props:
                print("⚠️  No props returned from API (might be no games today)")
                return
            
            # Preferred bookmakers (in order of preference)
            preferred_books = ['fanduel', 'draftkings', 'betmgm', 'caesars', 'pointsbet', 'bovada']
            
            # Cache lines by normalized player name
            for prop in props:
                if not prop.get('player_name') or not prop.get('line'):
                    continue
                    
                player_name = self._normalize_name(prop['player_name'])
                prop_type = prop['prop_type'].replace('player_', '')
                bookmaker = prop.get('bookmaker', '').lower()
                
                if player_name not in self.real_lines_cache:
                    self.real_lines_cache[player_name] = {
                        'home_team': prop.get('home_team'),
                        'away_team': prop.get('away_team'),
                        'props': {}
                    }
                
                # Only update if this is a preferred bookmaker or we don't have a line yet
                if prop_type not in self.real_lines_cache[player_name]['props']:
                    # First line for this prop - take it
                    self.real_lines_cache[player_name]['props'][prop_type] = {
                        'line': prop['line'],
                        'over_odds': prop.get('over_odds'),
                        'under_odds': prop.get('under_odds'),
                        'bookmaker': prop.get('bookmaker')
                    }
                else:
                    # We already have a line - only replace if this bookmaker is better
                    current_book = self.real_lines_cache[player_name]['props'][prop_type].get('bookmaker', '').lower()
                    
                    # Get preference scores (lower is better)
                    current_score = preferred_books.index(current_book) if current_book in preferred_books else 999
                    new_score = preferred_books.index(bookmaker) if bookmaker in preferred_books else 999
                    
                    if new_score < current_score:
                        # This bookmaker is preferred - replace
                        self.real_lines_cache[player_name]['props'][prop_type] = {
                            'line': prop['line'],
                            'over_odds': prop.get('over_odds'),
                            'under_odds': prop.get('under_odds'),
                            'bookmaker': prop.get('bookmaker')
                        }
            
            print(f"✅ Loaded real lines for {len(self.real_lines_cache)} players")
            
            # Store in class-level cache
            import time
            BettingAdvisor._lines_cache = self.real_lines_cache
            BettingAdvisor._cache_timestamp = time.time()
            
            # Debug: show sample cached players
            if self.real_lines_cache:
                print("Sample players with real lines:")
                for player_name in list(self.real_lines_cache.keys())[:5]:
                    props_available = list(self.real_lines_cache[player_name]['props'].keys())
                    game_info = f"{self.real_lines_cache[player_name]['away_team']} @ {self.real_lines_cache[player_name]['home_team']}"
                    print(f"  - {player_name} ({game_info}): {', '.join(props_available)}")
                    
        except Exception as e:
            print(f"❌ Error loading real lines: {e}")
            import traceback
            traceback.print_exc()
    
    def _get_line_for_player(self, player_name: str, prop_type: str, calculated_line: float) -> Dict:
        """Get betting line - real if available, otherwise calculated"""
        if self.use_real_lines:
            normalized_name = self._normalize_name(player_name)
            
            # Try exact match first
            if normalized_name in self.real_lines_cache:
                real_line = self.real_lines_cache[normalized_name]['props'].get(prop_type)
                if real_line:
                    print(f"✅ Found real line for {player_name}: {real_line['line']} ({real_line['bookmaker']})")
                    return {
                        'line': real_line['line'],
                        'source': 'sportsbook',
                        'bookmaker': real_line.get('bookmaker'),
                        'over_odds': real_line.get('over_odds'),
                        'under_odds': real_line.get('under_odds'),
                        'opponent': self.real_lines_cache[normalized_name].get('away_team') or self.real_lines_cache[normalized_name].get('home_team')
                    }
            
            # Try fuzzy match - split into parts and match
            name_parts = normalized_name.split()
            
            for cached_name, cached_data in self.real_lines_cache.items():
                cached_parts = cached_name.split()
                
                # Check if all significant parts match
                # (first name initial + last name, or full match)
                matches = 0
                for part in name_parts:
                    if len(part) > 1:  # Skip single letters
                        for cached_part in cached_parts:
                            if part in cached_part or cached_part in part:
                                matches += 1
                                break
                
                # If most parts match, consider it a match
                if matches >= len(name_parts) - 1 or matches >= len(cached_parts) - 1:
                    real_line = cached_data['props'].get(prop_type)
                    if real_line:
                        print(f"✅ Found real line for {player_name} (matched '{cached_name}'): {real_line['line']} ({real_line['bookmaker']})")
                        return {
                            'line': real_line['line'],
                            'source': 'sportsbook',
                            'bookmaker': real_line.get('bookmaker'),
                            'over_odds': real_line.get('over_odds'),
                            'under_odds': real_line.get('under_odds'),
                            'opponent': cached_data.get('away_team') or cached_data.get('home_team')
                        }
            
            # Last resort: try last name only
            if len(name_parts) > 1:
                last_name = name_parts[-1]
                for cached_name, cached_data in self.real_lines_cache.items():
                    if last_name in cached_name.split()[-1]:
                        real_line = cached_data['props'].get(prop_type)
                        if real_line:
                            print(f"✅ Found real line for {player_name} (last name match '{cached_name}'): {real_line['line']}")
                            return {
                                'line': real_line['line'],
                                'source': 'sportsbook',
                                'bookmaker': real_line.get('bookmaker'),
                                'over_odds': real_line.get('over_odds'),
                                'under_odds': real_line.get('under_odds'),
                                'opponent': cached_data.get('away_team') or cached_data.get('home_team')
                            }
        
        # Fallback to calculated line
        print(f"ℹ️  Using calculated line for {player_name}: {calculated_line}")
        print(f"   Available players in cache: {list(self.real_lines_cache.keys())[:10] if self.use_real_lines else 'N/A'}")
        return {
            'line': calculated_line,
            'source': 'calculated',
            'bookmaker': None,
            'over_odds': None,
            'under_odds': None
        }
    
    def get_player_prop_insights(self, player_id: str) -> Dict:
        """Get betting insights for player props (points, rebounds, assists)"""
        try:
            # Get recent stats (last 5 games)
            stats_response = supabase.table('daily_player_stats').select(
                'points, rebounds, assists, steals, blocks, game_date'
            ).eq('player_id', player_id).order('game_date', desc=True).limit(10).execute()
            
            if not stats_response.data or len(stats_response.data) < 3:
                return {'error': 'Not enough recent games'}
            
            stats = stats_response.data
            
            # Calculate averages and trends
            recent_5 = stats[:5]
            last_10 = stats[:10] if len(stats) >= 10 else stats
            
            points_avg_5 = sum(g['points'] for g in recent_5) / len(recent_5)
            points_avg_10 = sum(g['points'] for g in last_10) / len(last_10)
            
            rebounds_avg_5 = sum(g['rebounds'] for g in recent_5) / len(recent_5)
            rebounds_avg_10 = sum(g['rebounds'] for g in last_10) / len(last_10)
            
            assists_avg_5 = sum(g['assists'] for g in recent_5) / len(recent_5)
            assists_avg_10 = sum(g['assists'] for g in last_10) / len(last_10)
            
            # Trend analysis (recent vs longer term)
            points_trend = "UP" if points_avg_5 > points_avg_10 else "DOWN"
            rebounds_trend = "UP" if rebounds_avg_5 > rebounds_avg_10 else "DOWN"
            assists_trend = "UP" if assists_avg_5 > assists_avg_10 else "DOWN"
            
            # Consistency (lower std = more consistent = safer bet)
            import numpy as np
            points_std = np.std([g['points'] for g in recent_5])
            rebounds_std = np.std([g['rebounds'] for g in recent_5])
            assists_std = np.std([g['assists'] for g in recent_5])
            
            # Get player name for real lines lookup
            player_response = supabase.table('players').select('full_name').eq('id', player_id).single().execute()
            player_name = player_response.data['full_name'] if player_response.data else ""
            
            # Betting recommendations
            recommendations = []
            
            # Points prop
            if points_trend == "UP" and points_std < 5:
                line_info = self._get_line_for_player(player_name, 'points', round(points_avg_5, 1))
                recommendations.append({
                    'prop': 'Points',
                    'line': line_info['line'],
                    'line_source': line_info['source'],
                    'bookmaker': line_info['bookmaker'],
                    'over_odds': line_info['over_odds'],
                    'recommendation': 'OVER',
                    'confidence': 'HIGH',
                    'reason': f'Trending up ({points_avg_5:.1f} vs {points_avg_10:.1f}) with low variance'
                })
            elif points_trend == "UP":
                line_info = self._get_line_for_player(player_name, 'points', round(points_avg_5, 1))
                recommendations.append({
                    'prop': 'Points',
                    'line': line_info['line'],
                    'line_source': line_info['source'],
                    'bookmaker': line_info['bookmaker'],
                    'over_odds': line_info['over_odds'],
                    'recommendation': 'OVER',
                    'confidence': 'MEDIUM',
                    'reason': f'Trending up but inconsistent (std: {points_std:.1f})'
                })
            
            # Rebounds prop
            if rebounds_trend == "UP" and rebounds_std < 2:
                line_info = self._get_line_for_player(player_name, 'rebounds', round(rebounds_avg_5, 1))
                recommendations.append({
                    'prop': 'Rebounds',
                    'line': line_info['line'],
                    'line_source': line_info['source'],
                    'bookmaker': line_info['bookmaker'],
                    'over_odds': line_info['over_odds'],
                    'recommendation': 'OVER',
                    'confidence': 'HIGH',
                    'reason': f'Trending up ({rebounds_avg_5:.1f} vs {rebounds_avg_10:.1f}) with consistency'
                })
            
            # Assists prop
            if assists_trend == "UP" and assists_std < 2:
                line_info = self._get_line_for_player(player_name, 'assists', round(assists_avg_5, 1))
                recommendations.append({
                    'prop': 'Assists',
                    'line': line_info['line'],
                    'line_source': line_info['source'],
                    'bookmaker': line_info['bookmaker'],
                    'over_odds': line_info['over_odds'],
                    'recommendation': 'OVER',
                    'confidence': 'HIGH',
                    'reason': f'Trending up ({assists_avg_5:.1f} vs {assists_avg_10:.1f}) with consistency'
                })
            
            return {
                'player_id': player_id,
                'averages': {
                    'points_last_5': round(points_avg_5, 1),
                    'points_last_10': round(points_avg_10, 1),
                    'rebounds_last_5': round(rebounds_avg_5, 1),
                    'rebounds_last_10': round(rebounds_avg_10, 1),
                    'assists_last_5': round(assists_avg_5, 1),
                    'assists_last_10': round(assists_avg_10, 1)
                },
                'trends': {
                    'points': points_trend,
                    'rebounds': rebounds_trend,
                    'assists': assists_trend
                },
                'consistency': {
                    'points_std': round(points_std, 2),
                    'rebounds_std': round(rebounds_std, 2),
                    'assists_std': round(assists_std, 2)
                },
                'recommendations': recommendations
            }
            
        except Exception as e:
            print(f"Error getting prop insights: {e}")
            return {'error': str(e)}
    
    def _get_picks_from_real_lines(self, limit: int) -> List[Dict]:
        """Get picks directly from players with real lines (today's games) - OPTIMIZED"""
        picks = []
        
        # Pre-fetch all players from database to avoid repeated queries
        print("📊 Pre-fetching player database...")
        all_players_response = supabase.table('players').select(
            'id, full_name, team_name, position'
        ).execute()
        
        # Build lookup maps for fast matching
        players_by_name = {}
        players_by_last_name = {}
        for p in all_players_response.data:
            normalized = self._normalize_name(p['full_name'])
            players_by_name[normalized] = p
            last_name = normalized.split()[-1] if ' ' in normalized else normalized
            if last_name not in players_by_last_name:
                players_by_last_name[last_name] = []
            players_by_last_name[last_name].append(p)
        
        print(f"✅ Loaded {len(players_by_name)} players into cache")
        
        # Common nickname and name variation mappings
        nickname_map = {
            'carlton carrington': 'bub carrington',
            'carlton "bub" carrington': 'bub carrington',
            'vit krejci': 'vít krejčí',
            'kristaps porzingis': 'kristaps porzingis',
            'luka doncic': 'luka dončić',
            'bogdan bogdanovic': 'bogdan bogdanović',
            'nikola jokic': 'nikola jokić',
            'nikola vucevic': 'nikola vučević',
            'dario saric': 'dario šarić',
            'bojan bogdanovic': 'bojan bogdanović',
            'goran dragic': 'goran dragić',
        }
        
        for player_name, player_data in self.real_lines_cache.items():
            # Check all available prop types for this player
            available_props = []
            opponent_team = player_data.get('away_team') or player_data.get('home_team')
            
            # Map API prop names to database column names
            prop_type_map = {
                'points': 'points',
                'rebounds': 'rebounds',
                'assists': 'assists',
                'threes': 'three_pointers_made',
                'blocks': 'blocks',
                'steals': 'steals',
                'turnovers': 'turnovers',
                'points_rebounds_assists': 'pra',  # Calculated
                'points_rebounds': 'pr',  # Calculated
                'points_assists': 'pa',  # Calculated
                'rebounds_assists': 'ra',  # Calculated
            }
            
            for prop_type in prop_type_map.keys():
                if prop_type not in player_data['props']:
                    continue
                
                prop_data = player_data['props'][prop_type]
                available_props.append({
                    'type': prop_type,
                    'line': prop_data['line'],
                    'bookmaker': prop_data['bookmaker'],
                    'over_odds': prop_data.get('over_odds'),
                    'under_odds': prop_data.get('under_odds')
                })
            
            if not available_props:
                continue
            
            # Try to find this player in database using cached data
            try:
                # Normalize the name for searching
                search_name = self._normalize_name(player_name)
                
                # Check nickname map
                if search_name in nickname_map:
                    search_name = nickname_map[search_name]
                
                player = None
                
                # Strategy 1: Exact match
                if search_name in players_by_name:
                    player = players_by_name[search_name]
                
                # Strategy 2: Last name match
                if not player:
                    last_name = search_name.split()[-1] if ' ' in search_name else search_name
                    if last_name in players_by_last_name:
                        candidates = players_by_last_name[last_name]
                        # Try to match first name too
                        first_name = search_name.split()[0] if ' ' in search_name else ''
                        for candidate in candidates:
                            candidate_normalized = self._normalize_name(candidate['full_name'])
                            if first_name and first_name[:3] in candidate_normalized:
                                player = candidate
                                break
                        if not player and candidates:
                            player = candidates[0]  # Take first match
                
                # Strategy 3: Fuzzy match
                if not player:
                    name_parts = search_name.split()
                    for cached_name, cached_player in players_by_name.items():
                        cached_parts = cached_name.split()
                        matches = sum(1 for part in name_parts if any(part in cp or cp in part for cp in cached_parts if len(part) > 1))
                        if matches >= len(name_parts) - 1:
                            player = cached_player
                            break
                
                if not player:
                    continue
                
                # Get recent stats - fetch all needed columns
                stats = supabase.table('daily_player_stats').select(
                    'points, rebounds, assists, steals, blocks, turnovers, three_pointers_made'
                ).eq('player_id', player['id']).order('game_date', desc=True).limit(5).execute()
                
                if stats.data and len(stats.data) >= 3:
                    import numpy as np
                    
                    # Analyze each available prop type
                    best_pick = None
                    best_value_score = 0
                    
                    for prop in available_props:
                        prop_type = prop['type']
                        line = prop['line']
                        db_column = prop_type_map.get(prop_type)
                        
                        # Calculate stat values (handle combo props)
                        if prop_type == 'points_rebounds_assists':
                            recent_stats = [g['points'] + g['rebounds'] + g['assists'] for g in stats.data]
                        elif prop_type == 'points_rebounds':
                            recent_stats = [g['points'] + g['rebounds'] for g in stats.data]
                        elif prop_type == 'points_assists':
                            recent_stats = [g['points'] + g['assists'] for g in stats.data]
                        elif prop_type == 'rebounds_assists':
                            recent_stats = [g['rebounds'] + g['assists'] for g in stats.data]
                        elif db_column and db_column in stats.data[0]:
                            recent_stats = [g[db_column] for g in stats.data if g.get(db_column) is not None]
                        else:
                            continue  # Skip if stat not available
                        
                        if not recent_stats or len(recent_stats) < 3:
                            continue
                        
                        player_avg = np.mean(recent_stats)
                        stat_std = np.std(recent_stats)
                        
                        # Calculate value score (how much edge we have)
                        edge = player_avg - line
                        value_score = abs(edge)
                        
                        # Determine recommendation
                        if edge > 2:
                            recommendation = 'OVER'
                            confidence = 'HIGH'
                            reason = f'Averaging {player_avg:.1f}, line is {line} - strong value'
                        elif edge > 0.5:
                            recommendation = 'OVER'
                            confidence = 'MEDIUM'
                            reason = f'Averaging {player_avg:.1f}, slight edge over {line}'
                        elif edge < -2:
                            recommendation = 'UNDER'
                            confidence = 'MEDIUM'
                            reason = f'Averaging {player_avg:.1f}, line seems high at {line}'
                        else:
                            recommendation = 'PASS'
                            confidence = 'LOW'
                            reason = f'Line {line} fairly priced (avg: {player_avg:.1f})'
                        
                        # Only consider OVER/UNDER picks (skip PASS)
                        if recommendation != 'PASS' and value_score > best_value_score:
                            best_value_score = value_score
                            
                            # Use simple consistency calculation for speed (skip matchup-aware for now)
                            # Matchup-aware is slower due to additional queries
                            if stat_std < 3:
                                consistency_rating = 'High'
                            elif stat_std < 5:
                                consistency_rating = 'Medium'
                            else:
                                consistency_rating = 'Low'
                            
                            consistency_data = {
                                'rating': consistency_rating,
                                'std': stat_std,
                                'matchup_adjusted': False,
                                'explanation': f'Last {len(recent_stats)} games'
                            }
                            
                            # Enhance reason with matchup info if available
                            enhanced_reason = reason
                            if consistency_data['matchup_adjusted']:
                                enhanced_reason += f" | vs {opponent_team}: {consistency_data['matchup_avg']:.1f} avg in {consistency_data['matchup_games']} games"
                            
                            best_pick = {
                                'player_id': player['id'],
                                'player_name': player['full_name'],
                                'team': player['team_name'],
                                'position': player['position'],
                                'prop_type': self._format_prop_name(prop_type),
                                'line': line,
                                'line_source': 'sportsbook',
                                'bookmaker': prop['bookmaker'],
                                'over_odds': prop['over_odds'],
                                'under_odds': prop['under_odds'],
                                'recommendation': recommendation,
                                'confidence_level': confidence,
                                'reason': enhanced_reason,
                                'player_avg': round(player_avg, 1),
                                'consistency': consistency_data['rating'],
                                'consistency_explanation': consistency_data['explanation'],
                                'matchup_adjusted': consistency_data['matchup_adjusted'],
                                'opponent': opponent_team,
                                'momentum_score': 0.5,
                                'confidence': 0.5
                            }
                    
                    # Add the best pick for this player
                    if best_pick:
                        picks.append(best_pick)
                    
            except Exception as e:
                print(f"Error processing {player_name}: {e}")
                continue
        
        # Sort by recommendation quality
        def sort_key(pick):
            conf_score = {'HIGH': 3, 'MEDIUM': 2, 'LOW': 1, 'PASS': 0}.get(pick['confidence_level'], 0)
            return conf_score
        
        picks.sort(key=sort_key, reverse=True)
        return picks[:limit]
    
    def get_top_betting_picks(self, limit: int = 10, todays_games_only: bool = False) -> List[Dict]:
        """
        Get top betting picks
        
        Args:
            limit: Number of picks to return
            todays_games_only: If True, only return players with real lines (playing today)
        """
        try:
            # If todays_games_only, return picks from real lines cache directly
            if todays_games_only:
                if not self.use_real_lines or not self.real_lines_cache:
                    print("⚠️  No real lines available for today's games")
                    return []
                
                return self._get_picks_from_real_lines(limit)
            
            # Otherwise, get top momentum picks
            # Get latest player value data
            latest_date_response = supabase.table('player_value_index').select('value_date').order('value_date', desc=True).limit(1).execute()
            if not latest_date_response.data:
                return []
            
            latest_date = latest_date_response.data[0]['value_date']
            
            # Get players with high momentum and consistency
            response = supabase.table('player_value_index').select(
                'player_id, value_score, stat_component, momentum_score, confidence_score'
            ).eq('value_date', latest_date).gte('momentum_score', 0.2).gte('confidence_score', 0.3).execute()
            
            picks = []
            for record in response.data:
                # Get player details
                player = supabase.table('players').select('id, full_name, team_name, position').eq('id', record['player_id']).single().execute()
                
                # Get recent stats for analysis
                stats = supabase.table('daily_player_stats').select('points, rebounds, assists, steals, blocks').eq('player_id', record['player_id']).order('game_date', desc=True).limit(10).execute()
                
                if stats.data and len(stats.data) >= 3:
                    import numpy as np
                    
                    # Calculate stats
                    recent_5 = stats.data[:5]
                    recent_10 = stats.data[:10]
                    
                    points_avg_5 = np.mean([g['points'] for g in recent_5])
                    points_avg_10 = np.mean([g['points'] for g in recent_10])
                    points_std = np.std([g['points'] for g in recent_5])
                    
                    # Get real line if available
                    calculated_line = round(points_avg_5 - 1.5, 1)
                    line_info = self._get_line_for_player(
                        player.data['full_name'], 
                        'points', 
                        calculated_line
                    )
                    
                    # If todays_games_only, skip players without real lines
                    if todays_games_only and line_info['source'] != 'sportsbook':
                        continue
                    
                    # Determine recommendation based on our analysis
                    recommendation = None
                    confidence_level = None
                    reason = ""
                    
                    if line_info['source'] == 'sportsbook':
                        # We have a real line - analyze if it's good
                        real_line = line_info['line']
                        
                        # Compare real line to our projection
                        if points_avg_5 > real_line + 2:
                            recommendation = 'OVER'
                            confidence_level = 'HIGH' if points_std < 5 else 'MEDIUM'
                            reason = f'Averaging {points_avg_5:.1f}, line is {real_line} - strong value'
                        elif points_avg_5 > real_line:
                            recommendation = 'OVER'
                            confidence_level = 'MEDIUM'
                            reason = f'Averaging {points_avg_5:.1f}, slight edge over {real_line}'
                        elif points_avg_5 < real_line - 2:
                            recommendation = 'UNDER'
                            confidence_level = 'MEDIUM'
                            reason = f'Averaging {points_avg_5:.1f}, line seems high at {real_line}'
                        else:
                            recommendation = 'PASS'
                            confidence_level = 'LOW'
                            reason = f'Line {real_line} fairly priced (avg: {points_avg_5:.1f})'
                        
                        # Boost confidence if trending up
                        if points_avg_5 > points_avg_10 and recommendation == 'OVER':
                            confidence_level = 'HIGH'
                            reason += ' + trending up'
                    else:
                        # Estimated line - just show momentum
                        recommendation = 'OVER'
                        confidence_level = 'MEDIUM'
                        reason = f'Hot streak with {record["momentum_score"]:.2f} momentum'
                    
                    picks.append({
                        'player_id': record['player_id'],
                        'player_name': player.data['full_name'],
                        'team': player.data['team_name'],
                        'position': player.data['position'],
                        'momentum_score': record['momentum_score'],
                        'confidence': record['confidence_score'],
                        'prop_type': 'Points',
                        'line': line_info['line'],
                        'line_source': line_info['source'],
                        'bookmaker': line_info['bookmaker'],
                        'over_odds': line_info['over_odds'],
                        'under_odds': line_info['under_odds'],
                        'recommendation': recommendation,
                        'confidence_level': confidence_level,
                        'reason': reason,
                        'player_avg': round(points_avg_5, 1),
                        'consistency': 'High' if points_std < 5 else 'Medium' if points_std < 8 else 'Low'
                    })
            
            # Sort by confidence and value
            def sort_key(pick):
                conf_score = {'HIGH': 3, 'MEDIUM': 2, 'LOW': 1}.get(pick['confidence_level'], 0)
                has_real_line = 1 if pick['line_source'] == 'sportsbook' else 0
                return (has_real_line, conf_score, pick['momentum_score'])
            
            picks.sort(key=sort_key, reverse=True)
            return picks[:limit]
            
        except Exception as e:
            print(f"Error getting betting picks: {e}")
            import traceback
            traceback.print_exc()
            return []
