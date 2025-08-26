import { createFromReadableStream } from '@vitejs/plugin-rsc/ssr';
import { renderToReadableStream } from 'react-dom/server.edge';
import React from 'react';

export async function handleSsr(
  rscStream: ReadableStream,
  bootstrapScriptContent?: string
): Promise<ReadableStream> {
  // Create React component from RSC stream
  const Component = await createFromReadableStream(rscStream) as React.ReactElement;
  
  // Extract the module path from bootstrapScriptContent if present
  // e.g., 'import("/assets/index-xxx.js")' -> '/assets/index-xxx.js'
  let bootstrapModules: string[] | undefined;
  if (bootstrapScriptContent) {
    const match = bootstrapScriptContent.match(/import\("([^"]+)"\)/);
    if (match && match[1]) {
      bootstrapModules = [match[1]];
    }
  }
  
  // Convert RSC component to HTML stream with client hydration
  return renderToReadableStream(Component, {
    // Use bootstrapModules for proper ESM loading
    bootstrapModules,
  });
}