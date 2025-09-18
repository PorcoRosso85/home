"use client";

import React from 'react'
import { hydrateRoot } from 'react-dom/client'
import App from './App.tsx'

// Use hydrateRoot for RSC hydration with React 19
// This connects client-side React to the server-rendered HTML from Document.server.tsx
hydrateRoot(
  document.getElementById('root')!,
  <React.StrictMode>
    <App />
  </React.StrictMode>
)