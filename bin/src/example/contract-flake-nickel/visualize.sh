#!/usr/bin/env bash

# Contract Graph Visualization Script
# Exports Nickel graph to JSON and optionally converts to Graphviz format

set -euo pipefail

# Configuration
GRAPH_FILE="${1:-graph.ncl}"
OUTPUT_DIR="${2:-./output}"
EXPORT_FORMAT="${3:-json}"

# Colors for different node types
declare -A NODE_COLORS=(
    ["Producer"]="lightblue"
    ["Transformer"]="lightyellow"
    ["Consumer"]="lightgreen"
)

# Edge styles for different types
declare -A EDGE_STYLES=(
    ["Dependency"]="solid"
    ["Transform"]="dashed"
)

# Create output directory
mkdir -p "$OUTPUT_DIR"

echo "🔍 Exporting Nickel graph to JSON..."

# Export basic graph
echo "📊 Exporting basic graph..."
nickel export --format json --field basic "$GRAPH_FILE" > "$OUTPUT_DIR/basic_graph.json"
echo "✅ Basic graph exported to: $OUTPUT_DIR/basic_graph.json"

# Export large-scale graph
echo "📊 Exporting large-scale graph..."
nickel export --format json --field large_scale "$GRAPH_FILE" > "$OUTPUT_DIR/large_scale_graph.json"
echo "✅ Large-scale graph exported to: $OUTPUT_DIR/large_scale_graph.json"

# Function to convert JSON to DOT format
json_to_dot() {
    local json_file="$1"
    local dot_file="$2"
    local graph_name="$3"
    
    echo "🔄 Converting $json_file to Graphviz DOT format..."
    
    # Use jq to parse JSON and generate DOT
    cat > "$dot_file" << 'EOF'
digraph contract_graph {
    rankdir=TB;
    node [shape=box, style=filled];
    edge [fontsize=10];
    
EOF
    
    # Add nodes with colors based on type
    jq -r '.nodes[] | "    \"\(.id)\" [label=\"\(.id)\\n\(.contract.version)\\n\(.metadata.description)\", fillcolor=\"" + (if .type == "Producer" then "lightblue" elif .type == "Transformer" then "lightyellow" else "lightgreen" end) + "\"];"' "$json_file" >> "$dot_file"
    
    echo "" >> "$dot_file"
    
    # Add edges with styles based on type
    jq -r '.edges[] | "    \"\(.from)\" -> \"\(.to)\" [label=\"" + (.contract_requirements | join(",")) + "\", style=\"" + (if .type == "Dependency" then "solid" else "dashed" end) + "\"];"' "$json_file" >> "$dot_file"
    
    echo "}" >> "$dot_file"
    
    echo "✅ DOT file created: $dot_file"
}

# Function to generate statistics
generate_stats() {
    local json_file="$1"
    local stats_file="$2"
    
    echo "📈 Generating statistics for $json_file..."
    
    cat > "$stats_file" << EOF
# Contract Graph Statistics

Generated: $(date)
Source: $json_file

## Graph Metadata
$(jq -r '"\(.metadata.name) v\(.metadata.version)\n\(.metadata.description)"' "$json_file")

## Node Statistics
- Total Nodes: $(jq '.nodes | length' "$json_file")
- Producers: $(jq '[.nodes[] | select(.type == "Producer")] | length' "$json_file")
- Transformers: $(jq '[.nodes[] | select(.type == "Transformer")] | length' "$json_file")  
- Consumers: $(jq '[.nodes[] | select(.type == "Consumer")] | length' "$json_file")

## Edge Statistics
- Total Edges: $(jq '.edges | length' "$json_file")
- Dependencies: $(jq '[.edges[] | select(.type == "Dependency")] | length' "$json_file")
- Transforms: $(jq '[.edges[] | select(.type == "Transform")] | length' "$json_file")

## Contract Complexity
- Average Input Contracts per Node: $(jq '[.nodes[].contract.input | length] | add / length' "$json_file")
- Average Output Contracts per Node: $(jq '[.nodes[].contract.output | length] | add / length' "$json_file")
- Maximum Fan-out: $(jq '[.nodes[] | .contract.output | length] | max' "$json_file")
- Maximum Fan-in: $(jq '[.nodes[] | .contract.input | length] | max' "$json_file")

## Node Details
$(jq -r '.nodes[] | "- \(.id) (\(.type)): \(.contract.input | length) inputs → \(.contract.output | length) outputs"' "$json_file")

## Edge Details
$(jq -r '.edges[] | "- \(.from) → \(.to) (\(.type)): [\(.contract_requirements | join(", "))]"' "$json_file")
EOF
    
    echo "✅ Statistics generated: $stats_file"
}

# Convert JSON to DOT format
if command -v jq >/dev/null 2>&1; then
    echo "🎨 Converting to Graphviz format..."
    json_to_dot "$OUTPUT_DIR/basic_graph.json" "$OUTPUT_DIR/basic_graph.dot" "basic"
    json_to_dot "$OUTPUT_DIR/large_scale_graph.json" "$OUTPUT_DIR/large_scale_graph.dot" "large_scale"
    
    # Generate statistics
    generate_stats "$OUTPUT_DIR/basic_graph.json" "$OUTPUT_DIR/basic_stats.md"
    generate_stats "$OUTPUT_DIR/large_scale_graph.json" "$OUTPUT_DIR/large_scale_stats.md"
    
    # Generate SVG if graphviz is available
    if command -v dot >/dev/null 2>&1; then
        echo "🖼️  Generating SVG visualizations..."
        dot -Tsvg "$OUTPUT_DIR/basic_graph.dot" -o "$OUTPUT_DIR/basic_graph.svg"
        dot -Tsvg "$OUTPUT_DIR/large_scale_graph.dot" -o "$OUTPUT_DIR/large_scale_graph.svg"
        echo "✅ SVG files generated"
    else
        echo "⚠️  graphviz not found, skipping SVG generation"
    fi
else
    echo "⚠️  jq not found, skipping DOT format conversion"
fi

# Summary
echo ""
echo "📋 Summary:"
echo "- JSON exports: $OUTPUT_DIR/{basic,large_scale}_graph.json"
echo "- Statistics: $OUTPUT_DIR/{basic,large_scale}_stats.md"
if command -v jq >/dev/null 2>&1; then
    echo "- DOT files: $OUTPUT_DIR/{basic,large_scale}_graph.dot"
fi
if command -v dot >/dev/null 2>&1 && command -v jq >/dev/null 2>&1; then
    echo "- SVG visualizations: $OUTPUT_DIR/{basic,large_scale}_graph.svg"
fi

echo ""
echo "🎉 Contract graph visualization complete!"
echo "📁 All output files are in: $OUTPUT_DIR/"