import json
from map_scraper import map_scraper

if __name__ == "__main__":
    with open("icp_profile.json", "r", encoding="utf-8") as f:
        icp_data = json.load(f)

    map_scraper(icp_data, num_search_queries=3, count=5)
