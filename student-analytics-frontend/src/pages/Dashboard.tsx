import { useAuth } from '../auth/AuthContext'

export default function Dashboard() {
  const { user } = useAuth()
  return (
    <>
      <h1>Dashboard</h1>
      <p>Signed in as {user?.email} ({user?.role}). Analytics coming soon.</p>
    </>
  )
}
