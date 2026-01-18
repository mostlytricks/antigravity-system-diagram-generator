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
def search_templates(query: str) -> Dict[str, Any]:
    """
    Searches for specific diagram element styles (e.g., 'k8s pod', 'database').
    Returns the style string and default geometry.
    """
    print(f"\n[TOOL] Searching for template: '{query}'...")
    
    # Load library from external JSON file
    try:
        import json
        with open("library.json", "r") as f:
            library = json.load(f)
    except FileNotFoundError:
        print("[TOOL] Error: library.json not found. Using empty library.")
        library = {}
    
    # Simple fuzzy search
    query_lower = query.lower()
    for key, data in library.items():
        if key in query_lower:
            print(f"[TOOL] Found template for '{key}'")
            return data
            
    print(f"[TOOL] No template found for '{query}', returning default.")
    return {"style": "rounded=0;whiteSpace=wrap;html=1;", "width": 80, "height": 40}

# --- 3. Configure the Agent ---
# The Agent is the "Brain". It has an identity, instructions, and access to tools.

architect_agent = LlmAgent(
    model=MODEL_NAME,
    name="drawio_architect",
    description="An expert system architect that generates Draw.io XML.",
    instruction="""
    You are a Principal Diagram Architect.
    Your goal is to generate valid Draw.io XML for system architectures.
    
    ### Design Rules (CRITICAL)
    1.  **Clean Routing**: Edges should NOT cross through other Nodes (containers) unless absolutely necessary.
        - Place connected pods CLOSE to each other.
        - If a connection spans across containers, route it cleanly around others.
    2.  **Orthogonal Lines**: ALWAYS use the "connection" style from the library for edges.
    3.  **Container Layout**: 
        - Pods inside a Node should be arranged vertically or horizontally with padding.
        - Do not overlap Pods.
    
    ### Workflow
    1.  **Analyze** the user's request (e.g., "Draw a K8s Node with 2 Pods").
    2.  **Search** for the correct styles using `search_templates`. DO NOT GUESS STYLES.
        - If the user asks for "Pod", call `search_templates("k8s pod")`.
        - If the user asks for "Node", call `search_templates("k8s node")`.
    3.  **Construct** the XML. Use the styles and dimensions returned by the tool.
    4.  **Output** ONLY the valid XML string.
    """,
    tools=[search_templates], # Giving the agent "Hands"
    output_key="final_xml_result" # Where to store the result in the session state
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
        # Generate unique filename
        timestamp = int(time.time())
        output_path = f"generated/drawio_{timestamp}.drawio"
        
        # Ensure directory exists
        os.makedirs("generated", exist_ok=True)
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(final_output)
            
        # IMPORTANT: Print specific prefix for Node.js to capture
        print(f"OUTPUT_FILE: {output_path}")
        print(f"\n[SYSTEM] Saved generated diagram to: {output_path}")
    else:
        print("\n[AGENT] No output generated.")

if __name__ == "__main__":
    asyncio.run(main())
