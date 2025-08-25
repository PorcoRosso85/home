import { createFromReadableStream } from '@vitejs/plugin-rsc/ssr';
import { renderToReadableStream } from 'react-dom/server.edge';

export async function handleSsr(
  rscStream: ReadableStream,
  bootstrapScriptContent?: string
): Promise<ReadableStream> {
  // Create React component from RSC stream
  const Component = await createFromReadableStream(rscStream);
  
  // Convert RSC component to HTML stream with client hydration
  return renderToReadableStream(Component, {
    bootstrapScriptContent,
  });
}