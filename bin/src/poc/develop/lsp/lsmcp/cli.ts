#!/usr/bin/env node
// LSP CLI wrapper - works with LSMCP source from Nix store

import { spawn } from 'child_process';
import { readFileSync } from 'fs';
import { pathToFileURL } from 'url';
import path from 'path';

// LSP client implementation
class LSPClient {
  private process: any;
  private messageId = 0;
  private responses = new Map<number, (value: any) => void>();
  private buffer = '';
  
  constructor(cmd: string, args: string[]) {
    this.process = spawn(cmd, args, { stdio: ['pipe', 'pipe', 'pipe'] });
    this.process.stdout.on('data', (data: Buffer) => {
      this.buffer += data.toString();
      this.processBuffer();
    });
    
    this.process.stderr.on('data', (data: Buffer) => {
      if (process.env.DEBUG) {
        console.error('LSP stderr:', data.toString());
      }
    });
  }
  
  private processBuffer() {
    while (true) {
      const match = this.buffer.match(/Content-Length: (\d+)\r\n/);
      if (!match) break;
      
      const contentLength = parseInt(match[1]);
      const headerEnd = this.buffer.indexOf('\r\n\r\n');
      if (headerEnd === -1) break;
      
      const contentStart = headerEnd + 4;
      const contentEnd = contentStart + contentLength;
      if (this.buffer.length < contentEnd) break;
      
      const content = this.buffer.substring(contentStart, contentEnd);
      this.buffer = this.buffer.substring(contentEnd);
      
      try {
        const msg = JSON.parse(content);
        if (msg.id && this.responses.has(msg.id)) {
          this.responses.get(msg.id)!(msg);
          this.responses.delete(msg.id);
        }
      } catch {}
    }
  }
  
  async request(method: string, params: any): Promise<any> {
    return new Promise((resolve) => {
      const id = ++this.messageId;
      this.responses.set(id, resolve);
      
      const msg = JSON.stringify({ jsonrpc: '2.0', id, method, params });
      this.process.stdin.write(`Content-Length: ${msg.length}\r\n\r\n${msg}`);
      
      setTimeout(() => {
        if (this.responses.has(id)) {
          this.responses.delete(id);
          resolve({ error: 'timeout' });
        }
      }, 5000);
    });
  }
  
  notify(method: string, params: any) {
    const msg = JSON.stringify({ jsonrpc: '2.0', method, params });
    this.process.stdin.write(`Content-Length: ${msg.length}\r\n\r\n${msg}`);
  }
  
  close() {
    this.process.kill();
  }
}

// Global client instance
let client: LSPClient | null = null;

// Initialize LSP based on file type
async function initForFile(filePath: string) {
  if (client) return;
  
  const ext = path.extname(filePath);
  let cmd: string, args: string[];
  
  switch (ext) {
    case '.py':
      cmd = 'pyright-langserver';
      args = ['--stdio'];
      break;
    case '.ts':
    case '.js':
      cmd = 'typescript-language-server';
      args = ['--stdio'];
      break;
    case '.rs':
      cmd = 'rust-analyzer';
      args = [];
      break;
    default:
      throw new Error(`Unsupported file type: ${ext}`);
  }
  
  client = new LSPClient(cmd, args);
  
  // Initialize
  await client.request('initialize', {
    processId: process.pid,
    rootPath: process.cwd(),
    rootUri: pathToFileURL(process.cwd()).toString(),
    capabilities: {}
  });
  
  client.notify('initialized', {});
}

// LSP operations
async function findReferences(filePath: string, line: number, _symbolName?: string) {
  await initForFile(filePath);
  
  const uri = pathToFileURL(path.resolve(filePath)).toString();
  const content = readFileSync(filePath, 'utf-8');
  const lines = content.split('\n');
  
  let column = 0;
  if (_symbolName && lines[line - 1]) {
    const idx = lines[line - 1].indexOf(_symbolName);
    if (idx >= 0) column = idx;
  }
  
  const ext = path.extname(filePath);
  const languageId = ext === '.py' ? 'python' : ext === '.ts' ? 'typescript' : 'javascript';
  
  client!.notify('textDocument/didOpen', {
    textDocument: { uri, languageId, version: 1, text: content }
  });
  
  // Wait for document processing
  await new Promise(resolve => setTimeout(resolve, 1000));
  
  const resp = await client!.request('textDocument/references', {
    textDocument: { uri },
    position: { line: line - 1, character: column },
    context: { includeDeclaration: true }
  });
  
  if (resp.result) {
    return resp.result.map((r: any) => ({
      file: r.uri.replace('file://', ''),
      line: r.range.start.line + 1,
      column: r.range.start.character
    }));
  }
  return [];
}

