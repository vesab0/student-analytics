import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'
import AuthForm from './AuthForm'

export default function Login() {
  const { login } = useAuth()
  const navigate = useNavigate()
  return (
    <>
      <AuthForm
        title="Log in"
        submitLabel="Log in"
        onSubmit={async (email, password) => {
          await login({ email, password })
          navigate('/')
        }}
      />
      <p style={{ textAlign: 'center' }}>
        No account? <Link to="/register">Register</Link>
      </p>
    </>
  )
}
