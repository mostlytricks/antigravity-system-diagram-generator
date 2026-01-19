from google.adk.agents import Agent
import os
import json
import xml.etree.ElementTree as ET
from typing import Dict, Any

# --- Tools ---

def search_templates(query: str) -> Dict[str, Any]:
    """
    Searches for specific diagram element styles (e.g., 'k8s pod', 'database').
    Returns the style string and default geometry.
    """
    print(f"\n[TOOL] Searching for template: '{query}'...")
    
    try:
        with open("library.json", "r") as f:
            library = json.load(f)
    except FileNotFoundError:
        print("[TOOL] Error: library.json not found. Using empty library.")
        library = {}
    
    query_lower = query.lower()
    for key, data in library.items():
        if key in query_lower:
            print(f"[TOOL] Found template for '{key}'")
            return data
            
    print(f"[TOOL] No template found for '{query}', returning default.")
    return {"style": "rounded=0;whiteSpace=wrap;html=1;", "width": 80, "height": 40}

def extract_and_save_pattern(file_path: str, pattern_name: str) -> str:
    """
    Analyzes a .drawio file, extracts a design pattern (style/geometry),
    and saves it to library.json.
    """
    print(f"\n[TOOL] Extracting pattern '{pattern_name}' from '{file_path}'...")
    
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        
        target_cell = None
        for cell in root.findall(".//mxCell"):
            if cell.get("vertex") == "1" and cell.get("id") not in ["0", "1"]:
                if not pattern_name or pattern_name.lower() in (cell.get("value") or "").lower():
                    target_cell = cell
                    break
        
        if target_cell is None:
            for cell in root.findall(".//mxCell"):
                if cell.get("vertex") == "1" and cell.get("id") not in ["0", "1"]:
                    target_cell = cell
                    break

        if target_cell is None:
            return f"Error: Could not find any valid vertex cells in {file_path}."

        style = target_cell.get("style", "")
        geometry = target_cell.find("mxGeometry")
        
        if geometry is None:
            return f"Error: No geometry found for the selected cell."

        width = int(geometry.get("width", "80"))
        height = int(geometry.get("height", "40"))

        try:
            with open("library.json", "r") as f:
                library = json.load(f)
        except FileNotFoundError:
            library = {}

        library[pattern_name.lower()] = {
            "style": style,
            "width": width,
            "height": height
        }

        with open("library.json", "w") as f:
            json.dump(library, f, indent=4)

        return f"Successfully extracted pattern '{pattern_name}' and saved to library.json."

    except Exception as e:
        return f"Error during extraction: {str(e)}"

def save_diagram(xml_content: str, filename: str) -> str:
    """
    Saves the provided XML content to a file in the 'generated' directory.
    """
    print(f"\n[TOOL] Saving diagram to '{filename}'...")
    
    if not filename.endswith(".drawio"):
        filename += ".drawio"
        
    os.makedirs("generated", exist_ok=True)
    output_path = os.path.join("generated", filename)
    
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(xml_content)
        return f"File saved successfully at: {output_path}"
    except Exception as e:
        return f"Error saving file: {str(e)}"

# --- Agent Configuration ---

root_agent = Agent(
    name="drawio_architect",
    model="gemini-2.5-flash",
    description="An expert system architect that generates Draw.io XML and manages a design library.",
    instruction="""
    You are a Principal Diagram Architect.
    Your goal is to generate valid Draw.io XML for system architectures AND manage your style library.
    
    ### Design Rules (CRITICAL)
    1.  **Clean Routing**: Edges should NOT cross through other Nodes (containers) unless absolutely necessary.
    2.  **Orthogonal Lines**: ALWAYS use the "connection" style from the library for edges.
    3.  **Container Layout**: Arrange cells neatly with padding.
    
    ### Workflow
    1.  **Extraction**: If asked to "learn", "extract", or "analyze" a file, use `extract_and_save_pattern`.
    2.  **Search**: When building, use `search_templates` to get styles. DO NOT GUESS STYLES.
    3.  **Construct**: Build the XML using library styles.
    4.  **Save**: After generating XML, ALWAYS use `save_diagram` to persist it to the 'generated' folder with a descriptive name.
    5.  **Final Response**: Provide the XML string AND the confirmation from the save tool.
    """,
    tools=[search_templates, extract_and_save_pattern, save_diagram]
)
