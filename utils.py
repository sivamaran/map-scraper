# utils.py
import json
import csv

def save_json(json_list, filename="map_search_leads.json"):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(json_list, f, indent=2, ensure_ascii=False)
    print(f"✅ Saved JSON with {len(json_list)} entries → {filename}")


def json_to_csv(json_list, filename="map_search_leads.csv"):
    if not json_list:
        print("⚠️ No data to save.")
        return

    keys = set()
    for entry in json_list:
        keys.update(entry.keys())
    keys = list(keys)

    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(json_list)

    print(f"✅ Saved CSV with {len(json_list)} entries → {filename}")
