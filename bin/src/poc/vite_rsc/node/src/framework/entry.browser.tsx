import { createFromReadableStream, createFromFetch } from '@vitejs/plugin-rsc/browser'
import { hydrateRoot } from 'react-dom/client'
import React from 'react'

async function main() {
  // Fetch RSC stream for the current page
  const rscResponse = await fetch(window.location.href + '.rsc')
  const root = await createFromReadableStream(rscResponse.body!) as React.ReactElement
  
  // Hydrate the server-rendered HTML with React
  hydrateRoot(document, root)
}

main().catch(console.error)