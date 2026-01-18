const xml2js = require('xml2js');
const fs = require('fs');

async function parseDrawio(xmlContent) {
    const parser = new xml2js.Parser();
    const result = await parser.parseStringPromise(xmlContent);

    // Navigate to root
    const root = result.mxfile?.diagram?.[0]?.mxGraphModel?.[0]?.root?.[0]?.mxCell;

    if (!root) {
        // Fallback for simple XML without mxfile wrapper
        const directRoot = result.mxGraphModel?.root?.[0]?.mxCell;
        if (directRoot) return processCells(directRoot);
        throw new Error("Invalid Draw.io XML format");
    }

    return processCells(root);
}

function processCells(cells) {
    const nodes = [];
    const edges = [];

    cells.forEach(cell => {
        const attrs = cell.$;
        if (!attrs) return;

        // Skip structural root elements (id="0", id="1")
        if (attrs.id === "0" || attrs.id === "1") return;

        if (attrs.edge === "1") {
            edges.push({
                id: attrs.id,
                source: attrs.source,
                target: attrs.target,
                style: attrs.style,
                value: attrs.value || ""
            });
        } else if (attrs.vertex === "1") {
            const geometry = cell.mxGeometry?.[0]?.$;
            nodes.push({
                id: attrs.id,
                value: attrs.value || "",
                style: attrs.style,
                width: geometry?.width,
                height: geometry?.height,
                x: geometry?.x,
                y: geometry?.y
            });
        }
    });

    return { nodes, edges };
}

module.exports = { parseDrawio };
