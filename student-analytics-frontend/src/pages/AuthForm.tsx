import { useState, type FormEvent } from 'react'

interface Props {
  title: string
  submitLabel: string
  onSubmit: (email: string, password: string) => Promise<void>
}

export default function AuthForm({ title, submitLabel, onSubmit }: Props) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  async function handle(e: FormEvent) {
    e.preventDefault()
    setBusy(true)
    setError(null)
    try {
      await onSubmit(email, password)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong')
    } finally {
      setBusy(false)
    }
  }

  return (
    <form onSubmit={handle} style={{ display: 'grid', gap: 8, maxWidth: 320, margin: '10vh auto' }}>
      <h1>{title}</h1>
      <input type="email" placeholder="Email" value={email} onChange={(e) => setEmail(e.target.value)} required />
      <input type="password" placeholder="Password" value={password} onChange={(e) => setPassword(e.target.value)} minLength={8} required />
      {error && <p role="alert" style={{ color: 'crimson' }}>{error}</p>}
      <button disabled={busy}>{submitLabel}</button>
    </form>
  )
}
