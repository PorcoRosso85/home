export default function Home() {
  return (
    <main style={{ padding: '2rem' }}>
      <h1>OpenNext STG on Cloudflare Workers</h1>
      <p>Minimal Next.js deployment with OpenNext adapter</p>
      <p>Deployed at: {new Date().toISOString()}</p>
    </main>
  )
}