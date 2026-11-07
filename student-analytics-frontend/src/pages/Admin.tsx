import { useEffect, useState } from 'react'
import { authApi } from '../api/auth'
import type { User } from '../api/types'

export default function Admin() {
  const [users, setUsers] = useState<User[]>([])
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    authApi.users().then(setUsers).catch((e: Error) => setError(e.message))
  }, [])

  return (
    <>
      <h1>Users</h1>
      {error && <p role="alert">{error}</p>}
      <table>
        <thead>
          <tr><th>ID</th><th>Email</th><th>Role</th><th>Active</th></tr>
        </thead>
        <tbody>
          {users.map((u) => (
            <tr key={u.id}>
              <td>{u.id}</td><td>{u.email}</td><td>{u.role}</td><td>{String(u.is_active)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </>
  )
}
