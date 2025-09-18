# test2.py
import csv
from map_scraper import scrape_google_maps_contacts

def test_scraper_and_save():
    search_query = "restaurants in Mumbai"
    num_contacts = 5  # adjust as needed
    results = scrape_google_maps_contacts(search_query, num_contacts, headless=True)

    if results:
        filename = "map_search_leads.csv"
        with open(filename, "w", newline="", encoding="utf-8") as file:
            fieldnames = ["company_name", "address", "phone_number", "website", "email"]
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)
        print(f"✅ Saved {len(results)} leads to {filename}")
    else:
        print("⚠️ No leads scraped.")

if __name__ == "__main__":
    test_scraper_and_save()
