import csv
import json
import os
from dotenv import load_dotenv
import google.generativeai as genai
from playwright.sync_api import sync_playwright, TimeoutError

# ---------------- Load API key from .env ----------------
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("❌ GEMINI_API_KEY not found in .env file")
genai.configure(api_key=api_key)

# ---------------- Gemini Query Generation ----------------
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
    - Keep queries short and natural (e.g., "Real Estate Investors Navi Mumbai").
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

# ---------------- Scraper ----------------
def scrape_google_maps_contacts(search_query: str, num_contacts: int = 10, headless: bool = True):
    """
    Scrapes business contact information from Google Maps using Playwright.
    Returns a list of dictionaries with contact details.
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        page = browser.new_page()

        contacts = []

        try:
            print(f"\n🔍 Searching for: {search_query}")
            page.goto("https://www.google.com/maps", timeout=60000)

            # Accept cookies if prompt exists
            try:
                page.get_by_role("button", name="Accept all").click(timeout=5000)
            except TimeoutError:
                pass

            # Fill search box
            page.locator('input#searchboxinput').fill(search_query)
            page.keyboard.press("Enter")

            # --- Detect mode dynamically ---
            page.wait_for_timeout(5000)  # give Maps time to load
            if page.locator('a[href*="/maps/place/"]').count() > 0:
                mode = "list"
                print("✅ Detected LIST mode")
            else:
                mode = "profile"
                print("ℹ️ Detected PROFILE mode")

            # --- LIST MODE ---
            if mode == "list":
                previous_count = 0
                stuck_counter = 0

                while len(contacts) < num_contacts:
                    results = page.locator('a[href*="/maps/place/"]').all()
                    print(f"📌 Found {len(results)} results so far...")

                    # Stop if results don't increase after a few scrolls
                    if len(results) == previous_count:
                        stuck_counter += 1
                    else:
                        stuck_counter = 0
                    previous_count = len(results)

                    if stuck_counter >= 3:
                        print("⚠️ No more new results. Stopping scroll loop.")
                        break

                    if not results:
                        print("⚠️ No results found, switching to profile mode.")
                        break

                    for card in results:
                        if len(contacts) >= num_contacts:
                            break

                        try:
                            card.click()
                            page.wait_for_selector("h1", timeout=10000)
                            card_name = page.locator("h1").first.text_content()
                        except Exception:
                            continue

                        # 🚫 Skip dummies like "Results"
                        if not card_name or card_name.strip().lower() == "results":
                            continue

                        if any(c['company_name'] == card_name for c in contacts):
                            continue

                        details = extract_details(page, card_name, search_query)
                        contacts.append(details)

                        # Go back
                        try:
                            page.go_back()
                            page.wait_for_timeout(3000)
                        except Exception:
                            # fallback: re-run query
                            page.locator('input#searchboxinput').fill(search_query)
                            page.keyboard.press("Enter")
                            page.wait_for_timeout(5000)

            # --- PROFILE MODE ---
            if mode == "profile" or not contacts:
                try:
                    card_name = page.locator("h1").first.text_content()
                    if card_name and card_name.strip().lower() != "results":
                        details = extract_details(page, card_name, search_query)
                        contacts.append(details)
                except Exception:
                    print(f"⚠️ Could not extract profile for query: {search_query}")

        finally:
            browser.close()

        return contacts

def extract_details(page, card_name, source_query):
    """Extracts details from a Google Maps profile page"""
    details = {
        "company_name": card_name or "N/A",
        "address": "N/A",
        "phone_number": "N/A",
        "website": "N/A",
        "email": "N/A",
        "source_query": source_query
    }
    try:
        details["company_name"] = page.locator("h1").first.text_content()
    except:
        pass
    try:
        details["address"] = page.locator('button[aria-label*="Address"]').first.text_content()
    except:
        pass
    try:
        details["phone_number"] = page.locator('button[aria-label*="Phone"]').first.text_content()
    except:
        pass
    try:
        details["website"] = page.locator('a[aria-label*="Website"]').first.get_attribute("href")
    except:
        pass
    return details

# ---------------- Orchestrator ----------------
def map_scraper(icp_data: dict, num_search_queries: int = 3, count: int = 5):
    """
    Full pipeline:
    - Use ICP JSON (passed from outside)
    - Generate queries with Gemini
    - Scrape Google Maps
    - Save results to CSV
    """
    queries = generate_queries_with_gemini(icp_data, num_search_queries)

    all_results = []
    for q in queries:
        print(f"\n🔎 Running scraper for: {q}")
        results = scrape_google_maps_contacts(q, num_contacts=count, headless=True)
        all_results.extend(results)

    # save to csv
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
