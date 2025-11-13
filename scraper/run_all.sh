#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

echo "--- STARTING CRON JOB ---"

echo "Running stats scraper..."
python3 daily_stats_scraper.py

echo "Running sentiment scraper..."
python3 daily_sentiment_scraper.py

echo "--- CRON JOB COMPLETE ---"