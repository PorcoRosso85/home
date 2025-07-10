#!/usr/bin/env node
// Minimal LSP wrapper - extracts only essential parts from LSMCP

import { spawn } from 'child_process';
import { readFileSync } from 'fs';
import { pathToFileURL } from 'url';
import path from 'path';

// Minimal LSP client (extracted from LSMCP)
class MinimalLSPClient {
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

// Global state
let client: MinimalLSPClient | null = null;

// Initialize based on file type
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
  
  client = new MinimalLSPClient(cmd, args);
  await client.request('initialize', {
    processId: process.pid,
    rootPath: process.cwd(),
    rootUri: pathToFileURL(process.cwd()).toString(),
    capabilities: {}
  });
  client.notify('initialized', {});
}

// Core functions
async function findReferences(filePath: string, line: number, _symbolName?: string) {
  await initForFile(filePath);
  
  const uri = pathToFileURL(path.resolve(filePath)).toString();
  const content = readFileSync(filePath, 'utf-8');
  const lines = content.split('\n');
  
  // Find column if not provided
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
    return resp.result.map((d: any) => ({
      file: d.uri.replace('file://', ''),
      line: d.range.start.line + 1,
      column: d.range.start.character
    }));
  }
  return [];
}

// LSP method implementations
async function getDiagnostics(filePath: string) {
  await initForFile(filePath);
  
  const uri = pathToFileURL(path.resolve(filePath)).toString();
  const content = readFileSync(filePath, 'utf-8');
  
  const ext = path.extname(filePath);
  const languageId = ext === '.py' ? 'python' : ext === '.ts' ? 'typescript' : 'javascript';
  
  // Open document
  client!.notify('textDocument/didOpen', {
    textDocument: { uri, languageId, version: 1, text: content }
  });
  
  // Wait a bit for diagnostics to be computed
  await new Promise(resolve => setTimeout(resolve, 1000));
  
  // Request diagnostics - note: this is a custom method, not standard LSP
  const resp = await client!.request('textDocument/diagnostic', {
    textDocument: { uri }
  });
  
  if (resp.result && resp.result.items) {
    return resp.result.items.map((d: any) => ({
      line: d.range.start.line + 1,
      column: d.range.start.character,
      severity: d.severity === 1 ? 'error' : d.severity === 2 ? 'warning' : 'info',
      message: d.message,
      source: d.source
    }));
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

async function rename(filePath: string, line: number, column: number, newName: string) {
  await initForFile(filePath);
  
  const uri = pathToFileURL(path.resolve(filePath)).toString();
  const content = readFileSync(filePath, 'utf-8');
  
  const ext = path.extname(filePath);
  const languageId = ext === '.py' ? 'python' : ext === '.ts' ? 'typescript' : 'javascript';
  
  client!.notify('textDocument/didOpen', {
    textDocument: { uri, languageId, version: 1, text: content }
  });
  
  const resp = await client!.request('textDocument/rename', {
    textDocument: { uri },
    position: { line: line - 1, character: column },
    newName: newName
  });
  
  if (resp.result && resp.result.changes) {
    const changes: any[] = [];
    for (const [fileUri, edits] of Object.entries(resp.result.changes)) {
      changes.push({
        file: fileUri.replace('file://', ''),
        edits: edits.map((e: any) => ({
          line: e.range.start.line + 1,
          column: e.range.start.character,
          oldText: content.substring(
            content.split('\n').slice(0, e.range.start.line).join('\n').length + e.range.start.character,
            content.split('\n').slice(0, e.range.end.line).join('\n').length + e.range.end.character
          ),
          newText: e.newText
        }))
      });
    }
    return changes;
  }
  return [];
}

// Main
async function main() {
  try {
    const code = process.argv[2];
    if (!code) {
      console.error('Usage: node minimal-lsp.ts "await findReferences(...)"');
      process.exit(1);
    }
    
    const AsyncFunction = Object.getPrototypeOf(async function(){}).constructor;
    const fn = new AsyncFunction('findReferences', 'getDefinition', 'getDiagnostics', 'hover', 'rename', code);
    await fn(findReferences, getDefinition, getDiagnostics, hover, rename);
    
  } finally {
    if (client) client.close();
  }
}

main();