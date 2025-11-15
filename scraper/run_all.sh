#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

echo "--- STARTING CRON JOB ---"

echo "Running stats scraper..."
# Tell python to look inside the 'scraper' folder
python3 scraper/daily_stats_scraper.py

echo "Running sentiment scraper..."
# Tell python to look inside the 'scraper' folder
python3 scraper/daily_sentiment_scraper.py

echo "Running value index calculator..."
# Tell python to look inside the 'scraper' folder
python3 scraper/daily_value_index.py

echo "--- CRON JOB COMPLETE ---"