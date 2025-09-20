import os
import json
from dotenv import load_dotenv
from map_scraper import run_map_scraper
from utils import save_json, json_to_csv

# 🚨 WARNING: dry_run=False will use your Gemini API key every time.
# Make sure you intend to spend quota.
# If you want to simulate only query generation, pass dry_run=True explicitly.

# ---------------- Load API Key ----------------
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("❌ GEMINI_API_KEY not found. Please check your .env file.")

# ---------------- Main Runner ----------------
if __name__ == "__main__":
    # Load ICP profile
    with open("icp_profile.json", "r", encoding="utf-8") as f:
        icp_data = json.load(f)

    num_search_queries = 3   # how many queries Gemini should generate
    count = 5                # how many leads per query

    try:
        # 🔥 Always real run by default (dry_run=False)
        results = run_map_scraper(icp_data, num_search_queries, count, dry_run=False)
    except Exception as e:
        print(f"❌ Error during scraping: {e}")
        results = []  # ensure variable is defined

    if results:
        save_json(results, "map_search_leads.json")
        json_to_csv(results, "map_search_leads.csv")
    else:
        print("⚠️ No leads scraped, nothing to save.")
