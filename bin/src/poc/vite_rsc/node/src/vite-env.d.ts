/// <reference types="vite/client" />

// Vite RSC plugin types
interface ImportMetaViteRsc {
  loadModule<T = any>(environment: 'ssr' | 'rsc', entryName: string): Promise<T>
  loadBootstrapScriptContent(entryName: string): Promise<string>
}

interface ImportMeta {
  readonly viteRsc: ImportMetaViteRsc
}

// React Server DOM types for edge runtime
declare module 'react-dom/server.edge' {
  export function renderToReadableStream(
    element: React.ReactElement,
    options?: {
      bootstrapScriptContent?: string
      bootstrapScripts?: string[]
      bootstrapModules?: string[]
      identifierPrefix?: string
      namespaceURI?: string
      nonce?: string
      onError?: (error: unknown) => void
      progressiveChunkSize?: number
      signal?: AbortSignal
    }
  ): ReadableStream
}

// Virtual module types
declare module 'virtual:vite-rsc/server-references' {
  const serverReferences: Record<string, any>
  export default serverReferences
}