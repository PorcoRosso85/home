export function Home() {
  return (
    <div>
      <h1>Home Page</h1>
      <p>Welcome to the RSC + Hono app!</p>
      <nav>
        <ul>
          <li><a href="/about">About</a></li>
          <li><a href="/users">Users (Client Component + API)</a></li>
          <li><a href="/users-ssr">Users (Server Component)</a></li>
          <li><a href="/counter">Counter</a></li>
        </ul>
      </nav>
    </div>
  )
}