# Draw.io AI Architect Agent 🤖📐

> **An Intelligent Agent that "learns" your diagram styles and generates valid Draw.io XML.**

## 🎯 Project Vision
The goal of this project is **NOT** just to have an LLM guess XML structures.
The specific goal is to build an **Enterprise-Grade Diagram Agent** that:
1.  **Learns specific styles** from your existing `.drawio` files (e.g., "Our company uses *green cubes* for Severs and *blue swimlanes* for Kubernetes").
2.  **Generates valid Draw.io XML** that can be immediately opened and edited.
3.  **Visualizes results instantly** in a Web UI before you even download the file.

## 🏗️ Architecture

The system uses a **Hybrid Architecture** combining a Node.js Web App with a Google ADK (Agent Development Kit) Python Agent.

```mermaid
graph LR
    User[User] -->|Prompt| UI[Web UI (D3.js Preview)]
    UI -->|POST /api/generate| Server[Node.js Express Server]
    Server -->|Spawns| Agent[Python ADK Agent]
    
    subgraph "AI Brain (Google ADK)"
        Agent -->|1. Analyze Request| Model[Gemini 1.5 Pro]
        Model -->|2. Call Tool| Tool[search_templates()]
        Tool -->|3. Retrieve Style| Lib[library.json]
        Lib -->|Return Style| Model
        Model -->|4. Generate XML| Output[generated/drawio_TIMESTAMP.drawio]
    end
    
    Output -->|Return content| Server
    Server -->|Render| UI
```

### Key Components
1.  **Frontend (`public/index.html`)**:
    *   Simple "Teach" & "Build" interface.
    *   **D3.js Visualizer**: Renders the generated XML instantly in the browser. Supports custom styles like "Orthogonal Edges".
2.  **Backend (`src/server.js`)**:
    *   Acts as the bridge between the UI and the Python Agent.
    *   Handles file reading/writing and process execution.
3.  **The Agent (`adk_agent_demo.py`)**:
    *   Built with **Google Agent Development Kit (ADK)** logic.
    *   **Tool-Use**: It doesn't hallucinate styles. It calls `search_templates('k8s pod')` to get the *exact* XML style definition from `library.json`.
4.  **Style Database (`library.json`)**:
    *   A JSON extract of your accepted design components.
    *   Scalable: You can add new styles (AWS, Azure, etc.) here without retraining the model.

## 🚀 How to Use

### 1. Prerequisities
*   Node.js & npm
*   Python 3.9+
*   Google Gemini API Key

### 2. Setup
```bash
# Install Node dependencies
npm install

# Install Python dependencies (mock or real)
pip install google-adk google-generative-ai
```

### 3. Run the App
```bash
# Start the server (runs on localhost:3000)
node src/server.js
```

### 4. Workflows

#### A. The "Teach" Workflow (Extraction)
1.  Go to `http://localhost:3000`.
2.  Upload an existing `.drawio` file (e.g., `sample/web_architecture.drawio`).
3.  The D3 Visualizer will render it, proving the system effectively "understands" the nodes and edges.
4.  *(Future)*: Click "Add to Library" to save these styles to `library.json`.

#### B. The "Build" Workflow (Generation)
1.  Enter a prompt: *"Design a HA K8s Cluster with 2 Nodes and a Load Balancer."*
2.  Click **Generate**.
3.  The system calls the Python Agent -> Agent tools lookup styles -> Generates XML.
4.  The result appears instantly in the web view.
5.  Click **Download** to get the `.drawio` file.

## 📂 Project Structure
*   `adk_agent_demo.py`: The Main Agent logic (Tools + Instructions).
*   `library.json`: The "Knowledge Base" of diagram styles.
*   `src/server.js`: The API Server.
*   `public/`: The Frontend UI.
*   `generated/`: Folder where AI-created diagrams are saved.

---
*Created with the assistance of Antigravity Agent.*
