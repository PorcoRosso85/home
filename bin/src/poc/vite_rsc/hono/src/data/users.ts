// Shared data fetching logic
export async function fetchUsers() {
  // Simulate fetching from a database
  // In a real app, this would query your database
  await new Promise(resolve => setTimeout(resolve, 100))
  
  return [
    { id: 1, name: 'Alice', email: 'alice@example.com' },
    { id: 2, name: 'Bob', email: 'bob@example.com' },
    { id: 3, name: 'Charlie', email: 'charlie@example.com' },
  ]
}

export async function fetchUserById(id: string) {
  // Simulate fetching a single user from database
  await new Promise(resolve => setTimeout(resolve, 100))
  
  const users = {
    '1': { id: 1, name: 'Alice', email: 'alice@example.com', bio: 'Software engineer who loves React' },
    '2': { id: 2, name: 'Bob', email: 'bob@example.com', bio: 'Full-stack developer and open source contributor' },
    '3': { id: 3, name: 'Charlie', email: 'charlie@example.com', bio: 'DevOps engineer passionate about automation' },
  }
  
  return users[id as keyof typeof users] || null
}