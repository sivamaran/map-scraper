# test2.py
import csv
import json
import os
from dotenv import load_dotenv
import google.generativeai as genai
from map_scraper import scrape_google_maps_contacts

# ---------------- Load API key from .env ----------------
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("❌ GEMINI_API_KEY not found in .env file")
genai.configure(api_key=api_key)

# ---------------- Query Generation ----------------
def generate_single_query_with_gemini(icp_data: dict) -> str:
    """
    Ask Gemini to generate ONE highly specific Google Maps search query.
    """
    model = genai.GenerativeModel("gemini-1.5-flash")
    prompt = f"""
    You are an expert in lead generation using Google Maps.
    Based on the ICP profile below, generate ONE highly specific
    Google Maps search query that will return a list of relevant businesses.

    ⚠️ Rules:
    - Always include a concrete location (city, region, or country).
    - Never use vague terms like "near me".
    - Query must be short and precise, like "Luxury bus rental Mumbai"
      or "Corporate travel agency Delhi".
    - Use industries, regions, and travel occasions from the ICP.
    - Avoid generic terms like "companies" or "services".
    - If region is broad, default to India.

    Output ONLY the query, nothing else.

    ICP Profile:
    {json.dumps(icp_data, indent=2)}
    """
    response = model.generate_content(prompt)

    print("\n✅ Raw Gemini response:")
    print(response.text)

    query = response.text.strip().splitlines()[0]
    return query

# ---------------- Main Runner ----------------
def test_scraper_and_save():
    # Load ICP profile
    with open("icp_profile.json", "r", encoding="utf-8") as f:
        icp_data = json.load(f)

    # Generate single query with Gemini
    query = generate_single_query_with_gemini(icp_data)

    #queries = ["Restaurants in Mumbai"]


    print("\n🔎 Gemini-generated search query:")
    print(f"➡️ {query}")


    # Run scraper for that query
    results = scrape_google_maps_contacts(query, num_contacts=5, headless=True)

    # Save results
    filename = "map_search_leads.csv"
    with open(filename, "w", newline="", encoding="utf-8") as file:
        fieldnames = ["company_name", "address", "phone_number", "website", "email", "source_query"]
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        if results:
            writer.writerows(results)
            print(f"\n✅ Saved {len(results)} leads to {filename}")
        else:
            print(f"\n⚠️ No leads scraped. Empty CSV created: {filename}")

if __name__ == "__main__":
    test_scraper_and_save()
