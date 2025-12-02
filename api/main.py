import os
from fastapi import FastAPI, HTTPException
from dotenv import load_dotenv
from supabase import create_client, Client
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import datetime
from typing import List, Optional
from pydantic import BaseModel
import time
from functools import lru_cache

# --- 1. SETUP & CONFIG ---
load_dotenv()
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)
app = FastAPI()

# --- CACHING SETUP ---
# Simple in-memory cache with TTL
_cache = {}
_cache_ttl = {}

def get_cached(key: str, ttl_seconds: int = 300):
    """Get cached value if exists and not expired"""
    current_time = time.time()
    if key in _cache and key in _cache_ttl:
        if current_time - _cache_ttl[key] < ttl_seconds:
            print(f"✅ Cache hit: {key}")
            return _cache[key], True
    return None, False

def set_cache(key: str, value):
    """Set cache value with current timestamp"""
    _cache[key] = value
    _cache_ttl[key] = time.time()
    print(f"💾 Cached: {key}")

# --- 2. CORS MIDDLEWARE ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- ⭐️ 2. DEFINE THE REQUEST MODEL FOR THE NEW ENDPOINT ---
class CompareRequest(BaseModel):
    player_ids: List[str] 

# --- 3. API ENDPOINTS ---
@app.get("/")
def read_root():
    return {"message": "Sportfolio API is running"}

@app.post("/admin/clear-cache")
def clear_cache():
    """Clear all cached data - useful after scraper runs"""
    global _cache, _cache_ttl
    cache_size = len(_cache)
    _cache.clear()
    _cache_ttl.clear()
    return {
        "message": "Cache cleared successfully",
        "items_cleared": cache_size,
        "timestamp": datetime.datetime.now().isoformat()
    }

@app.get("/players")
def get_players():
    try:
        # Check cache first (2 min cache)
        cached_data, hit = get_cached("players", ttl_seconds=120)
        if hit:
            return cached_data
        
        # Fetch from database
        response = supabase.table('players').select(
            'id, full_name, team_name, position, headshot_url, nba_api_id'
        ).execute()
        
        # Cache the result
        set_cache("players", response.data)
        return response.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/featured-players")
def get_featured_players():
    try:
        # Check cache first (2 min cache)
        cached_data, hit = get_cached("featured", ttl_seconds=120)
        if hit:
            return cached_data
        
        # Fetch from database
        response = supabase.rpc('get_featured_players').execute()
        
        # Cache the result
        set_cache("featured", response.data)
        return response.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/player/{player_id}")
def get_player_info(player_id: str):
    try:
        response = supabase.table('players').select('*').eq('id', player_id).single().execute()
        return response.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/player/{player_id}/value_history")
def get_player_value_history(player_id: str):
    try:
        response = supabase.table('player_value_index').select(
            'value_date, value_score, stat_component, sentiment_component, momentum_score, confidence_score'
        ).eq('player_id', player_id).order('value_date').execute()
        return response.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/player/{player_id}/stats")
def get_player_stats(player_id: str):
    try:
        response = supabase.table('daily_player_stats').select('*').eq('player_id', player_id).order('game_date', desc=True).limit(5).execute()
        return response.data if response.data else []
    except Exception as e:
        # Return empty array instead of error for missing data
        return []

@app.get("/player/{player_id}/season_stats")
def get_player_season_stats(player_id: str):
    try:
        response = supabase.table('player_season_stats') \
            .select('*') \
            .eq('player_id', player_id) \
            .order('season', desc=True) \
            .limit(1) \
            .maybe_single() \
            .execute()
        # Return null if no data, don't throw error
        return response.data if response.data else None
    except Exception as e:
        # Return null instead of error for missing data
        return None

