export default {
  async fetch(request: Request): Promise<Response> {
    return new Response('Built from TypeScript! 🚀', {
      headers: {
        'content-type': 'text/plain',
      },
    })
  },
}