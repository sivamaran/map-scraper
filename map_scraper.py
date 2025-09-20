# map_scraper.py
import os
import google.generativeai as genai
from dotenv import load_dotenv
from scraper_engine import scrape_google_maps_contacts
from utils import save_json, json_to_csv

import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()  # load .env

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise EnvironmentError("❌ GEMINI_API_KEY not found. Please check your .env file.")

genai.configure(api_key=api_key)
MODEL_NAME = "gemini-2.5-flash"


def generate_queries_with_gemini(icp_data, num_search_queries=3):
    """
    Generate search queries from ICP using Gemini 2.5 Flash.
    """
    prompt = f"""
    Based on this ICP (Ideal Customer Profile): {icp_data},
    generate {num_search_queries} highly targeted Google Maps search queries.
    Return them as a plain list, one query per line.
    """

    model = genai.GenerativeModel(MODEL_NAME)
    response = model.generate_content(prompt)

    if not response or not response.text:
        print("⚠️ Gemini returned no text output.")
        return []

    queries = [line.strip() for line in response.text.split("\n") if line.strip()]
    print(f"✅ Gemini generated {len(queries)} queries: {queries}")
    return queries


def wrap_into_schema(raw_details):
    """
    Wrap scraped raw details into schema format.
    """
    address = raw_details.get("address", "")
    phone = raw_details.get("phone", "")

    return {
        "url": raw_details.get("url", ""),
        "platform": "map",
        "content_type": "business",
        "source": "map-scraper",
        "company_name": raw_details.get("company_name", ""),
        "profile": {
            "username": "",
            "full_name": "",
            "bio": "",
            "location": address,  # ✅ location from address
            "job_title": "",
            "employee_count": "",
        },
        "contact": {
            "emails": raw_details.get("emails", []),
            "phone_numbers": [phone] if phone else [],
            "address": address,
            "websites": [raw_details.get("website")] if raw_details.get("website") else [],
            "social_media_handles": {}
        }
    }


def run_map_scraper(icp_data, num_search_queries=3, count=5, dry_run=False):
    """
    Orchestrator:
    - dry_run=True → only queries
    - dry_run=False → full scrape (queries + schema JSON leads)
    """
    queries = generate_queries_with_gemini(icp_data, num_search_queries)

    if dry_run:
        print("📝 Dry run mode → only queries generated")
        return queries

    all_results = []
    for q in queries:
        print(f"\n🔎 Searching for: {q}")
        raw_results = scrape_google_maps_contacts(q, num_contacts=count, headless=True)
        for r in raw_results:
            all_results.append(wrap_into_schema(r))

    return all_results
