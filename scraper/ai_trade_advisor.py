"""
AI Trade Advisor - Provides intelligent trade recommendations and insights
"""
import os
from dotenv import load_dotenv
from supabase import create_client, Client
import datetime
import numpy as np
from typing import List, Dict, Tuple

load_dotenv()
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

class AITradeAdvisor:
    """AI-powered trade recommendations and portfolio analysis"""
    
    def __init__(self):
        self.today = datetime.date.today().isoformat()
        self.yesterday = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()
        self.week_ago = (datetime.date.today() - datetime.timedelta(days=7)).isoformat()
    
    def get_player_data(self, player_id: str = None) -> List[Dict]:
        """Get comprehensive player data"""
        try:
            query = supabase.table('player_value_index').select(
                'player_id, value_date, value_score, stat_component, '
                'sentiment_component, momentum_score, confidence_score'
            )
            
            if player_id:
                query = query.eq('player_id', player_id)
            
            query = query.gte('value_date', self.week_ago).order('value_date', desc=True)
            
            response = query.execute()
            return response.data
        except Exception as e:
            print(f"Error fetching player data: {e}")
            return []
    
    def calculate_value_trend(self, player_id: str) -> Tuple[float, str]:
        """Calculate value trend over last 7 days"""
        data = self.get_player_data(player_id)
        
        if len(data) < 2:
            return 0.0, "insufficient_data"
        
        # Get today's and week ago values
        values = [d['value_score'] for d in data]
        
        if len(values) >= 7:
            recent_avg = np.mean(values[:3])
            older_avg = np.mean(values[-3:])
            trend = ((recent_avg - older_avg) / older_avg) * 100 if older_avg > 0 else 0
        else:
            trend = ((values[0] - values[-1]) / values[-1]) * 100 if values[-1] > 0 else 0
        
        # Classify trend
        if trend > 5:
            classification = "rising_fast"
        elif trend > 2:
            classification = "rising"
        elif trend < -5:
            classification = "falling_fast"
        elif trend < -2:
            classification = "falling"
        else:
            classification = "stable"
        
        return trend, classification
    
    def find_buy_opportunities(self, limit: int = 10) -> List[Dict]:
        """Find undervalued players (buy low opportunities)"""
        print("\n🔍 Finding Buy Opportunities...")
        
        try:
            # Get latest value data with player info
            response = supabase.table('player_value_index').select(
                'player_id, value_score, stat_component, sentiment_component, '
                'momentum_score, confidence_score'
            ).eq('value_date', self.today).execute()
            
            opportunities = []
            
            for record in response.data:
                stat = record['stat_component']
                sentiment = record['sentiment_component']
                confidence = record['confidence_score']
                
                # Buy signal: High stats, low/negative sentiment, decent confidence
                if stat > 30 and sentiment < 0 and confidence > 0.3:
                    # Get player name
                    player = supabase.table('players').select('full_name, team_name, position').eq('id', record['player_id']).single().execute()
                    
                    # Calculate opportunity score
                    opportunity_score = (stat * 0.6) + (abs(sentiment) * 30 * 0.3) + (confidence * 10)
                    
                    trend, trend_class = self.calculate_value_trend(record['player_id'])
                    
                    opportunities.append({
                        'player_id': record['player_id'],
                        'player_name': player.data['full_name'],
                        'team': player.data['team_name'],
                        'position': player.data['position'],
                        'value_score': record['value_score'],
                        'stat_component': stat,
                        'sentiment_component': sentiment,
                        'confidence': confidence,
                        'opportunity_score': opportunity_score,
                        'trend': trend,
                        'trend_class': trend_class,
                        'reason': f"Strong stats ({stat:.1f}) but negative sentiment ({sentiment:.2f}). Market undervaluing performance.",
                        'action': 'BUY',
                        'urgency': 'high' if confidence > 0.5 else 'medium'
                    })
            
            # Sort by opportunity score
            opportunities.sort(key=lambda x: x['opportunity_score'], reverse=True)
            
            return opportunities[:limit]
            
        except Exception as e:
            print(f"Error finding buy opportunities: {e}")
            return []
    
    def find_sell_opportunities(self, limit: int = 10) -> List[Dict]:
        """Find overvalued players (sell high opportunities)"""
        print("\n🔍 Finding Sell Opportunities...")
        
        try:
            response = supabase.table('player_value_index').select(
                'player_id, value_score, stat_component, sentiment_component, '
                'momentum_score, confidence_score'
            ).eq('value_date', self.today).execute()
            
            opportunities = []
            
            for record in response.data:
                stat = record['stat_component']
                sentiment = record['sentiment_component']
                confidence = record['confidence_score']
                
                # Sell signal: Low stats, high sentiment, decent confidence
                if stat < 30 and sentiment > 0.3 and confidence > 0.3:
                    player = supabase.table('players').select('full_name, team_name, position').eq('id', record['player_id']).single().execute()
                    
                    # Calculate risk score
                    risk_score = (sentiment * 50) - (stat * 0.5) + (confidence * 10)
                    
                    trend, trend_class = self.calculate_value_trend(record['player_id'])
                    
                    opportunities.append({
                        'player_id': record['player_id'],
                        'player_name': player.data['full_name'],
                        'team': player.data['team_name'],
                        'position': player.data['position'],
                        'value_score': record['value_score'],
                        'stat_component': stat,
                        'sentiment_component': sentiment,
                        'confidence': confidence,
                        'risk_score': risk_score,
                        'trend': trend,
                        'trend_class': trend_class,
                        'reason': f"High sentiment ({sentiment:.2f}) but weak stats ({stat:.1f}). Market overvaluing hype.",
                        'action': 'SELL',
                        'urgency': 'high' if trend < -2 else 'medium'
                    })
            
            opportunities.sort(key=lambda x: x['risk_score'], reverse=True)
            
            return opportunities[:limit]
            
        except Exception as e:
            print(f"Error finding sell opportunities: {e}")
            return []
    
    def find_breakout_candidates(self, limit: int = 10) -> List[Dict]:
        """Find players likely to break out (rising momentum + positive sentiment)"""
        print("\n🚀 Finding Breakout Candidates...")
        
        try:
            response = supabase.table('player_value_index').select(
                'player_id, value_score, stat_component, sentiment_component, '
                'momentum_score, confidence_score'
            ).eq('value_date', self.today).execute()
            
            candidates = []
            
            for record in response.data:
                momentum = record['momentum_score']
                sentiment = record['sentiment_component']
                stat = record['stat_component']
                confidence = record['confidence_score']
                
                # Breakout signal: Positive momentum, rising sentiment, improving stats
                if momentum > 0.2 and sentiment > 0 and stat > 20:
                    player = supabase.table('players').select('full_name, team_name, position').eq('id', record['player_id']).single().execute()
                    
                    breakout_score = (momentum * 50) + (sentiment * 30) + (stat * 0.3) + (confidence * 10)
                    
                    trend, trend_class = self.calculate_value_trend(record['player_id'])
                    
                    candidates.append({
                        'player_id': record['player_id'],
                        'player_name': player.data['full_name'],
                        'team': player.data['team_name'],
                        'position': player.data['position'],
                        'value_score': record['value_score'],
                        'momentum_score': momentum,
                        'sentiment_component': sentiment,
                        'stat_component': stat,
                        'confidence': confidence,
                        'breakout_score': breakout_score,
                        'trend': trend,
                        'trend_class': trend_class,
                        'reason': f"Strong momentum ({momentum:.2f}) with positive sentiment. Stats trending up.",
                        'action': 'WATCH',
                        'potential': 'high' if breakout_score > 50 else 'medium'
                    })
            
            candidates.sort(key=lambda x: x['breakout_score'], reverse=True)
            
            return candidates[:limit]
            
        except Exception as e:
            print(f"Error finding breakout candidates: {e}")
            return []
    
    def analyze_portfolio_risk(self, player_ids: List[str]) -> Dict:
        """Analyze risk of a portfolio of players"""
        print(f"\n📊 Analyzing Portfolio Risk for {len(player_ids)} players...")
        
        try:
            portfolio_data = []
            
            for player_id in player_ids:
                response = supabase.table('player_value_index').select(
                    'value_score, stat_component, sentiment_component, '
                    'momentum_score, confidence_score'
                ).eq('player_id', player_id).eq('value_date', self.today).single().execute()
                
                if response.data:
                    player = supabase.table('players').select('full_name').eq('id', player_id).single().execute()
                    trend, trend_class = self.calculate_value_trend(player_id)
                    
                    portfolio_data.append({
                        'player_id': player_id,
                        'player_name': player.data['full_name'],
                        'value_score': response.data['value_score'],
                        'confidence': response.data['confidence_score'],
                        'momentum': response.data['momentum_score'],
                        'trend': trend,
                        'trend_class': trend_class
                    })
            
            if not portfolio_data:
                return {'error': 'No data found for portfolio'}
            
            # Calculate portfolio metrics
            avg_value = np.mean([p['value_score'] for p in portfolio_data])
            avg_confidence = np.mean([p['confidence'] for p in portfolio_data])
            avg_momentum = np.mean([p['momentum'] for p in portfolio_data])
            
            # Risk assessment based on multiple factors (mutually exclusive)
            high_risk_players = []
            medium_risk_players = []
            low_risk_players = []
            
            for p in portfolio_data:
                # High Risk: Steep decline OR very low value
                if p['trend'] < -20 or p['value_score'] < 30:
                    high_risk_players.append(p)
                # Medium Risk: Moderate decline OR moderate value (but not high risk)
                elif (-20 <= p['trend'] < -5) or (30 <= p['value_score'] < 50):
                    medium_risk_players.append(p)
                # Low Risk: Stable/rising AND good value
                else:
                    low_risk_players.append(p)
            
            high_risk = len(high_risk_players)
            medium_risk = len(medium_risk_players)
            low_risk = len(low_risk_players)
            
            # Diversification score (0-100)
            value_std = np.std([p['value_score'] for p in portfolio_data])
            diversification = min(100, (value_std / avg_value) * 100) if avg_value > 0 else 0
            
            # Calculate average trend
            avg_trend = np.mean([p['trend'] for p in portfolio_data])
            
            # Overall risk score (0-100, higher is riskier)
            risk_score = 0
            
            # Factor 1: Proportion of risky players (0-40 points)
            risk_score += (high_risk / len(portfolio_data)) * 40
            risk_score += (medium_risk / len(portfolio_data)) * 20
            
            # Factor 2: Average value score (0-30 points, inverse)
            if avg_value < 40:
                risk_score += 30
            elif avg_value < 60:
                risk_score += 15
            
            # Factor 3: Average trend (0-30 points)
            if avg_trend < -10:
                risk_score += 30
            elif avg_trend < -5:
                risk_score += 20
            elif avg_trend < 0:
                risk_score += 10
            
            # Add individual risk classification to each player
            for p in portfolio_data:
                if p['trend'] < -20 or p['value_score'] < 30:
                    p['individual_risk'] = 'High'
                elif (-20 <= p['trend'] < -5) or (30 <= p['value_score'] < 50):
                    p['individual_risk'] = 'Medium'
                else:
                    p['individual_risk'] = 'Low'
            
            return {
                'portfolio_size': len(portfolio_data),
                'avg_value_score': round(avg_value, 2),
                'avg_confidence': round(avg_confidence, 3),
                'avg_momentum': round(avg_momentum, 3),
                'risk_score': round(risk_score, 2),
                'risk_level': 'High' if risk_score > 40 else 'Medium' if risk_score > 20 else 'Low',
                'avg_trend': round(avg_trend, 2),
                'diversification_score': round(diversification, 1),
                'high_risk_players': high_risk,
                'medium_risk_players': medium_risk,
                'low_risk_players': low_risk,
                'players': portfolio_data,
                'recommendations': self._generate_portfolio_recommendations(portfolio_data, risk_score)
            }
            
        except Exception as e:
            print(f"Error analyzing portfolio: {e}")
            return {'error': str(e)}
    
    def _generate_portfolio_recommendations(self, portfolio_data: List[Dict], risk_score: float) -> List[str]:
        """Generate actionable recommendations for portfolio"""
        recommendations = []
        
        # Analyze value scores
        low_value = [p for p in portfolio_data if p['value_score'] < 40]
        high_value = [p for p in portfolio_data if p['value_score'] >= 70]
        
        # Analyze trends
        steep_decline = [p for p in portfolio_data if p['trend'] < -20]
        declining = [p for p in portfolio_data if -20 <= p['trend'] < -5]
        rising = [p for p in portfolio_data if p['trend'] > 10]
        
        # Generate recommendations based on analysis
        if steep_decline:
            recommendations.append(f"⚠️ {len(steep_decline)} player(s) declining rapidly (>20%): {', '.join([p['player_name'] for p in steep_decline[:3]])}. Consider selling.")
        
        if declining:
            recommendations.append(f"📉 {len(declining)} player(s) showing negative trends: {', '.join([p['player_name'] for p in declining[:3]])}. Monitor closely.")
        
        if low_value:
            recommendations.append(f"⬇️ {len(low_value)} player(s) have low value scores (<40): {', '.join([p['player_name'] for p in low_value[:3]])}. High risk.")
        
        if rising:
            recommendations.append(f"📈 {len(rising)} player(s) rising fast: {', '.join([p['player_name'] for p in rising[:3]])}. Good holds.")
        
        if high_value:
            recommendations.append(f"⭐ {len(high_value)} player(s) have strong value scores (>70): {', '.join([p['player_name'] for p in high_value[:3]])}. Core assets.")
        
        # Overall assessment
        if risk_score > 40:
            recommendations.append("🔴 Overall: High risk portfolio. Consider rebalancing with more stable players.")
        elif risk_score > 20:
            recommendations.append("🟡 Overall: Medium risk portfolio. Some concerns but manageable.")
        else:
            recommendations.append("🟢 Overall: Low risk portfolio. Well-balanced with strong fundamentals.")
        
        return recommendations

