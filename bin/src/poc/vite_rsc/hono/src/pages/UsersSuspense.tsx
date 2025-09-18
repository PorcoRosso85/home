'use client'

import { use, Suspense } from 'react'

type User = {
  id: number
  name: string
  email: string
}

const tableStyles = {
  table: {
    tableLayout: 'fixed' as const,
    width: '100%',
    maxWidth: '600px'
  },
  columns: {
    id: { width: '60px' },
    name: { width: '150px' },
    email: { width: '250px' }
  }
}

// Create a promise that fetches users
let usersPromise: Promise<User[]> | null = null

function fetchUsers(): Promise<User[]> {
  // Cache the promise to avoid refetching on every render
  if (!usersPromise) {
    usersPromise = fetch('/api/users')
      .then(res => {
        if (!res.ok) throw new Error('Failed to fetch')
        return res.json()
      })
  }
  return usersPromise
}

// Skeleton component for loading state (body only)
function UsersTableBodySkeleton() {
  const skeletonStyle = {
    backgroundColor: '#e0e0e0',
    animation: 'heartbeat 1.5s ease-in-out infinite',
    height: '20px',
    borderRadius: '4px'
  }

  return (
    <>
      <style>{`
        @keyframes heartbeat {
          0% { opacity: 0.3; transform: scale(1); }
          50% { opacity: 0.6; transform: scale(1.02); }
          100% { opacity: 0.3; transform: scale(1); }
        }
      `}</style>
      {[1, 2, 3].map(i => (
        <tr key={i}>
          <td style={tableStyles.columns.id}><div style={skeletonStyle}/></td>
          <td style={tableStyles.columns.name}><div style={skeletonStyle}/></td>
          <td style={tableStyles.columns.email}><div style={skeletonStyle}/></td>
        </tr>
      ))}
    </>
  )
}

// Component that uses the `use` hook (body only)
function UsersTableBody() {
  const users = use(fetchUsers())

  return (
    <>
      {users.map(user => (
        <tr key={user.id}>
          <td style={tableStyles.columns.id}>{user.id}</td>
          <td style={tableStyles.columns.name}>{user.name}</td>
          <td style={tableStyles.columns.email}>{user.email}</td>
        </tr>
      ))}
    </>
  )
}

// Main component with Suspense
export function UsersSuspense() {
  return (
    <div>
      <h1>Users (with Client Component + API)</h1>
      <table style={tableStyles.table}>
        <thead>
          <tr>
            <th style={tableStyles.columns.id}>ID</th>
            <th style={tableStyles.columns.name}>Name</th>
            <th style={tableStyles.columns.email}>Email</th>
          </tr>
        </thead>
        <tbody>
          <Suspense fallback={<UsersTableBodySkeleton />}>
            <UsersTableBody />
          </Suspense>
        </tbody>
      </table>
      <a href="/">&larr; Back to Home</a>
    </div>
  )
}
