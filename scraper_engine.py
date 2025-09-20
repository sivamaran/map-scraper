# scraper_engine.py
from playwright.sync_api import sync_playwright

def scrape_google_maps_contacts(query, num_contacts=5, headless=True):
    results = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        page = browser.new_page()
        page.goto("https://www.google.com/maps", timeout=60000)

        # ✅ Handle consent popups if they appear
        try:
            page.locator("button:has-text('Accept all')").click(timeout=5000)
        except:
            pass

        # ✅ Candidate selectors for search box
        candidate_selectors = [
            "input[aria-label='Search Google Maps']",
            "input[aria-label*='Search']",
            "input#searchboxinput",
            "input.tactile-searchbox-input",   # class used in Maps UI
            "input[placeholder*='Search']"
        ]

        search_box = None
        for sel in candidate_selectors:
            try:
                page.wait_for_selector(sel, timeout=5000)
                search_box = page.locator(sel)
                print(f"✅ Search bar found with selector: {sel}")
                break
            except:
                continue

        if not search_box:
            browser.close()
            raise RuntimeError("❌ Could not find the Google Maps search bar")

        # ✅ Enter the query
        search_box.fill(query)
        search_box.press("Enter")
        page.wait_for_timeout(6000)

        # ✅ Detect list of results
        listings = page.locator("a[href*='/maps/place/']").all()

        for i, listing in enumerate(listings[:num_contacts]):
            try:
                url = listing.get_attribute("href")
                name = listing.inner_text()

                results.append({
                    "company_name": name,
                    "url": url,
                    "address": "",
                    "phone_number": "",
                    "website": "",
                    "email": "",
                    "source_query": query
                })
            except Exception as e:
                print(f"⚠️ Skipped a listing due to error: {e}")

        browser.close()

    return results
