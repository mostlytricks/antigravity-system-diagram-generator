const express = require('express');
const multer = require('multer');
const fs = require('fs');
const path = require('path');
const { parseDrawio } = require('./extract');
const { generateDrawio } = require('./generate');

require('dotenv').config();

const app = express();
const port = 3000;
const upload = multer({ dest: 'uploads/' });

app.use(express.static('public'));
app.use(express.json());

// 1. EXTRACT Endpoint
app.post('/api/extract', upload.single('file'), async (req, res) => {
    try {
        if (!req.file) return res.status(400).json({ error: 'No file uploaded' });

        const xmlContent = fs.readFileSync(req.file.path, 'utf8');
        const graphData = await parseDrawio(xmlContent);

        // Cleanup temp file
        fs.unlinkSync(req.file.path);

        res.json({ success: true, data: graphData });
    } catch (error) {
        console.error("Extraction error:", error);
        res.status(500).json({ error: error.message });
    }
});

// 2. GENERATE// Endpoint to generate diagram using ADK Agent (Python)
app.post('/api/generate', async (req, res) => {
    try {
        const { prompt, context } = req.body;
        console.log(`[Server] Generating for prompt: "${prompt}"`);

        // Escape double quotes in prompt for CLI safety (basic)
        const safePrompt = prompt.replace(/"/g, '\\"');
        const command = `python adk_agent_demo.py "${safePrompt}"`;

        const { exec } = require('child_process');

        exec(command, { cwd: __dirname + '/../' }, async (error, stdout, stderr) => {
            if (error) {
                console.error(`[Server] Agent Error: ${error.message}`);
                console.error(`[Server] Agent Stderr: ${stderr}`);
                return res.status(500).json({ error: 'Agent execution failed' });
            }

            console.log(`[Server] Agent Output:\n${stdout}`);

            // Parse the output filename from stdout
            const match = stdout.match(/OUTPUT_FILE: (.+)/);
            if (match && match[1]) {
                const filePath = match[1].trim();
                const absolutePath = path.resolve(__dirname, '../', filePath);

                try {
                    const xmlContent = await fs.promises.readFile(absolutePath, 'utf-8'); // Use fs.promises.readFile for async
                    res.send(xmlContent); // Return XML to frontend
                } catch (readError) {
                    console.error(`[Server] Read Error: ${readError.message}`);
                    res.status(500).json({ error: 'Failed to read generated file' });
                }
            } else {
                console.error("[Server] No output file reported by Agent");
                res.status(500).json({ error: 'Agent did not produce a file' });
            }
        });

    } catch (error) {
        console.error('Generation failed:', error);
        res.status(500).json({ error: 'Internal Server Error' });
    }
});

app.listen(port, () => {
    console.log(`Draw.io Agent running at http://localhost:${port}`);
});
