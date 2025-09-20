import json
import itertools
import os

def decompose_icp_json(icp_data):
    """
    Dynamically generates all permutations and combinations of list values
    from the 'icp_information' dictionary.
    """
    icp_info = icp_data.get('icp_information', {})
    
    # Identify all keys that have a list as a value
    list_keys = {k: v for k, v in icp_info.items() if isinstance(v, list) and v}
    
    # Handle case where there are no lists to combine
    if not list_keys:
        return [icp_data] if icp_data else [{'icp_information': {'target_industry': ['businesses']}}]

    # Use itertools.product to get all combinations of the list values
    combinations = list(itertools.product(*list_keys.values()))
    
    decomposed_list = []
    
    for combo in combinations:
        new_icp_info = {}
        for i, key in enumerate(list_keys.keys()):
            new_icp_info[key] = [combo[i]]
        decomposed_list.append({'icp_information': new_icp_info})
    
    return decomposed_list

def create_search_query_from_icp(icp_data):
    """
    Creates a combined search query from a decomposed ICP dictionary.
    """
    icp_info = icp_data.get('icp_information', {})
    
    # Gather all non-empty values from the decomposed ICP
    search_terms = []
    for key, value_list in icp_info.items():
        if value_list and isinstance(value_list, list):
            search_terms.extend(value_list)
    
    # Join all search terms into a single query string
    if search_terms:
        return " ".join(search_terms)
            
    return "businesses"

# --- Main part of the script ---
if __name__ == '__main__':
    # Determine the path to the icp_profile.json file
    script_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(script_dir, "icp_profile.json")
    
    try:
        # Read the icp_profile.json file
        with open(json_path, 'r', encoding='utf-8') as f:
            master_icp_data = json.load(f)
            
        print("Successfully read 'icp_profile.json'.")
        
        # Decompose the master JSON
        targeted_icps = decompose_icp_json(master_icp_data.get('icp_data', {}))
        
        # Print the length of the list of decomposed ICPs
        print(f"Total number of decomposed ICPs: {len(targeted_icps)}\n")
        
        # Print the list of decomposed ICPs
        #print("List of decomposed ICPs:\n")
        #print(json.dumps(targeted_icps, indent=4))
        print(len(targeted_icps)) 
        
        # Demonstrate creating search queries from the decomposed ICPs
        if targeted_icps:
            print("\n" + "-"*50)
            print("Sample search queries:")
            for i, icp in enumerate(targeted_icps[:5]): # Print first 5 queries as a sample
                search_query = create_search_query_from_icp(icp)
                print(f"  {i+1}: '{search_query}'")
               
    except FileNotFoundError:
        print(f"Error: 'icp_profile.json' not found at {json_path}. Please make sure the file exists.")
    except json.JSONDecodeError as e:
        print(f"Error: 'icp_profile.json' is not a valid JSON file. Details: {e}")

