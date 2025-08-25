import { createFromReadableStream } from '@vitejs/plugin-rsc/browser'
import { hydrateRoot } from 'react-dom/client'

async function hydrate() {
  const response = await fetch('/__rsc')
  const stream = response.body!
  const root = await createFromReadableStream(stream)
  
  hydrateRoot(document, root)
}

hydrate().catch(console.error)