const { GoogleGenerativeAI } = require("@google/generative-ai");
require('dotenv').config();

// --- 1. TOOL DEFINITIONS (The "Hands") ---
// We define the function signatures that the model can call.

const tools = [
  {
    functionDeclarations: [
      {
        name: "search_templates",
        description: "Search for specific diagram element styles (e.g., 'k8s pod', 'database', 'azure server'). Returns the style string and geometry.",
        parameters: {
          type: "OBJECT",
          properties: {
            query: {
              type: "STRING",
              description: "The name of the component to look for."
            }
          },
          required: ["query"]
        }
      },
      {
        name: "validate_xml",
        description: "Validates if the generated XML string is well-formed and follows Draw.io structure.",
        parameters: {
          type: "OBJECT",
          properties: {
            xml: {
              type: "STRING",
              description: "The complete XML string to validate."
            }
          },
          required: ["xml"]
        }
      }
    ]
  }
];

// --- 2. EXECUTABLE FUNCTIONS (The "Muscle") ---
// These functions actually run when the model requests them.

const functions = {
  search_templates: async ({ query }) => {
    console.log(`[TOOL] Searching for: "${query}"...`);
    // MOCK: In a real app, this would query a Vector DB or file system
    const database = {
      "k8s pod": { style: "ellipse;whiteSpace=wrap;html=1;aspect=fixed;fillColor=#d5e8d4", width: 80, height: 80 },
      "k8s node": { style: "swimlane;whiteSpace=wrap;html=1;fillColor=#dae8fc", width: 200, height: 200 },
      "database": { style: "shape=cylinder3;whiteSpace=wrap;html=1;fillColor=#fff2cc", width: 100, height: 80 }
    };
    
    // Simple fuzzy match simulation
    const hit = Object.keys(database).find(k => k.includes(query.toLowerCase()));
    if (hit) return database[hit];
    return { error: "Style not found. Use standard rectangle." };
  },

  validate_xml: async ({ xml }) => {
    console.log(`[TOOL] Validating XML...`);
    if (xml.includes("<mxGraphModel") && xml.includes("</mxGraphModel>")) {
      return { valid: true, message: "Structure looks correct." };
    }
    return { valid: false, error: "Missing <mxGraphModel> tag." };
  }
};

// --- 3. SYSTEM INSTRUCTION (The "Brain") ---
// This defines the Agent's persona and workflow.

const systemInstruction = `
You are a Principal Diagram Architect. Your goal is to generate strictly valid Draw.io XML files.

### ARCHITECTURE
You are a "Tool-Using Agent". You DO NOT guess styles. You must:
1.  ANALYZE the user request.
2.  SEARCH for appropriate styles using \`search_templates\`.
3.  CONSTRUCT the XML using the retrieved styles.
4.  VALIDATE your output using \`validate_xml\` before returning it.

### CONSTRAINTS
- Output ONLY valid XML in the final response.
- If a style is not found, default to a simple white rectangle.
`;

async function runAgentDemo() {
  const genAI = new GoogleGenerativeAI(process.env.GOOGLE_API_KEY);
  const model = genAI.getGenerativeModel({ 
    model: "gemini-1.5-flash", // Support function calling
    systemInstruction: systemInstruction,
    tools: tools
  });

  const chat = model.startChat();
  const userPrompt = "Build a diagram with a Kubernetes Node containing one Pod.";

  console.log(`\nUser: "${userPrompt}"\n`);
  
  try {
    // 1st Turn: Agent thinks and might call tools
    let result = await chat.sendMessage(userPrompt);
    let response = await result.response;
    let functionCalls = response.functionCalls();

    // Loop to handle potentially multiple tool calls
    while (functionCalls && functionCalls.length > 0) {
      const toolParts = [];
      
      for (const call of functionCalls) {
        // Execute the tool
        const fn = functions[call.name];
        if (fn) {
           const toolResult = await fn(call.args);
           console.log(`[AGENT] Called ${call.name}(${JSON.stringify(call.args)}) -> Result:`, toolResult);
           
           // Pack result for the model
           toolParts.push({
             functionResponse: {
               name: call.name,
               response: { name: call.name, content: toolResult }
             }
           });
        }
      }

      // Send tool results back to the model
      result = await chat.sendMessage(toolParts);
      response = await result.response;
      functionCalls = response.functionCalls();
    }

    // Final Response (The generated XML)
    console.log("\n[AGENT] Final Output:\n");
    console.log(response.text());

  } catch (e) {
    console.error("Agent Error:", e);
  }
}

runAgentDemo();
