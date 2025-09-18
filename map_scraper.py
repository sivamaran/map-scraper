# map_scraper.py

from playwright.sync_api import sync_playwright, TimeoutError

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
                while len(contacts) < num_contacts:
                    results = page.locator('a[href*="/maps/place/"]').all()
                    print(f"📌 Found {len(results)} results so far...")

                    if not results:
                        print("⚠️ No results found, switching to profile mode.")
                        break

                    for card in results:
                        if len(contacts) >= num_contacts:
                            break

                        try:
                            card_name = card.get_attribute("aria-label")
                        except Exception:
                            card_name = None

                        if not card_name or any(c['company_name'] == card_name for c in contacts):
                            continue

                        try:
                            card.click()
                            page.wait_for_selector("h1", timeout=10000)
                        except Exception:
                            continue

                        details = extract_details(page, card_name, search_query)
                        contacts.append(details)

                        # Go back to results
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
