// Simple TypeScript to JavaScript transpiler for our SSG framework
// This script is used by the build process to compile .ts files to .js

// Function to transform TypeScript to JavaScript (simple transformation)
function transformTsToJs(tsContent: string): string {
  // Very basic transformation: just remove types and TypeScript-specific syntax
  let jsContent = tsContent
    // Remove TypeScript type annotations
    .replace(/:\s*[a-zA-Z0-9_<>\[\].,|& \(\)]+(?=[,)]|(?= =)| \|)/g, '')
    // Remove interface declarations
    .replace(/interface\s+\w+\s*\{[^}]*\}/g, '')
    // Remove type declarations
    .replace(/type\s+\w+\s*=\s*[^;]+;/g, '')
    // Remove import type statements
    .replace(/import\s+type\s+[^;]+;/g, '')
    // Remove export type statements
    .replace(/export\s+type\s+[^;]+;/g, '')
    // Remove generics
    .replace(/<[^>]+>/g, '')
    // Remove 'as' type assertions
    .replace(/\s+as\s+[a-zA-Z0-9_<>\[\].,|&]+/g, '');

  return jsContent;
}

// Main function
async function main() {
  // Get command line arguments
  const args = Deno.args;
  
  if (args.length < 1) {
    console.error("Usage: deno run transpile.ts <input.ts> [output.js]");
    Deno.exit(1);
  }
  
  const inputFile = args[0];
  const outputFile = args.length > 1 ? args[1] : inputFile.replace('.ts', '.js');
  
  try {
    // Read the TypeScript file
    const tsContent = await Deno.readTextFile(inputFile);
    
    // Transform it to JavaScript
    const jsContent = transformTsToJs(tsContent);
    
    // Write the JavaScript file
    await Deno.writeTextFile(outputFile, jsContent);
    
    console.log(`Successfully transpiled: ${inputFile} -> ${outputFile}`);
  } catch (error) {
    console.error(`Error transpiling file: ${error}`);
    Deno.exit(1);
  }
}

// Run the main function
if (import.meta.main) {
  await main();
}

export { transformTsToJs };
