// Mock for @vitejs/plugin-rsc modules
// These are normally provided by the Vite RSC plugin

import React from 'react';

export function renderToReadableStream(element: React.ReactElement): ReadableStream {
  // Mock implementation for testing
  const encoder = new TextEncoder();
  const stream = new ReadableStream({
    start(controller) {
      controller.enqueue(encoder.encode('mock-rsc-stream'));
      controller.close();
    },
  });
  return stream;
}

export async function createFromReadableStream(stream: ReadableStream): Promise<React.ReactElement> {
  // Mock implementation for testing
  return React.createElement('div', null, 'Mock RSC Component');
}