@app.get("/player/{player_id}/news")
def get_player_news(player_id: str):
    try:
        response = supabase.table('daily_player_sentiment').select(
            'article_date, headline_text, sentiment_score, source, url'
        ).eq('player_id', player_id).order('article_date', desc=True).limit(10).execute()
        return response.data if response.data else []
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/player/{player_id}/sentiment_breakdown")
def get_player_sentiment_breakdown(player_id: str):
    """Get sentiment breakdown by source for a player"""
    try:
        # Get recent sentiment data
        response = supabase.table('daily_player_sentiment').select(
            'sentiment_score, source'
        ).eq('player_id', player_id).execute()
        
        if not response.data:
            return {"total_mentions": 0, "by_source": {}, "avg_sentiment": 0}
        
        # Group by source
        by_source = {}
        total_sentiment = 0
        
        for item in response.data:
            source = item.get('source', 'unknown')
            score = item['sentiment_score']
            
            if source not in by_source:
                by_source[source] = {
                    "count": 0,
                    "avg_sentiment": 0,
                    "total": 0
                }
            
            by_source[source]["count"] += 1
            by_source[source]["total"] += score
            total_sentiment += score
        
        # Calculate averages
        for source in by_source:
            by_source[source]["avg_sentiment"] = by_source[source]["total"] / by_source[source]["count"]
            del by_source[source]["total"]
        
        return {
            "total_mentions": len(response.data),
            "by_source": by_source,
            "avg_sentiment": total_sentiment / len(response.data) if response.data else 0
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/player/{player_id}/enhanced_metrics")
def get_player_enhanced_metrics(player_id: str):
    """Get the latest enhanced metrics for a player"""
    try:
        response = supabase.table('player_value_index').select(
            'value_date, value_score, stat_component, sentiment_component, momentum_score, confidence_score'
        ).eq('player_id', player_id).order('value_date', desc=True).limit(1).maybe_single().execute()
        
        if not response.data:
            return None
        
        # Add momentum status
        momentum = response.data.get('momentum_score', 0)
        if momentum > 0.5:
            status = "🔥 Hot"
        elif momentum > 0.2:
            status = "📈 Rising"
        elif momentum > -0.2:
            status = "➡️ Stable"
        elif momentum > -0.5:
            status = "📉 Falling"
        else:
            status = "🧊 Cold"
        
        response.data['momentum_status'] = status
        
        # Add confidence level
        confidence = response.data.get('confidence_score', 0)
        if confidence > 0.7:
            confidence_level = "High"
        elif confidence > 0.4:
            confidence_level = "Medium"
        else:
            confidence_level = "Low"
        
        response.data['confidence_level'] = confidence_level
        
        return response.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/market-movers")
def get_market_movers():
    try:
        # Check cache (2 min cache)
        cached_data, hit = get_cached("market_movers", ttl_seconds=120)
        if hit:
            return cached_data
        
        response = supabase.rpc('get_market_movers').execute()
        all_movers = response.data
        all_movers.sort(key=lambda x: x['value_change'], reverse=True)
        risers = all_movers[:5]
        fallers = all_movers[-5:]
        fallers.reverse()
        result = {"risers": risers, "fallers": fallers}
        
        # Cache result
        set_cache("market_movers", result)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- ⭐️ 3. THIS IS THE NEW, WORKING ENDPOINT ---
@app.post("/players/compare")
def get_compare_data(request: CompareRequest):
    """
    Fetches all data needed for a side-by-side comparison
    for a list of player_ids.
    """
    try:
        player_ids = request.player_ids
        
        info_res = supabase.table('players').select('*').in_('id', player_ids).execute()
        
        stats_res = supabase.table('player_season_stats') \
            .select('*').in_('player_id', player_ids) \
            .order('season', desc=True) \
            .execute()
            
        value_res = supabase.table('player_value_index') \
            .select('*') \
            .in_('player_id', player_ids).order('value_date').execute()

        player_data = {}
        for player in info_res.data:
            player_data[player['id']] = {
                "info": player,
                "season_stats": None, 
                "value_history": [] 
            }
        
        for stats in stats_res.data:
            player_id = stats['player_id']
            if player_id in player_data:
                if player_data[player_id]['season_stats'] is None:
                     player_data[player_id]['season_stats'] = stats
        
        for value in value_res.data:
            player_id = value['player_id']
            if player_id in player_data:
                player_data[player_id]['value_history'].append({
                    "value_date": value['value_date'],
                    "value_score": value['value_score']
                })
        
        return player_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- AI TRADE ADVISOR ENDPOINTS ---

@app.get("/ai/buy-opportunities")
def get_buy_opportunities(limit: int = 10):
    """Get AI-recommended buy opportunities (undervalued players)"""
    try:
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), '../scraper'))
        from ai_trade_advisor import AITradeAdvisor
        
        advisor = AITradeAdvisor()
        opportunities = advisor.find_buy_opportunities(limit)
        
        return {
            "count": len(opportunities),
            "opportunities": opportunities,
            "description": "Players with strong stats but negative sentiment - potential buy low opportunities"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/ai/sell-opportunities")
def get_sell_opportunities(limit: int = 10):
    """Get AI-recommended sell opportunities (overvalued players)"""
    try:
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), '../scraper'))
        from ai_trade_advisor import AITradeAdvisor
        
        advisor = AITradeAdvisor()
        opportunities = advisor.find_sell_opportunities(limit)
        
        return {
            "count": len(opportunities),
            "opportunities": opportunities,
            "description": "Players with high sentiment but weak stats - potential sell high opportunities"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/ai/breakout-candidates")
def get_breakout_candidates(limit: int = 10):
    """Get AI-identified breakout candidates"""
    try:
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), '../scraper'))
        from ai_trade_advisor import AITradeAdvisor
        
        advisor = AITradeAdvisor()
        candidates = advisor.find_breakout_candidates(limit)
        
        return {
            "count": len(candidates),
            "candidates": candidates,
            "description": "Players with positive momentum and rising sentiment - watch for breakouts"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ai/portfolio-analysis")
def analyze_portfolio(request: CompareRequest):
    """Analyze risk and performance of a portfolio of players"""
    try:
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), '../scraper'))
        from ai_trade_advisor import AITradeAdvisor
        
        advisor = AITradeAdvisor()
        analysis = advisor.analyze_portfolio_risk(request.player_ids)
        
        return analysis
    except Exception as e:
        # Return a friendly error message instead of crashing
        return {
            "error": "insufficient_data",
            "message": "Portfolio analysis requires recent player data. Please run the scraper to populate the database.",
            "risk_level": "Unknown",
            "risk_score": 0,
            "players": [],
            "recommendations": [
                "Run the scraper to get the latest player data: cd scraper && bash run_enhanced.sh",
                "Portfolio analysis will be available once data is populated"
            ]
        }

