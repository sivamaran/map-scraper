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
    Ask Gemini (2.5 Flash) to generate ONE highly specific Google Maps search query
    by selecting the best combination of target_industry + region from the ICP JSON.
    """
    model = genai.GenerativeModel("gemini-2.5-flash")

    # Prepare full ICP JSON for context
    icp_json_text = json.dumps(icp_data, indent=2)

    prompt = f"""
    You are an expert in lead generation using Google Maps.

    You are given an ICP profile in JSON format.

    Task:
    - Select exactly ONE value from "target_industry".
    - Select exactly ONE value from "region".
    - Combine them into ONE short Google Maps search query.

    Rules:
    - ⚠️ You must only choose values that appear in the JSON lists. Never invent or replace values.
    - Do not output vague placeholders like "businesses", "shops", "companies", or "services".
    - Always keep the format: "<Chosen Industry> <Chosen Region>".
    - Keep it short and natural (like "Real Estate Agents Mumbai", "Corporate Travel Agencies Delhi").
    - Output ONLY the query, nothing else.

    ICP JSON:
    {icp_json_text}
    """

    response = model.generate_content(prompt)

    if response.candidates and response.candidates[0].content.parts:
        query = response.candidates[0].content.parts[0].text.strip()
    else:
        raise ValueError("❌ Gemini returned no valid text.")

    print("\n🔎 Gemini-generated search query:")
    print(f"➡️ {query}")

    return query

# ---------------- Main Runner ----------------
def test_scraper_and_save():
    # Load ICP profile
    with open("icp_profile.json", "r", encoding="utf-8") as f:
        icp_data = json.load(f)

    # Generate single query with Gemini
    query = generate_single_query_with_gemini(icp_data)

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
