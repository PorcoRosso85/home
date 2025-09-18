import { Hono } from 'hono'
import { rscRenderer } from './framework/rsc-renderer.tsx'
import { Home } from './pages/Home.tsx'
import { About } from './pages/About.tsx'
import { UsersSuspense } from './pages/UsersSuspense.tsx'
import { UsersSSR } from './pages/UsersSSR.tsx'
import { Counter } from './pages/Counter.tsx'
import { UserDetail } from './pages/UserDetail.tsx'

export const app = new Hono()

// Apply RSC renderer middleware
app.use(rscRenderer)

// Define routes with components
app.get('/', async (c) => {
  return c.render(<Home />)
})

app.get('/about', async (c) => {
  return c.render(<About />)
})

app.get('/users', async (c) => {
  return c.render(<UsersSuspense />)
})

app.get('/users-ssr', async (c) => {
  return c.render(<UsersSSR />)
})

app.get('/users/:id', async (c) => {
  const id = c.req.param('id')
  return c.render(<UserDetail id={id} />)
})

app.get('/counter', async (c) => {
  return c.render(<Counter />)
})

// API endpoints can also be added
app.get('/api/health', (c) => {
  return c.json({ status: 'ok', timestamp: new Date().toISOString() })
})

app.get('/api/users', async (c) => {
  // Use the shared data fetching function
  const { fetchUsers } = await import('./data/users.ts')
  const users = await fetchUsers()
  return c.json(users)
})

// 404 handler for unmatched paths
app.notFound((c) => {
  return c.render(
    <div>
      <h1>404 - Page Not Found</h1>
      <p>The page you are looking for does not exist.</p>
      <a href="/">Go to Home</a>
    </div>
  )
})