@app.get("/ai/daily-insights")
def get_daily_insights():
    """Get comprehensive daily AI insights"""
    try:
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), '../scraper'))
        from ai_trade_advisor import AITradeAdvisor
        
        advisor = AITradeAdvisor()
        
        buy_ops = advisor.find_buy_opportunities(5)
        sell_ops = advisor.find_sell_opportunities(5)
        breakouts = advisor.find_breakout_candidates(5)
        
        # Try to get ML recommendations
        ml_recommendations = []
        try:
            from ml_trade_advisor import MLTradeAdvisor
            ml_advisor = MLTradeAdvisor()
            ml_recommendations = ml_advisor.get_ml_recommendations(5)
        except Exception as e:
            print(f"ML recommendations unavailable: {e}")
        
        return {
            "generated_at": datetime.datetime.now().isoformat(),
            "buy_opportunities": {
                "count": len(buy_ops),
                "players": buy_ops
            },
            "sell_opportunities": {
                "count": len(sell_ops),
                "players": sell_ops
            },
            "breakout_candidates": {
                "count": len(breakouts),
                "players": breakouts
            },
            "ml_recommendations": {
                "count": len(ml_recommendations),
                "players": ml_recommendations
            },
            "summary": {
                "total_opportunities": len(buy_ops) + len(sell_ops),
                "high_urgency_buys": sum(1 for o in buy_ops if o['urgency'] == 'high'),
                "high_urgency_sells": sum(1 for o in sell_ops if o['urgency'] == 'high'),
                "high_potential_breakouts": sum(1 for b in breakouts if b['potential'] == 'high')
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- AI PRICE PREDICTION ENDPOINTS ---

@app.get("/ai/predict/{player_id}")
def predict_player_price(player_id: str, days: int = 7):
    """Predict future price for a specific player"""
    try:
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), '../scraper'))
        from ai_price_predictor import AIPricePredictor
        
        predictor = AIPricePredictor()
        predictions = predictor.predict_future_value(player_id, days_ahead=days)
        momentum = predictor.get_price_momentum(player_id)
        
        if not predictions:
            return {
                "error": "Insufficient data for prediction",
                "message": "Need at least 5 days of historical data"
            }
        
        return {
            "player_id": player_id,
            "predictions": predictions,
            "momentum": momentum,
            "prediction_horizon": f"{days} days",
            "generated_at": datetime.datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/ai/trending-players")
def get_trending_players(limit: int = 10):
    """Get players with strong upward price trends"""
    try:
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), '../scraper'))
        from ai_price_predictor import AIPricePredictor
        
        predictor = AIPricePredictor()
        trending = predictor.find_trending_players(limit)
        
        return {
            "count": len(trending),
            "players": trending,
            "description": "Players with strong upward price momentum and positive predictions"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/ai/value-drops")
def get_value_drops(limit: int = 10):
    """Get players with recent value drops (potential recovery plays)"""
    try:
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), '../scraper'))
        from ai_price_predictor import AIPricePredictor
        
        predictor = AIPricePredictor()
        drops = predictor.find_value_drops(limit)
        
        return {
            "count": len(drops),
            "players": drops,
            "description": "Players with recent value drops that may recover"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/ai/price-forecast")
def get_price_forecast():
    """Get comprehensive price forecast report"""
    try:
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), '../scraper'))
        from ai_price_predictor import AIPricePredictor
        
        predictor = AIPricePredictor()
        
        trending = predictor.find_trending_players(5)
        drops = predictor.find_value_drops(5)
        
        return {
            "generated_at": datetime.datetime.now().isoformat(),
            "trending_players": {
                "count": len(trending),
                "players": trending
            },
            "value_drops": {
                "count": len(drops),
                "players": drops
            },
            "summary": {
                "total_predictions": len(trending) + len(drops),
                "strong_buy_signals": sum(1 for d in drops if d.get('buy_signal', False)),
                "high_confidence_predictions": sum(1 for t in trending if t.get('prediction_confidence', 0) > 0.7)
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- LIVE SCORES ENDPOINTS ---

@app.get("/live/scores")
def get_live_scores(date: str = None):
    """Get live scores for a specific date (defaults to today)"""
    try:
        # Parse date
        if date:
            try:
                target_date = datetime.datetime.strptime(date, '%Y-%m-%d').date()
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
        else:
            target_date = datetime.date.today()
        
        # Check cache (shorter TTL for live data)
        cache_key = f"live_scores_{target_date.isoformat()}"
        cached_data, hit = get_cached(cache_key, ttl_seconds=60)  # 1 minute cache
        if hit:
            return cached_data
        
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), '../scraper'))
        from live_scores import LiveScores
        
        live = LiveScores()
        games = live.get_games_by_date(target_date)
        
        result = {
            "date": target_date.isoformat(),
            "games_count": len(games),
            "games": games,
            "live_games": [g for g in games if g['is_live']],
            "completed_games": [g for g in games if g['is_final']],
            "upcoming_games": [g for g in games if not g['is_live'] and not g['is_final']]
        }
        
        # Cache result
        set_cache(cache_key, result)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/live/game/{game_id}")
