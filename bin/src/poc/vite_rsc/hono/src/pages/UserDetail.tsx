import { fetchUserById } from '../data/users.ts'

type UserDetailProps = {
  id: string
}

export async function UserDetail({ id }: UserDetailProps) {
  const user = await fetchUserById(id)
  
  if (!user) {
    return (
      <div>
        <h1>User Not Found</h1>
        <p>User with ID {id} does not exist.</p>
        <a href="/users">&larr; Back to Users</a>
      </div>
    )
  }
  
  return (
    <div>
      <h1>{user.name}</h1>
      <dl>
        <dt>ID:</dt>
        <dd>{user.id}</dd>
        <dt>Email:</dt>
        <dd>{user.email}</dd>
        <dt>Bio:</dt>
        <dd>{user.bio}</dd>
      </dl>
      <a href="/users">&larr; Back to Users</a>
    </div>
  )
}