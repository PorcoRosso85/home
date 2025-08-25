// Server Component that fetches from external API
// This demonstrates how to call external APIs from Server Components

async function fetchUsersFromAPI() {
  // In production, use environment variable for the base URL
  // For external APIs, this works fine. For same-origin during SSR, 
  // you'd need to know the actual host or use a different approach
  
  // Example: fetching from an external API
  // const response = await fetch('https://jsonplaceholder.typicode.com/users')
  
  // For demo: using the shared data function
  const { fetchUsers } = await import('../data/users.ts')
  return await fetchUsers()
}

export async function UsersSSR() {
  const users = await fetchUsersFromAPI()
  
  return (
    <div>
      <h1>Users (Server Component)</h1>
      <p>This is a Server Component that fetches data on the server.</p>
      <table>
        <thead>
          <tr>
            <th>ID</th>
            <th>Name</th>
            <th>Email</th>
          </tr>
        </thead>
        <tbody>
          {users.map((user: any) => (
            <tr key={user.id}>
              <td>{user.id}</td>
              <td>{user.name}</td>
              <td>{user.email}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <a href="/">&larr; Back to Home</a>
    </div>
  )
}