def generate_daily_insights():
    """Generate daily AI insights"""
    print("="*60)
    print("AI TRADE ADVISOR - DAILY INSIGHTS")
    print("="*60)
    
    advisor = AITradeAdvisor()
    
    # Buy opportunities
    buy_ops = advisor.find_buy_opportunities(5)
    print(f"\n💰 TOP 5 BUY OPPORTUNITIES (Undervalued)")
    print("-"*60)
    for i, opp in enumerate(buy_ops, 1):
        print(f"{i}. {opp['player_name']} ({opp['team']}) - {opp['position']}")
        print(f"   Value: {opp['value_score']:.1f} | Stats: {opp['stat_component']:.1f} | Sentiment: {opp['sentiment_component']:.2f}")
        print(f"   💡 {opp['reason']}")
        print(f"   🎯 Urgency: {opp['urgency'].upper()}")
        print()
    
    # Sell opportunities
    sell_ops = advisor.find_sell_opportunities(5)
    print(f"\n💸 TOP 5 SELL OPPORTUNITIES (Overvalued)")
    print("-"*60)
    for i, opp in enumerate(sell_ops, 1):
        print(f"{i}. {opp['player_name']} ({opp['team']}) - {opp['position']}")
        print(f"   Value: {opp['value_score']:.1f} | Stats: {opp['stat_component']:.1f} | Sentiment: {opp['sentiment_component']:.2f}")
        print(f"   💡 {opp['reason']}")
        print(f"   ⚠️ Urgency: {opp['urgency'].upper()}")
        print()
    
    # Breakout candidates
    breakouts = advisor.find_breakout_candidates(5)
    print(f"\n🚀 TOP 5 BREAKOUT CANDIDATES")
    print("-"*60)
    for i, player in enumerate(breakouts, 1):
        print(f"{i}. {player['player_name']} ({player['team']}) - {player['position']}")
        print(f"   Value: {player['value_score']:.1f} | Momentum: {player['momentum_score']:.2f} | Trend: {player['trend']:+.1f}%")
        print(f"   💡 {player['reason']}")
        print(f"   ⭐ Potential: {player['potential'].upper()}")
        print()
    
    print("="*60)
    print("Run complete! Insights generated.")
    print("="*60)

if __name__ == "__main__":
    generate_daily_insights()
