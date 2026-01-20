# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
ADK Agent Demo: Draw.io Architect
This script demonstrates how to build a Tool-Using Agent with the Google Agent Development Kit (ADK).
It effectively replaces our previous 'Context Stuffing' approach with proper Tool function calling.
"""

import asyncio
import os
from typing import Dict, Any

# NOTE: These imports assume the `google-adk` package is installed.
# If running in a mock environment, you might need to adjust or mock these.
try:
    from google.adk.agents import LlmAgent
    from google.adk.runners import Runner
    from google.adk.sessions import InMemorySessionService
    from google.genai import types
except ImportError:
    print("WARNING: `google-adk` not found. This script serves as a Reference Implementation.")
    # Mocking basic classes so the script syntax can be validated conceptually
    class LlmAgent:
        def __init__(self, **kwargs): pass
    class Runner:
        def __init__(self, **kwargs): pass
        async def run_async(self, **kwargs): 
            # Simulate a multi-turn response for the mock
            yield type('obj', (object,), {'text': "Mock Agent Thinking...", 'function_calls': []})()
            yield type('obj', (object,), {'text': "Mock Agent Output: <mxfile>...</mxfile>", 'function_calls': []})()
    class InMemorySessionService:
        async def get_session(self, **kwargs):
             return type('obj', (object,), {'state': {"final_xml_result": "<mock_xml>Generated Diagram</mock_xml>"}})()
    
    # Mock types for Content/Part
    class types:
        class Part:
            def __init__(self, text): self.text = text
        class Content:
            def __init__(self, role, parts): self.role = role; self.parts = parts


# --- 1. Define Constants ---
APP_NAME = "drawio_architect_app"
USER_ID = "architect_user_001"
SESSION_ID = "session_k8s_design"
MODEL_NAME = "gemini-1.5-pro" # Or gemini-2.0-flash

# --- 2. Define the Tool ---
def list_library() -> Dict[str, Any]:
    """
    Returns all currently saved styles and components from library.json.
    Agent should use this to see what building blocks are already available.
    """
    print("\n[TOOL] Listing library contents...")
    try:
        import json
        with open("library.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"message": "library.json not found. The library is currently empty."}

def search_templates(query: str) -> Dict[str, Any]:
    """
    Searches building blocks (style, width, height) in the library.
    Agent should call this before trying to build a new component to see if a style already exists.
    Priority: Exact matches > Fuzzy matches.
    """
    print(f"\n[TOOL] Searching for template: '{query}'...")
    
    try:
        import json
        with open("library.json", "r") as f:
            library = json.load(f)
    except FileNotFoundError:
        return {"error": "library.json not found. Use extract_and_save_pattern to add patterns."}
    
    query_lower = query.lower()
    
    # 1. Exact match check
    if query_lower in library:
        print(f"[TOOL] Found exact match for '{query_lower}'")
        return library[query_lower]
        
    # 2. Simple fuzzy search (substring)
    matches = {k: v for k, v in library.items() if query_lower in k or k in query_lower}
    if matches:
        print(f"[TOOL] Found {len(matches)} fuzzy matches for '{query}'")
        return {"results": matches, "suggestion": "Use one of these keys for a precise style."}
            
    print(f"[TOOL] No template found for '{query}', returning default box.")
    return {
        "style": "rounded=0;whiteSpace=wrap;html=1;", 
        "width": 80, 
        "height": 40, 
        "message": f"No library entry for '{query}'. Using basic rectangle."
    }

def extract_and_save_pattern(file_path: str, pattern_name: str = "all") -> str:
    """
    Analyzes an existing .drawio file and extracts style/geometry patterns.
    - If pattern_name is "all", it tries to extract ALL unique-looking vertex cells.
    - If pattern_name is specific (e.g. 'k8s pod'), it searches for a cell with that value.
    This tool is essential when you (the agent) want to 'learn' new designs from user files.
    """
    print(f"\n[TOOL] Extracting pattern '{pattern_name}' from '{file_path}'...")
    
    import xml.etree.ElementTree as ET
    import json
    
    try:
        if not os.path.exists(file_path):
            return f"Error: File not found at {file_path}. Use absolute paths if possible."

        tree = ET.parse(file_path)
        root = tree.getroot()
        
        extracted_count = 0
        new_patterns = {}
        
        # Load existing library
        try:
            with open("library.json", "r") as f:
                library = json.load(f)
        except FileNotFoundError:
            library = {}

        for cell in root.findall(".//mxCell"):
            # We only care about vertices (boxes, nodes) and skip the default parent containers (0 and 1)
            if cell.get("vertex") == "1" and cell.get("id") not in ["0", "1"]:
                cell_value = (cell.get("value") or "").strip()
                cell_style = cell.get("style", "")
                geometry = cell.find("mxGeometry")
                
                if not geometry or not cell_style:
                    continue
                    
                width = int(geometry.get("width", "80"))
                height = int(geometry.get("height", "40"))

                # Logic: If 'all', extract everything that has a value.
                # If specific name, only extract if name matches.
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
                    library[extract_key] = {
                        "style": cell_style,
                        "width": width,
                        "height": height
                    }
                    new_patterns[extract_key] = True
                    extracted_count += 1

        if extracted_count == 0:
            return f"Agent Note: No suitable cells found in {file_path} for pattern '{pattern_name}'."

        with open("library.json", "w") as f:
            json.dump(library, f, indent=4)

        summary = f"Successfully extracted {extracted_count} patterns: {list(new_patterns.keys())}."
        print(f"[TOOL] {summary}")
        return summary

    except Exception as e:
        return f"Extraction Error: {str(e)}. Please check the file path and format."

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

# --- 3. Configure the Agent ---
# The Agent is the "Brain". It has an identity, instructions, and access to tools.

architect_agent = LlmAgent(
    model=MODEL_NAME,
    name="drawio_architect",
    description="An expert system architect that generates Draw.io XML and manages its own component library.",
    instruction="""
    You are a Principal Diagram Architect. 
    Your job is to design professional architectures using Draw.io XML format.
    You have a persistent library of components (library.json) that you MUST manage and use.

    ### CRITICAL: Handling LLM Reasoning & Errors
    - When asked to generate a diagram, FIRST check the library using `list_library` or `search_templates`.
    - If you are missing a style, and the user provided a sample .drawio file, use `extract_and_save_pattern` to LEARN from it.
    - If extraction returns an error, do not hallucinate a style; instead, use the default style or ask the user for clarification.
    - Always output valid XML wrapped in <mxfile> tags.

    ### Design Rules
    1.  **Clean Routing**: Use orthogonal edges. Avoid lines overlapping nodes.
    2.  **Consistency**: Use the same style/size for identical components (e.g., all 'Pods' should look the same).
    3.  **Persistence**: Every pattern you extract is saved PERMANENTLY. Build up your expertise over multiple sessions.
    
    ### Workflow
    1.  **Context**: Use `list_library` to see what you already know.
    2.  **Extraction**: Use `extract_and_save_pattern(file_path, 'all')` to ingest new designs from user examples.
    3.  **Design**: Use patterns from `search_templates`.
    4.  **Save**: Use `save_diagram` to store your final XML in the 'generated' folder.
    """,
    tools=[list_library, search_templates, extract_and_save_pattern, save_diagram],
    output_key="final_xml_result"
)

# --- 4. Setup Runner & Session ---
session_service = InMemorySessionService()
runner = Runner(
    agent=architect_agent,
    app_name=APP_NAME,
    session_service=session_service
)

# --- 5. Execution Loop ---
async def main():
    import sys
    import time
    
    print(f"--- Starting ADK Agent Demo: {APP_NAME} ---")
    
    # User Request from CLI or default
    if len(sys.argv) > 1:
        user_prompt = sys.argv[1]
    else:
        user_prompt = "Design a Kubernetes Worker Node that contains two Pods."
    
    print(f"User: {user_prompt}")
    
    user_content = types.Content(role='user', parts=[types.Part(text=user_prompt)])
    
    # Run the agent (Handling the conversation loop)
    async for event in runner.run_async(user_id=USER_ID, session_id=SESSION_ID, new_message=user_content):
        # The Runner automatically handles tool calling loops!
        pass
        
    # Get the final result from the session state
    session = await session_service.get_session(app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID)
    final_output = session.state.get("final_xml_result")
    
    if final_output:
        print(f"\n[AGENT OUTPUT]\n{final_output}")
    else:
        print("\n[AGENT] No output or update generated.")

if __name__ == "__main__":
    asyncio.run(main())
