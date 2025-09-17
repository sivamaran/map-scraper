import csv
import json
from playwright.sync_api import sync_playwright, TimeoutError
import re
import os
import itertools

def decompose_icp_json(icp_data):
    """
    Dynamically generates a list of targeted search dictionaries from the ICP data.
    Combines 'target_industry' and 'region' lists for focused searches.
    """
    icp_info = icp_data.get('icp_information', {})
    industries = icp_info.get('target_industry', [])
    regions = icp_info.get('region', [])

    if not industries or not regions:
        print("Warning: 'target_industry' or 'region' lists are empty in icp_profile.json.")
        return []

    # Create combinations of industries and regions for targeted searches
    campaigns = list(itertools.product(industries, regions))

    decomposed_list = []
    for campaign in campaigns:
        decomposed_list.append({
            'icp_information': {
                'target_industry': [campaign[0]],
                'region': [campaign[1]]
            }
        })
    
    return decomposed_list

def create_search_query_from_icp(icp_data):
    """
    Creates a single, tailored search query for Google Maps from a decomposed ICP.
    """
    icp_info = icp_data.get('icp_information', {})
    
    search_terms = []
    if 'target_industry' in icp_info and icp_info['target_industry']:
        search_terms.append(icp_info['target_industry'][0])
    
    if 'region' in icp_info and icp_info['region']:
        search_terms.append(icp_info['region'][0])
    
    return ", ".join(search_terms)

def scrape_google_maps_contacts():
    """
    Scrapes business contact information from Google Maps using Playwright.
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(script_dir, "icp_profile.json")

    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            master_icp_data = json.load(f)
    except FileNotFoundError:
        print(f"Error: 'icp_profile.json' not found at {json_path}. Please create the file with your ICP data.")
        return
    except json.JSONDecodeError:
        print(f"Error: 'icp_profile.json' is not a valid JSON file. Please check its content.")
        return
    
    targeted_icps = decompose_icp_json(master_icp_data)
    
    try:
        num_contacts = int(input("Enter the number of contacts to scrape per campaign (e.g., 10 or 20): "))
        if num_contacts <= 0:
            print("Please enter a positive number.")
            return
    except ValueError:
        print("Invalid number. Please enter a valid integer.")
        return
    
    all_contacts = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            print("Starting the scraping process...")
            page.goto("https://www.google.com/maps")
            try:
                page.get_by_role("button", name="Accept all").click(timeout=5000)
                print("Accepted cookies.")
            except TimeoutError:
                print("Cookie consent button not found or already accepted.")

            for i, icp in enumerate(targeted_icps):
                search_query = create_search_query_from_icp(icp)
                print(f"Starting campaign {i+1}/{len(targeted_icps)} for: '{search_query}'")
                
                contacts_for_campaign = []

                page.locator('input#searchboxinput').fill(search_query)
                page.keyboard.press("Enter")
                page.wait_for_selector('div[role="feed"]', timeout=30000)
                
                while len(contacts_for_campaign) < num_contacts:
                    results_pane = page.locator('div[role="feed"]')
                    results_pane.evaluate("el => el.scrollTop = el.scrollHeight")
                    
                    business_cards = page.locator('a[class^="hfpxzc"]').all()
                    
                    if len(business_cards) == len(contacts_for_campaign):
                        print("Could not find more unique contacts. Ending this campaign.")
                        break

                    for card in business_cards:
                        if len(contacts_for_campaign) >= num_contacts:
                            break

                        card_name = card.get_attribute("aria-label")
                        if not card_name or any(c['company_name'] == card_name for c in contacts_for_campaign):
                            continue
                        
                        try:
                            card.click()
                            print(f" - Scraping '{card_name}'...")
                        except Exception as e:
                            print(f" - Could not click on card '{card_name}': {e}")
                            continue

                        details = {
                            'company_name': card_name,
                            'address': "N/A",
                            'phone_number': "N/A",
                            'website': "N/A",
                            'email': "N/A"
                        }
                        
                        try:
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

                        contacts_for_campaign.append(details)
                        
                        page.go_back()
                        page.wait_for_selector('div[role="feed"]')

                # Clear search bar for the next campaign
                page.locator('input#searchboxinput').fill("")
                
                all_contacts.extend(contacts_for_campaign)

        except Exception as e:
            print(f"A fatal error occurred: {e}")
            
        finally:
            browser.close()

    if all_contacts:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        filename = os.path.join(script_dir, "map_search_leads.csv")
        
        with open(filename, 'w', newline='', encoding='utf-8') as file:
            fieldnames = ['company_name', 'address', 'phone_number', 'website', 'email']
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_contacts)
        print(f"Successfully scraped {len(all_contacts)} contacts and saved to '{filename}'.")
    else:
        print("No contacts were scraped. The search may have returned no results or there was an issue.")
        
if __name__ == '__main__':
    scrape_google_maps_contacts()
