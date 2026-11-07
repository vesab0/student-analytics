import { Link, Outlet } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'

export default function Layout() {
  const { user, logout } = useAuth()
  return (
    <>
      <nav style={{ display: 'flex', gap: 12, padding: 12 }}>
        <Link to="/">Dashboard</Link>
        {user?.role === 'admin' && <Link to="/admin">Admin</Link>}
        <span style={{ marginLeft: 'auto' }}>{user?.email}</span>
        <button onClick={logout}>Log out</button>
      </nav>
      <main style={{ padding: 12 }}>
        <Outlet />
      </main>
    </>
  )
}
