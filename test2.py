# test2.py

import csv
import json
import os
from dotenv import load_dotenv
import google.generativeai as genai
from map_scraper import scrape_google_maps_contacts, convert_to_unified_format

# ---------------- Load API key ----------------
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("❌ GEMINI_API_KEY not found in .env file")
genai.configure(api_key=api_key)


# ---------------- Gemini Query Generation ----------------
def generate_single_query_with_gemini(icp_data: dict) -> str:
    model = genai.GenerativeModel("gemini-1.5-flash")
    prompt = f"""
    You are an expert in lead generation using Google Maps.
    Based on the ICP profile below, generate ONE highly specific
    Google Maps search query that will return a list of relevant businesses.

    ⚠️ Rules:
    - Always include a concrete location (city, region, or country).
    - Never use vague terms like "near me".
    - Query must be short and precise, e.g. "Luxury bus rental Mumbai".
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
    return response.text.strip().splitlines()[0]


# ---------------- Main Runner ----------------
def test_scraper_and_save():
    # Load ICP profile
    with open("icp_profile.json", "r", encoding="utf-8") as f:
        icp_data = json.load(f)

    # Get one Gemini query
    query = generate_single_query_with_gemini(icp_data)
    print(f"\n🔎 Gemini-generated query: {query}")

    # Run scraper
    results = scrape_google_maps_contacts(query, num_contacts=5, headless=True)

    # Convert results to unified format
    unified_results = [convert_to_unified_format(r, "schema_template.json") for r in results]

    # Save CSV
    filename_csv = "map_search_leads.csv"
    with open(filename_csv, "w", newline="", encoding="utf-8") as file:
        fieldnames = ["company_name", "address", "phone_number", "website", "email", "source_query"]
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    print(f"\n✅ Saved {len(results)} leads to {filename_csv}")

    # Save JSON
    filename_json = "map_search_leads.json"
    with open(filename_json, "w", encoding="utf-8") as f:
        json.dump(unified_results, f, indent=2, ensure_ascii=False)
    print(f"✅ Saved {len(unified_results)} unified leads to {filename_json}")


if __name__ == "__main__":
    test_scraper_and_save()
