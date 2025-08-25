import { app } from '../server.tsx'

export default app.fetch

if (import.meta.hot) {
  import.meta.hot.accept()
}