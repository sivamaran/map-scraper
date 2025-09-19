import csv
import json
from playwright.sync_api import sync_playwright, TimeoutError
import re
import sys
import os

def create_search_query_from_icp(icp_data):
    """
    Creates a tailored search query for Google Maps based on the ICP data.
    """
    icp_info = icp_data.get('icp_information', {})
    
    # Prioritize target industries and regions
    industries = icp_info.get('target_industry', [])
    regions = icp_info.get('region', [])

    search_terms = []
    if industries and regions:
        for industry in industries:
            for region in regions:
                search_terms.append(f"{industry}, {region}")
    elif industries:
        search_terms = industries
    elif regions:
        search_terms = regions
    else:
        # Fallback to a general search if no specific info is provided
        return "businesses" 

    return " OR ".join(search_terms)


def scrape_google_maps_contacts():
    """
    Scrapes business contact information from Google Maps using Playwright.
    """
    # Load JSON data from a file named 'icp_profile.json'
    # You will need to save your JSON content into a file with this name
    script_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(script_dir, "icp_profile.json")

    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            icp_data = json.load(f)
    except FileNotFoundError:
        print(f"Error: 'icp_profile.json' not found at {json_path}. Please create the file with your ICP data.")
        return
    except json.JSONDecodeError:
        print(f"Error: 'icp_profile.json' is not a valid JSON file. Please check its content.")
        return

    # Use the JSON data to automatically generate the search query
    search_query = create_search_query_from_icp(icp_data)
    
    # --- New print statement to show the generated search query ---
    print(f"Generated search query: {search_query}")
    # -----------------------------------------------------------------

    try:
        num_contacts = int(input("Enter the number of contacts to scrape (e.g., 10 or 20): "))
        if num_contacts <= 0:
            print("Please enter a positive number.")
            return
    except ValueError:
        print("Invalid number. Please enter a valid integer.")
        return
    
    # --- New print statement to confirm the scrape count ---
    print(f"Attempting to scrape a total of {num_contacts} contacts.")
    # -----------------------------------------------------------------


    # Use sync_playwright to run in a single thread
    with sync_playwright() as p:
        # Launch a headless Chromium browser
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        contacts = []

        try:
            print("Starting the scraping process...")
            page.goto("https://www.google.com/maps")

            # Playwright's auto-waiting handles this, but a manual wait for a specific selector is a good practice.
            # Using get_by_role is a more resilient locator strategy.
            try:
                page.get_by_role("button", name="Accept all").click(timeout=5000)
                print("Accepted cookies.")
            except TimeoutError:
                print("Cookie consent button not found or already accepted.")

            # --- New print statement for search query execution ---
            print(f"Searching for: {search_query}")
            # ------------------------------------------------------------------

            # Updated locator for the search box to be more resilient
            page.locator('input#searchboxinput').fill(search_query)
            page.keyboard.press("Enter")

            # Updated the wait for the search results to use a more reliable selector based on role
            page.wait_for_selector('div[role="feed"]', timeout=30000)
            
            print("Search results loaded. Starting to scrape...")

            # Scroll to load more results until we have enough
            while len(contacts) < num_contacts:
                results_pane = page.locator('div[role="feed"]')
                results_pane.evaluate("el => el.scrollTop = el.scrollHeight")

                # Get all the cards that are now visible
                business_cards = page.locator('a[class^="hfpxzc"]').all()
                if len(business_cards) == len(contacts):
                    print("Could not find more unique contacts. Ending scrape.")
                    break

                for i, card in enumerate(business_cards):
                    if len(contacts) >= num_contacts:
                        break

                    # Get basic info from the card before clicking
                    card_name = card.get_attribute("aria-label")
                    if any(c['company_name'] == card_name for c in contacts):
                        continue
                    
                    try:
                        card.click()
                        print(f"Scraping result {i+1} of {num_contacts}...")
                    except Exception as e:
                        print(f"Could not click on card {i+1}: {e}")
                        continue

                    # Scrape details from the detail page
                    details = {}
                    details['company_name'] = card_name
                    details['address'] = "N/A"
                    details['phone_number'] = "N/A"
                    details['website'] = "N/A"
                    details['email'] = "N/A" # Email is generally not available on Google Maps

                    try:
                        details['company_name'] = page.get_by_role("heading", name=card_name).text_content()
                    except TimeoutError:
                        pass
                    
                    try:
                        # Use get_by_label for better resilience than CSS selectors
                        details['address'] = page.get_by_label(re.compile(r"Address: ")).text_content().replace("Address: ", "").strip()
                    except TimeoutError:
                        pass

                    try:
                        details['phone_number'] = page.get_by_label(re.compile(r"Phone: ")).text_content().replace("Phone: ", "").strip()
                    except TimeoutError:
                        pass
                    
                    try:
                        website_locator = page.get_by_label(re.compile(r"Website: "))
                        details['website'] = website_locator.get_attribute("href")
                    except TimeoutError:
                        pass

                    contacts.append(details)
                    
                    # Go back to the search results
                    page.go_back()
                    page.wait_for_selector('div[role="feed"]')

        except Exception as e:
            print(f"An error occurred: {e}")
            
        finally:
            browser.close()

        # Save the data to a CSV file
        if contacts:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            filename = os.path.join(script_dir, "map_search_leads.csv")
            
            with open(filename, 'w', newline='', encoding='utf-8') as file:
                fieldnames = ['company_name', 'address', 'phone_number', 'website', 'email']
                writer = csv.DictWriter(file, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(contacts)
            print(f"Successfully scraped {len(contacts)} contacts and saved to '{filename}'.")
        else:
            print("No contacts were scraped. The search may have returned no results or there was an issue.")
            
if __name__ == '__main__':
    scrape_google_maps_contacts()
