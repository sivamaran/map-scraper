import csv
from playwright.sync_api import sync_playwright, TimeoutError
import re
import sys
import os

def scrape_google_maps_contacts():
    """
    Scrapes business contact information from Google Maps using Playwright.
    """
    # Get search query and number of contacts directly from the user
    search_query = input("Enter the search query (e.g., 'restaurants in Mumbai'): ")
    try:
        num_contacts = int(input("Enter the number of contacts to scrape (e.g., 10 or 20): "))
        if num_contacts <= 0:
            print("Please enter a positive number.")
            return
    except ValueError:
        print("Invalid number. Please enter a valid integer.")
        return

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
                        print(f"Scraping result {len(contacts)+1} of {num_contacts}...")
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
            filename = "map_search_leads.csv"
            
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