async function getDefinition(filePath: string, line: number, _symbolName?: string) {
  await initForFile(filePath);
  
  const uri = pathToFileURL(path.resolve(filePath)).toString();
  const content = readFileSync(filePath, 'utf-8');
  const lines = content.split('\n');
  
  let column = 0;
  if (_symbolName && lines[line - 1]) {
    const idx = lines[line - 1].indexOf(_symbolName);
    if (idx >= 0) column = idx;
  }
  
  const ext = path.extname(filePath);
  const languageId = ext === '.py' ? 'python' : ext === '.ts' ? 'typescript' : 'javascript';
  
  client!.notify('textDocument/didOpen', {
    textDocument: { uri, languageId, version: 1, text: content }
  });
  
  const resp = await client!.request('textDocument/definition', {
    textDocument: { uri },
    position: { line: line - 1, character: column }
  });
  
  if (resp.result) {
    const results = Array.isArray(resp.result) ? resp.result : [resp.result];
    return results.map((d: any) => ({
      file: d.uri.replace('file://', ''),
      line: d.range.start.line + 1,
      column: d.range.start.character
    }));
  }
  return [];
}

async function getDocumentSymbols(filePath: string) {
  await initForFile(filePath);
  
  const uri = pathToFileURL(path.resolve(filePath)).toString();
  const content = readFileSync(filePath, 'utf-8');
  const ext = path.extname(filePath);
  const languageId = ext === '.py' ? 'python' : ext === '.ts' ? 'typescript' : 'javascript';
  
  client!.notify('textDocument/didOpen', {
    textDocument: { uri, languageId, version: 1, text: content }
  });
  
  // Wait for processing
  await new Promise(resolve => setTimeout(resolve, 500));
  
  const resp = await client!.request('textDocument/documentSymbol', {
    textDocument: { uri }
  });
  
  if (resp.result) {
    return resp.result.map((s: any) => {
      const result: any = {
        name: s.name,
        kind: s.kind
      };
      
      // DocumentSymbol has 'range', SymbolInformation has 'location'
      if (s.range) {
        result.range = {
          start: { line: s.range.start.line + 1, character: s.range.start.character },
          end: { line: s.range.end.line + 1, character: s.range.end.character }
        };
      } else if (s.location && s.location.range) {
        result.range = {
          start: { line: s.location.range.start.line + 1, character: s.location.range.start.character },
          end: { line: s.location.range.end.line + 1, character: s.location.range.end.character }
        };
      }
      
      return result;
    });
  }
  return [];
}

async function hover(filePath: string, line: number, column?: number) {
  await initForFile(filePath);
  
  const uri = pathToFileURL(path.resolve(filePath)).toString();
  const content = readFileSync(filePath, 'utf-8');
  const ext = path.extname(filePath);
  const languageId = ext === '.py' ? 'python' : ext === '.ts' ? 'typescript' : 'javascript';
  
  client!.notify('textDocument/didOpen', {
    textDocument: { uri, languageId, version: 1, text: content }
  });
  
  const resp = await client!.request('textDocument/hover', {
    textDocument: { uri },
    position: { line: line - 1, character: column || 0 }
  });
  
  if (resp.result && resp.result.contents) {
    const contents = resp.result.contents;
    if (typeof contents === 'string') {
      return contents;
    } else if (contents.value) {
      return contents.value;
    }
  }
  return null;
}

// Main CLI
async function main() {
  try {
    const code = process.argv[2];
    if (!code) {
      console.error('Usage: cli.ts "<code to evaluate>"');
      console.error('Available functions:');
      console.error('  - findReferences(file, line, symbol?)');
      console.error('  - getDefinition(file, line, symbol?)');
      console.error('  - getDocumentSymbols(file)');
      console.error('  - hover(file, line, column?)');
      process.exit(1);
    }
    
    // Create async function with available operations
    const AsyncFunction = Object.getPrototypeOf(async function(){}).constructor;
    const fn = new AsyncFunction(
      'findReferences', 
      'getDefinition', 
      'getDocumentSymbols',
      'hover',
      code
    );
    
    await fn(findReferences, getDefinition, getDocumentSymbols, hover);
    
  } finally {
    if (client) client.close();
  }
}

main();