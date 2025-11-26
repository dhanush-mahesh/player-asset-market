"""
ML-Powered Trade Advisor - Uses machine learning to predict profitable trades
"""
import os
from dotenv import load_dotenv
from supabase import create_client, Client
import datetime
import numpy as np
import pandas as pd
from typing import List, Dict
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
import pickle
import warnings
warnings.filterwarnings('ignore')

load_dotenv()
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

class MLTradeAdvisor:
    """Machine Learning-powered trade recommendations"""
    
    def __init__(self):
        self.model = None
        # Use absolute path relative to this file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.model_path = os.path.join(current_dir, 'ml_trade_model.pkl')
        self.feature_names = [
            'stat_component', 'sentiment_component', 'momentum_score',
            'confidence_score', 'value_score', 'stat_trend', 'sentiment_trend'
        ]
        print(f"🔍 Looking for model at: {self.model_path}")
        
    def generate_training_data(self, lookback_days: int = 7) -> pd.DataFrame:
        """
        Generate training data by looking at historical value changes.
        Label: 1 if value increased by >5% in next 7 days, 0 otherwise
        """
        print("\n📊 Generating training data from historical player values...")
        
        # Get all historical data
        response = supabase.table('player_value_index').select(
            'player_id, value_date, value_score, stat_component, '
            'sentiment_component, momentum_score, confidence_score'
        ).order('player_id').order('value_date').execute()
        
        if not response.data or len(response.data) < 100:
            print("❌ Not enough historical data. Need at least 100 records.")
            return None
        
        # Convert to DataFrame
        df = pd.DataFrame(response.data)
        df['value_date'] = pd.to_datetime(df['value_date'])
        
        training_samples = []
        
        # Group by player
        for player_id, player_data in df.groupby('player_id'):
            player_data = player_data.sort_values('value_date')
            
            # Need at least 2 data points
            if len(player_data) < 2:
                continue
            
            # For each date except the last few
            for i in range(len(player_data) - lookback_days):
                current = player_data.iloc[i]
                
                # Look ahead 7 days (or closest available)
                future_idx = min(i + lookback_days, len(player_data) - 1)
                future = player_data.iloc[future_idx]
                
                # Calculate value change
                value_change_pct = ((future['value_score'] - current['value_score']) / 
                                   current['value_score'] * 100)
                
                # Calculate trends (if we have previous data)
                stat_trend = 0
                sentiment_trend = 0
                if i > 0:
                    prev = player_data.iloc[i-1]
                    stat_trend = current['stat_component'] - prev['stat_component']
                    sentiment_trend = current['sentiment_component'] - prev['sentiment_component']
                
                # Label: 1 if profitable (>5% increase), 0 otherwise
                label = 1 if value_change_pct > 5 else 0
                
                # Create training sample
                sample = {
                    'player_id': player_id,
                    'date': current['value_date'],
                    'stat_component': current['stat_component'],
                    'sentiment_component': current['sentiment_component'],
                    'momentum_score': current['momentum_score'],
                    'confidence_score': current['confidence_score'],
                    'value_score': current['value_score'],
                    'stat_trend': stat_trend,
                    'sentiment_trend': sentiment_trend,
                    'future_value_change': value_change_pct,
                    'label': label
                }
                training_samples.append(sample)
        
        training_df = pd.DataFrame(training_samples)
        print(f"✅ Generated {len(training_df)} training samples")
        print(f"   Profitable trades: {training_df['label'].sum()} ({training_df['label'].mean()*100:.1f}%)")
        print(f"   Unprofitable trades: {(1-training_df['label']).sum()} ({(1-training_df['label']).mean()*100:.1f}%)")
        
        return training_df
    
    def train_model(self, training_df: pd.DataFrame):
        """Train Random Forest classifier"""
        print("\n🤖 Training ML model...")
        
        # Prepare features and labels
        X = training_df[self.feature_names].fillna(0)
        y = training_df['label']
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Train Random Forest
        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            min_samples_split=20,
            min_samples_leaf=10,
            random_state=42,
            class_weight='balanced'  # Handle imbalanced data
        )
        
        self.model.fit(X_train, y_train)
        
        # Evaluate
        y_pred = self.model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        
        print(f"✅ Model trained successfully!")
        print(f"   Accuracy: {accuracy*100:.1f}%")
        print(f"   Training samples: {len(X_train)}")
        print(f"   Test samples: {len(X_test)}")
        
        print("\n📊 Classification Report:")
        print(classification_report(y_test, y_pred, 
                                   target_names=['Unprofitable', 'Profitable']))
        
        # Feature importance
        feature_importance = pd.DataFrame({
            'feature': self.feature_names,
            'importance': self.model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        print("\n🎯 Feature Importance:")
        for _, row in feature_importance.iterrows():
            print(f"   {row['feature']}: {row['importance']:.3f}")
        
        return accuracy
    
    def save_model(self):
        """Save trained model to disk"""
        if self.model is None:
            print("❌ No model to save")
            return
        
        with open(self.model_path, 'wb') as f:
            pickle.dump(self.model, f)
        print(f"✅ Model saved to {self.model_path}")
    
    def load_model(self):
        """Load trained model from disk"""
        print(f"🔍 Attempting to load model from: {self.model_path}")
        print(f"   File exists: {os.path.exists(self.model_path)}")
        print(f"   Current working directory: {os.getcwd()}")
        
        if not os.path.exists(self.model_path):
            print(f"❌ Model file not found: {self.model_path}")
            return False
        
        try:
            with open(self.model_path, 'rb') as f:
                self.model = pickle.load(f)
            print(f"✅ Model loaded successfully from {self.model_path}")
            return True
        except Exception as e:
            print(f"❌ Error loading model: {e}")
            return False
    
    def predict_trade_success(self, player_data: Dict) -> Dict:
        """
        Predict if trading this player will be profitable
        Returns: {probability, recommendation, confidence}
        """
        if self.model is None:
            return {'error': 'Model not trained'}
        
        # Prepare features
        features = np.array([[
            player_data.get('stat_component', 0),
            player_data.get('sentiment_component', 0),
            player_data.get('momentum_score', 0),
            player_data.get('confidence_score', 0),
            player_data.get('value_score', 50),
            player_data.get('stat_trend', 0),
            player_data.get('sentiment_trend', 0)
        ]])
        
        # Get prediction probability
        probability = self.model.predict_proba(features)[0][1]  # Probability of profitable
        
        # Determine recommendation
        if probability > 0.7:
            recommendation = 'STRONG BUY'
            action = 'buy'
        elif probability > 0.55:
            recommendation = 'BUY'
            action = 'buy'
        elif probability < 0.3:
            recommendation = 'STRONG SELL'
            action = 'sell'
        elif probability < 0.45:
            recommendation = 'SELL'
            action = 'sell'
        else:
            recommendation = 'HOLD'
            action = 'hold'
        
        return {
            'probability': float(probability),
            'recommendation': recommendation,
            'action': action,
            'confidence': 'high' if abs(probability - 0.5) > 0.2 else 'medium'
        }
    
    def get_ml_recommendations(self, limit: int = 10) -> List[Dict]:
        """Get ML-powered buy recommendations"""
        print("\n🤖 Generating ML-powered recommendations...")
        
        if self.model is None:
            print("❌ Model not loaded. Loading...")
            if not self.load_model():
                print("❌ No trained model available. Run train_and_save() first.")
                return []
        
        # Get latest data
        latest_date_response = supabase.table('player_value_index').select('value_date').order('value_date', desc=True).limit(1).execute()
        if not latest_date_response.data:
            return []
        
        latest_date = latest_date_response.data[0]['value_date']
        
        # Get all players' latest data
        response = supabase.table('player_value_index').select(
            'player_id, value_score, stat_component, sentiment_component, '
            'momentum_score, confidence_score'
        ).eq('value_date', latest_date).execute()
        
        recommendations = []
        
        for record in response.data:
            # Calculate trends (simplified - using momentum as proxy)
            stat_trend = record['momentum_score'] * record['stat_component'] * 0.1
            sentiment_trend = record['momentum_score'] * 0.1
            
            player_data = {
                **record,
                'stat_trend': stat_trend,
                'sentiment_trend': sentiment_trend
            }
            
            prediction = self.predict_trade_success(player_data)
            
            # Only include buy signals (lowered threshold from 0.6 to 0.55)
            if prediction['action'] == 'buy' and prediction['probability'] > 0.55:
                recommendations.append({
                    'player_id': record['player_id'],
                    'value_score': record['value_score'],
                    'stat_component': record['stat_component'],
                    'sentiment_component': record['sentiment_component'],
                    'momentum_score': record['momentum_score'],
                    'ml_probability': prediction['probability'],
                    'ml_recommendation': prediction['recommendation'],
                    'ml_confidence': prediction['confidence']
                })
        
        # Sort by probability
        recommendations.sort(key=lambda x: x['ml_probability'], reverse=True)
        
        # Get player names
        if recommendations:
            player_ids = [r['player_id'] for r in recommendations[:limit]]
            players_response = supabase.table('players').select('id, full_name, team_name, position').in_('id', player_ids).execute()
            players_map = {p['id']: p for p in players_response.data}
            
            for rec in recommendations[:limit]:
                player = players_map.get(rec['player_id'])
                if player:
                    rec['player_name'] = player['full_name']
                    rec['team'] = player['team_name']
                    rec['position'] = player['position']
        
        result_count = len(recommendations[:limit])
        print(f"✅ Found {result_count} ML-powered buy opportunities")
        
        if result_count == 0:
            print(f"ℹ️  Checked {len(response.data)} players, none met criteria (probability > 0.55 and action == 'buy')")
        
        return recommendations[:limit]

def train_and_save():
    """Main function to train and save the model"""
    advisor = MLTradeAdvisor()
    
    # Generate training data
    training_df = advisor.generate_training_data(lookback_days=7)
    
    if training_df is None or len(training_df) < 50:
        print("❌ Not enough data to train. Need more historical data.")
        return
    
    # Train model
    accuracy = advisor.train_model(training_df)
    
    # Save model
    advisor.save_model()
    
    print(f"\n✅ ML Trade Advisor trained and saved!")
    print(f"   Model accuracy: {accuracy*100:.1f}%")
    print(f"   Ready to use for predictions")

if __name__ == "__main__":
    train_and_save()
