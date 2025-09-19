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
def generate_queries_with_gemini(icp_data: dict, num_search_queries: int = 3) -> list:
    """
    Ask Gemini (2.5 Flash) to generate multiple Google Maps search queries
    by combining values from target_industry + region in the ICP JSON.
    """
    model = genai.GenerativeModel("gemini-2.5-flash")

    icp_json_text = json.dumps(icp_data, indent=2)

    prompt = f"""
    You are an expert in lead generation using Google Maps.

    You are given an ICP profile in JSON format.

    Task:
    - Generate {num_search_queries} unique Google Maps search queries.
    - Each query must combine one value from "target_industry" with one value from "region".
    - Queries must reflect real combinations that would return useful business leads.

    Rules:
    - ⚠️ You must only use values from the JSON lists. Never invent new ones.
    - Do not use vague placeholders like "businesses", "shops", "companies", or "services".
    - Always keep the format: "<Chosen Industry> <Chosen Region>".
    - Keep queries short and natural (e.g., "Real Estate Agents Mumbai", "Corporate Travel Agencies Delhi").
    - Output ONLY the list of queries, one per line.

    ICP JSON:
    {icp_json_text}
    """

    response = model.generate_content(prompt)

    if response.candidates and response.candidates[0].content.parts:
        queries_text = response.candidates[0].content.parts[0].text.strip()
    else:
        raise ValueError("❌ Gemini returned no valid queries.")

    queries = [q.strip() for q in queries_text.splitlines() if q.strip()]
    queries = queries[:num_search_queries]

    # 🔍 Print queries when generated
    print("\n✅ Gemini-generated search queries:")
    for idx, q in enumerate(queries, start=1):
        print(f"{idx}. {q}")

    return queries

# ---------------- Main Runner ----------------
def test_scraper_and_save():
    # Load ICP profile
    with open("icp_profile.json", "r", encoding="utf-8") as f:
        icp_data = json.load(f)

    num_search_queries = 3  # how many queries Gemini should generate
    count = 5               # how many leads to scrape per query

    queries = generate_queries_with_gemini(icp_data, num_search_queries)

    all_results = []
    for q in queries:
        print(f"\n🔎 Searching for: {q}")
        results = scrape_google_maps_contacts(q, num_contacts=count, headless=True)
        for r in results:
            r["source_query"] = q  # tag results with the query they came from
        all_results.extend(results)

    # Save results
    filename = "map_search_leads.csv"
    with open(filename, "w", newline="", encoding="utf-8") as file:
        fieldnames = ["company_name", "address", "phone_number", "website", "email", "source_query"]
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        if all_results:
            writer.writerows(all_results)
            print(f"\n✅ Saved {len(all_results)} leads from {len(queries)} queries to {filename}")
        else:
            print(f"\n⚠️ No leads scraped. Empty CSV created: {filename}")

if __name__ == "__main__":
    test_scraper_and_save()
