# map_scraper.py

import csv
from playwright.sync_api import sync_playwright, TimeoutError
import re

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
            page.goto("https://www.google.com/maps", timeout=60000)

            # Accept cookies if prompt exists
            try:
                page.get_by_role("button", name="Accept all").click(timeout=5000)
            except TimeoutError:
                pass

            # Fill search box
            page.locator('input#searchboxinput').fill(search_query)
            page.keyboard.press("Enter")

            # Try feed (multi results) OR direct profile
            try:
                page.wait_for_selector('div[role="feed"]', timeout=15000)
                mode = "list"
            except TimeoutError:
                mode = "profile"

            # --- FEED MODE ---
            if mode == "list":
                while len(contacts) < num_contacts:
                    results_pane = page.locator('div[role="feed"]')
                    results_pane.evaluate("el => el.scrollTop = el.scrollHeight")

                    business_cards = page.locator('a[class^="hfpxzc"]').all()
                    if len(business_cards) == len(contacts):
                        break

                    for card in business_cards:
                        if len(contacts) >= num_contacts:
                            break

                        card_name = card.get_attribute("aria-label")
                        if not card_name or any(c['company_name'] == card_name for c in contacts):
                            continue

                        try:
                            card.click()
                            page.wait_for_selector('h1', timeout=10000)
                        except Exception:
                            continue

                        details = extract_details(page, card_name)
                        contacts.append(details)

                        page.go_back()
                        page.wait_for_selector('div[role="feed"]', timeout=10000)

            # --- PROFILE MODE ---
            else:
                card_name = page.locator("h1").first.text_content()
                details = extract_details(page, card_name)
                contacts.append(details)

        finally:
            browser.close()

        return contacts


def extract_details(page, card_name):
    """Extracts details from a Google Maps profile page"""
    details = {
        "company_name": card_name or "N/A",
        "address": "N/A",
        "phone_number": "N/A",
        "website": "N/A",
        "email": "N/A"
    }
    try:
        details["company_name"] = page.locator("h1").first.text_content()
    except: pass
    try:
        details["address"] = page.locator('button[aria-label*="Address"]').text_content()
    except: pass
    try:
        details["phone_number"] = page.locator('button[aria-label*="Phone"]').text_content()
    except: pass
    try:
        details["website"] = page.locator('a[aria-label*="Website"]').get_attribute("href")
    except: pass
    return details
