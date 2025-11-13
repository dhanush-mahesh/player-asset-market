import os
import feedparser # A simple library for RSS feeds
from transformers import pipeline # For the Hugging Face model
from dotenv import load_dotenv
from supabase import create_client, Client
import datetime
import time

# --- 1. SETUP ---
print("\nStarting Sentiment Scraper (Phase 2, Stage 2)...")
load_dotenv()
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")

if not url or not key:
    print("Error: SUPABASE_URL or SUPABASE_KEY not found in .env file.")
    exit()

try:
    supabase: Client = create_client(url, key)
    print("Successfully connected to Supabase.")
except Exception as e:
    print(f"Error connecting to Supabase: {e}")
    exit()

# Initialize the Hugging Face model (as mentioned in your plan)
# This will download the model the first time it's run
print("Loading sentiment model (this may take a moment)...")
try:
    sentiment_pipeline = pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")
    print("Sentiment model loaded successfully.")
except Exception as e:
    print(f"Error loading sentiment model: {e}")
    print("Please ensure you have an internet connection and 'transformers' and 'torch' are installed.")
    exit()

# --- 2. MAIN EXECUTION ---
def run_sentiment_pipeline():
    # --- STAGE 1: Get all players from DB ---
    print("Fetching player list from Supabase...")
    player_map = {} # Maps {full_name: supabase_id}
    try:
        response = supabase.table('players').select('id, full_name').execute()
        if not response.data:
            print("No players found in database. Exiting sentiment scraper.")
            return
        for player in response.data:
            player_map[player['full_name']] = player['id']
        print(f"Found {len(player_map)} players to check against headlines.")
    except Exception as e:
        print(f"Error fetching players: {e}")
        return

    # --- STAGE 2: Scrape News Feed ---
    print("Fetching ESPN NBA RSS feed...")
    # This is a much more stable way to get headlines than scraping a full page
    feed_url = "https://www.espn.com/espn/rss/nba/news"
    feed = feedparser.parse(feed_url)
    
    if not feed.entries:
        print("No articles found in RSS feed.")
        return
        
    print(f"Found {len(feed.entries)} articles.")
    
    # --- STAGE 3: Analyze Sentiment and Insert ---
    sentiment_to_insert = []
    today = datetime.date.today().isoformat()
    
    # Use a set to avoid saving the same (player, headline) pair twice
    processed_pairs = set()

    for entry in feed.entries:
        headline = entry.title
        
        # Check if any player name is in the headline
        for player_name, player_id in player_map.items():
            # Check for the full name as a whole word to avoid partial matches
            if f" {player_name} " in f" {headline} ":
                
                if (player_id, headline) in processed_pairs:
                    continue # Already processed this
                    
                print(f"  Found match: '{player_name}' in headline: '{headline}'")
                
                # Run NLP sentiment analysis
                try:
                    result = sentiment_pipeline(headline)[0]
                    label = result['label']
                    score = result['score']
                    
                    # Convert score to -1.0 to +1.0 (as per your plan)
                    if label == 'NEGATIVE':
                        sentiment_score = -score
                    else:
                        sentiment_score = score
                        
                    sentiment_obj = {
                        "player_id": player_id,
                        "article_date": today,
                        "headline_text": headline,
                        "sentiment_score": sentiment_score
                    }
                    sentiment_to_insert.append(sentiment_obj)
                    processed_pairs.add((player_id, headline))
                    
                except Exception as e:
                    print(f"    Error analyzing sentiment for headline: {e}")

    if sentiment_to_insert:
        print(f"\nInserting {len(sentiment_to_insert)} sentiment records...")
        try:
            response = supabase.table('daily_player_sentiment').insert(sentiment_to_insert).execute()
            if response.data:
                print(f"Successfully inserted {len(response.data)} sentiment records.")
            print("--- SENTIMENT SCRAPE COMPLETE ---")
        except Exception as e:
            print(f"Error inserting sentiment: {e}")
    else:
        print("\nNo new player sentiment to insert.")

if __name__ == "__main__":
    run_sentiment_pipeline()