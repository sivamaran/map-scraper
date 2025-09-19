import json
from map_scraper import map_scraper

if __name__ == "__main__":
    with open("icp_profile.json", "r", encoding="utf-8") as f:
        icp_data = json.load(f)

    # Inputs provided by user
    num_search_queries = 3   # how many queries Gemini should generate
    count = 5                # how many leads to scrape per query

    # ✅ Dry run (queries only)
    queries = map_scraper(icp_data, num_search_queries, count, dry_run=True)
    print("Dry run queries:", queries)

    # ✅ Full scrape (default since dry_run=False)
    # results = map_scraper(icp_data, num_search_queries, count, dry_run=False)
    # print("Scraped results:", results)
