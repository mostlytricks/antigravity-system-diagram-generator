import os
import json
import xml.etree.ElementTree as ET
from typing import Dict, Any

# Copy-pasted tools from adk_agent_demo.py to test logic in isolation
def list_library() -> Dict[str, Any]:
    print("\n[TOOL] Listing library contents...")
    try:
        with open("library.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"message": "library.json not found. The library is currently empty."}

def search_templates(query: str) -> Dict[str, Any]:
    print(f"\n[TOOL] Searching for template: '{query}'...")
    try:
        with open("library.json", "r") as f:
            library = json.load(f)
    except FileNotFoundError:
        return {"error": "library.json not found. Use extract_and_save_pattern to add patterns."}
    
    query_lower = query.lower()
    if query_lower in library:
        print(f"[TOOL] Found exact match for '{query_lower}'")
        return library[query_lower]
        
    matches = {k: v for k, v in library.items() if query_lower in k or k in query_lower}
    if matches:
        print(f"[TOOL] Found {len(matches)} fuzzy matches for '{query}'")
        return {"results": matches, "suggestion": "Use one of these keys for a precise style."}
            
    return {"style": "rounded=0;whiteSpace=wrap;html=1;", "width": 80, "height": 40, "message": "Default box."}

def extract_and_save_pattern(file_path: str, pattern_name: str = "all") -> str:
    print(f"\n[TOOL] Extracting pattern '{pattern_name}' from '{file_path}'...")
    try:
        if not os.path.exists(file_path):
            return f"Error: File not found at {file_path}."

        tree = ET.parse(file_path)
        root = tree.getroot()
        extracted_count = 0
        new_patterns = {}
        
        try:
            with open("library.json", "r") as f:
                library = json.load(f)
        except FileNotFoundError:
            library = {}

        for cell in root.findall(".//mxCell"):
            if cell.get("vertex") == "1" and cell.get("id") not in ["0", "1"]:
                cell_value = (cell.get("value") or "").strip()
                cell_style = cell.get("style", "")
                geometry = cell.find("mxGeometry")
                
                if not geometry or not cell_style:
                    continue
                    
                width = int(geometry.get("width", "80"))
                height = int(geometry.get("height", "40"))

                should_extract = False
                extract_key = ""

                if pattern_name.lower() == "all":
                    if cell_value:
                        extract_key = cell_value.lower()
                        should_extract = True
                elif cell_value and pattern_name.lower() in cell_value.lower():
                    extract_key = pattern_name.lower()
                    should_extract = True

                if should_extract and extract_key:
                    library[extract_key] = {"style": cell_style, "width": width, "height": height}
                    new_patterns[extract_key] = True
                    extracted_count += 1

        if extracted_count == 0:
            return f"Agent Note: No suitable cells found."

        with open("library.json", "w") as f:
            json.dump(library, f, indent=4)

        return f"Successfully extracted {extracted_count} patterns."
    except Exception as e:
        return f"Extraction Error: {str(e)}"

# --- Test Execution ---
if __name__ == "__main__":
    print("--- Testing Tool Logic ---")
    
    # 1. Test Extraction
    res = extract_and_save_pattern("sample/k8s_architecture.drawio", "all")
    print(res)
    
    # 2. Test Search (Exact)
    res = search_templates("k8s pod")
    print(f"Exact Match Result: {res.get('style')}")
    
    # 3. Test Search (Fuzzy)
    res = search_templates("k8s")
    print(f"Fuzzy Match Result Keys: {list(res.get('results', {}).keys())}")
    
    # 4. Test List
    res = list_library()
    print(f"Library Keys: {list(res.keys())[:5]}...")
