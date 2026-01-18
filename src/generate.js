const { GoogleGenerativeAI } = require('@google/generative-ai');
require('dotenv').config();

const genAI = new GoogleGenerativeAI(process.env.GOOGLE_API_KEY);
const model = genAI.getGenerativeModel({ model: "gemini-1.5-flash" }); // Using Flash for better availability

async function generateDrawio(prompt, contextNodes = []) {

    let systemInstruction = `
    You are an expert in Draw.io (mxGraph) XML format.
    Your goal is to generate a valid .drawio XML string based on the user's description.
    
    Output ONLY the raw XML string. Do not include markdown code fence blocks like \`\`\`xml.
    
    The XML should follow this structure:
    <mxGraphModel dx="1000" dy="1000" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="827" pageHeight="1169" math="0" shadow="0">
      <root>
        <mxCell id="0" />
        <mxCell id="1" parent="0" />
        <!-- Nodes and Edges go here -->
      </root>
    </mxGraphModel>

    Use standard simple shapes (rectangles, ellipses) unless specified.
    Ensure 'style' attributes are valid mxGraph styles.
    Position nodes logically so they don't overlap (simple auto-layout).
    `;

    if (contextNodes && contextNodes.length > 0) {
        systemInstruction += `\n\nHere is a list of existing node definitions (schema) you can use as reference for style and structure:\n${JSON.stringify(contextNodes, null, 2)}`;
    }

    try {
        const result = await model.generateContent({
            contents: [
                { role: 'user', parts: [{ text: systemInstruction + "\n\nUser Request: " + prompt }] }
            ]
        });

        const response = await result.response;
        let text = response.text();
        return text.replace(/```xml/g, '').replace(/```/g, '').trim();

    } catch (error) {
        console.warn("Gemini API failed or key missing. Using MOCK response.", error.message);

        // Return a mock XML for demonstration
        return `
            <mxGraphModel dx="1000" dy="1000" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="827" pageHeight="1169" math="0" shadow="0">
              <root>
                <mxCell id="0" />
                <mxCell id="1" parent="0" />
                <mxCell id="v1" value="Server 1 (Mock)" style="rounded=1;whiteSpace=wrap;html=1;" vertex="1" parent="1">
                  <mxGeometry x="100" y="100" width="120" height="60" as="geometry" />
                </mxCell>
                <mxCell id="v2" value="Server 2 (Mock)" style="rounded=1;whiteSpace=wrap;html=1;" vertex="1" parent="1">
                  <mxGeometry x="300" y="100" width="120" height="60" as="geometry" />
                </mxCell>
                <mxCell id="v3" value="Load Balancer" style="shape=ellipse;whiteSpace=wrap;html=1;" vertex="1" parent="1">
                  <mxGeometry x="200" y="250" width="80" height="80" as="geometry" />
                </mxCell>
                <mxCell id="e1" edge="1" parent="1" source="v1" target="v3">
                  <mxGeometry relative="1" as="geometry" />
                </mxCell>
                <mxCell id="e2" edge="1" parent="1" source="v2" target="v3">
                   <mxGeometry relative="1" as="geometry" />
                </mxCell>
              </root>
            </mxGraphModel>
        `;
    }
}

module.exports = { generateDrawio };
