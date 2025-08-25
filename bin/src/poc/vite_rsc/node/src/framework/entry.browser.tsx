import { createFromReadableStream } from '@vitejs/plugin-rsc/browser'
import { hydrateRoot } from 'react-dom/client'
import React from 'react'

async function hydrate() {
  const response = await fetch('/__rsc')
  const stream = response.body!
  const root = await createFromReadableStream(stream) as React.ReactElement
  
  hydrateRoot(document, root)
}

hydrate().catch(console.error)