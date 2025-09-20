# utils.py
import json
import csv
import os
from pymongo import MongoClient

def save_json(json_list, filename="map_search_leads.json"):
    """Save raw JSON list to file."""
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(json_list, f, indent=2, ensure_ascii=False)
    print(f"✅ Saved JSON with {len(json_list)} entries → {filename}")


def json_to_csv(json_list, filename="map_search_leads.csv"):
    """Flatten JSON list into a clean CSV format."""
    if not json_list:
        print("⚠️ No data to save.")
        return

    # Define the flat structure
    keys = [
        "company_name",
        "address",
        "phone_number",
        "website",
        "email",
        "url",
        "platform",
        "source",
        "content_type"
    ]

    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()

        for item in json_list:
            # Contact info is nested → flatten
            contact = item.get("contact", {})
            row = {
                "company_name": item.get("company_name", ""),
                "address": contact.get("address", ""),
                "phone_number": ";".join(contact.get("phone_numbers", [])),
                "website": ";".join(contact.get("websites", [])),
                "email": ";".join(contact.get("emails", [])),
                "url": item.get("url", ""),
                "platform": item.get("platform", ""),
                "source": item.get("source", ""),
                "content_type": item.get("content_type", ""),
            }
            writer.writerow(row)

    print(f"✅ Saved CSV with {len(json_list)} entries → {filename}")



def save_to_mongo(json_list, db_name="leadgen", collection_name="map_leads"):
    """
    Save a list of JSON documents into MongoDB.

    Parameters:
        json_list (list): List of dicts to insert.
        db_name (str): Database name (default = "leadgen").
        collection_name (str): Collection name (default = "map_leads").
    """
    mongo_uri = os.getenv("MONGO_URI")
    if not mongo_uri:
        raise EnvironmentError("❌ MONGO_URI not found. Please check your .env file.")

    client = MongoClient(mongo_uri)
    db = client[db_name]
    collection = db[collection_name]

    if not json_list:
        print("⚠️ No data to save to MongoDB.")
        return

    try:
        collection.insert_many(json_list)
        print(f"✅ Inserted {len(json_list)} documents into {db_name}.{collection_name}")
    except Exception as e:
        print(f"❌ MongoDB insert failed: {e}")
