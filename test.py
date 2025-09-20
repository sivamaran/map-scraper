import os
import json
from utils import save_json, json_to_csv, save_to_mongo
from map_scraper import run_map_scraper

def main():
    # Load ICP profile
    with open("icp_profile.json", "r", encoding="utf-8") as f:
        icp_data = json.load(f)

    # Params (you can adjust here or make CLI args later)
    num_search_queries = 3
    count = 5
    dry_run = False

    # Run scraper
    results = run_map_scraper(icp_data, num_search_queries=num_search_queries, count=count, dry_run=dry_run)

    # Ensure data/ folder exists
    os.makedirs("data", exist_ok=True)

    # Save results in multiple formats
    save_json(results, "data/map_leads.json")
    json_to_csv(results, "data/map_leads.csv")
    #save_to_mongo(results, db_name="leadgen", collection_name="map_leads")

if __name__ == "__main__":
    main()