def get_live_game(game_id: str):
    """Get live box score for a specific game (from API or database)"""
    try:
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), '../scraper'))
        from live_scores import LiveScores
        
        live = LiveScores()
        box_score = live.get_live_box_score(game_id, save_to_db=True)
        
        if not box_score:
            raise HTTPException(status_code=404, detail="Game not found or no data available")
        
        return box_score
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/live/top-performers")
def get_top_performers():
    """Get top performers from today's games"""
    try:
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), '../scraper'))
        from live_scores import LiveScores
        
        live = LiveScores()
        performers = live.get_top_performers()
        
        return {
            "date": datetime.date.today().isoformat(),
            "count": len(performers),
            "performers": performers
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- CHATBOT ENDPOINT ---

class ChatRequest(BaseModel):
    message: str
    history: List[dict] = []

@app.post("/chat")
def chat_with_assistant(request: ChatRequest):
    """Chat with NBA assistant powered by Gemini AI with real-time data"""
    try:
        import google.generativeai as genai
        
        # Configure Gemini API
        genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
        
        # Create model (using Gemini 2.5 Flash)
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        # Fetch real-time data from database
        today = datetime.date.today().isoformat()
        
        # Get featured players
        featured_response = supabase.rpc('get_featured_players').execute()
        featured_players = featured_response.data[:5] if featured_response.data else []
        
        # Get market movers
        movers_response = supabase.rpc('get_market_movers').execute()
        market_movers = movers_response.data if movers_response.data else []
        
        # Get today's live scores
        try:
            import sys
            sys.path.append(os.path.join(os.path.dirname(__file__), '../scraper'))
            from live_scores import LiveScores
            live = LiveScores()
            games = live.get_todays_games()
            live_summary = f"{len(games)} games today" if games else "No games today"
        except:
            live_summary = "Live scores unavailable"
        
        # Build enhanced context
        context = f"""You are an NBA expert assistant for a sports trading platform called Sportfolio. 
You help users analyze NBA players, develop trading strategies, and make informed decisions.

CURRENT DATA (as of {today}):

Featured Players (Top Value):
"""
        for i, player in enumerate(featured_players[:5], 1):
            context += f"{i}. {player.get('full_name', 'Unknown')} - Value: {player.get('latest_value', 0):.1f}, "
            context += f"Momentum: {player.get('momentum_status', 'N/A')}\n"
        
        context += f"\nMarket Activity:\n"
        if market_movers:
            risers = [m for m in market_movers if m.get('value_change', 0) > 0][:3]
            fallers = [m for m in market_movers if m.get('value_change', 0) < 0][:3]
            
            if risers:
                context += "Top Risers: " + ", ".join([f"{m.get('full_name')} (+{m.get('value_change', 0):.1f})" for m in risers]) + "\n"
            if fallers:
                context += "Top Fallers: " + ", ".join([f"{m.get('full_name')} ({m.get('value_change', 0):.1f})" for m in fallers]) + "\n"
        
        context += f"\nLive Games: {live_summary}\n"
        
        context += """
PLATFORM FEATURES:
- Watchlist: Users can save favorite players
- Trade Simulator: Build and analyze portfolios
- AI Insights: Buy/sell recommendations, breakout candidates
- Live Scores: Real-time NBA game data
- Value Index: Player value scores based on stats + sentiment

GUIDELINES:
- Provide specific, actionable advice
- Reference actual player data when available
- Suggest using platform features (watchlist, simulator, etc.)
- Keep responses concise (2-3 paragraphs max)
- Use trading terminology (buy low, sell high, momentum, etc.)

"""
        
        # Add conversation history
        for msg in request.history[-6:]:
            role = "User" if msg['role'] == 'user' else "Assistant"
            context += f"{role}: {msg['content']}\n"
        
        # Add current message
        context += f"User: {request.message}\nAssistant:"
        
        # Generate response
        response = model.generate_content(context)
        
        return {
            "response": response.text,
            "success": True
        }
        
    except Exception as e:
        print(f"Chat error: {e}")
        import traceback
        traceback.print_exc()
        return {
            "response": "I'm having trouble connecting right now. Please try again in a moment.",
            "success": False,
            "error": str(e)
        }

# --- BETTING ADVISOR ENDPOINTS ---

# Cache for betting picks (2 minute TTL)
_betting_picks_cache = {
    'data': None,
    'timestamp': None,
    'ttl': 120  # 2 minutes
}

@app.get("/betting/picks")
def get_betting_picks(todays_games: bool = True, force_refresh: bool = False):
    """
    Get top betting picks (with caching for faster loads)
    
    Parameters:
    - todays_games: If True (default), show only players in today's games with real sportsbook lines
                    If False, show top momentum picks with estimated lines
    - force_refresh: If True, bypass cache and fetch fresh data
    """
    try:
        import sys
        import os
        import time
        
        # Check cache first (unless force_refresh) - 2 min cache
        if not force_refresh and _betting_picks_cache['data'] is not None:
            cache_age = time.time() - _betting_picks_cache['timestamp']
            if cache_age < 120:  # 2 minutes instead of 5
                print(f"✅ Serving cached betting picks (age: {cache_age:.0f}s)")
                return _betting_picks_cache['data']
        
        print("🔄 Fetching fresh betting picks...")
        sys.path.append(os.path.join(os.path.dirname(__file__), '../scraper'))
        from betting_advisor import BettingAdvisor
        
        # Always try to use real lines
        advisor = BettingAdvisor(use_real_lines=True)
        picks = advisor.get_top_betting_picks(limit=20, todays_games_only=todays_games)
        
        # Count how many have real lines
        real_line_count = sum(1 for p in picks if p.get('line_source') == 'sportsbook')
        
        result = {
            "generated_at": datetime.datetime.now().isoformat(),
            "picks": picks,
            "todays_games_only": todays_games,
            "real_lines_available": real_line_count,
            "total_picks": len(picks),
            "cached": False
        }
        
        # Update cache
        _betting_picks_cache['data'] = result
        _betting_picks_cache['timestamp'] = time.time()
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/betting/player/{player_id}")
def get_player_betting_props(player_id: str, use_real_lines: bool = False):
    """
    Get betting prop insights for specific player
    
    Parameters:
    - player_id: The player's ID
    - use_real_lines: If True, fetch real lines from The Odds API (requires ODDS_API_KEY)
                      If False, use calculated lines from player averages (default)
    """
    try:
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), '../scraper'))
        from betting_advisor import BettingAdvisor
        
        advisor = BettingAdvisor(use_real_lines=use_real_lines)
        insights = advisor.get_player_prop_insights(player_id)
        insights['using_real_lines'] = use_real_lines
        
        return insights
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- FANTASY OPTIMIZER ENDPOINTS ---

@app.get("/fantasy/lineup")
def get_fantasy_lineup():
    """Get optimal fantasy lineup"""
    try:
        # Check cache (2 min cache)
        cached_data, hit = get_cached("fantasy_lineup", ttl_seconds=120)
        if hit:
            return cached_data
        
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), '../scraper'))
        from fantasy_optimizer import FantasyOptimizer
        
        optimizer = FantasyOptimizer()
        lineup = optimizer.get_optimal_lineup(limit=10)
        
        result = {
            "generated_at": datetime.datetime.now().isoformat(),
            "lineup": lineup
        }
        
        # Cache result
        set_cache("fantasy_lineup", result)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/fantasy/value-picks")
def get_fantasy_value_picks():
    """Get best fantasy value picks"""
    try:
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), '../scraper'))
        from fantasy_optimizer import FantasyOptimizer
        
        optimizer = FantasyOptimizer()
        picks = optimizer.get_value_picks(10)
        
        return {
            "generated_at": datetime.datetime.now().isoformat(),
            "value_picks": picks
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
