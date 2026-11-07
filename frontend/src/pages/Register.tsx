import { Link, useNavigate } from 'react-router-dom'
import { authApi } from '../api/auth'
import { useAuth } from '../auth/AuthContext'
import AuthForm from './AuthForm'

export default function Register() {
  const { login } = useAuth()
  const navigate = useNavigate()
  return (
    <>
      <AuthForm
        title="Register"
        submitLabel="Create account"
        onSubmit={async (email, password) => {
          await authApi.register({ email, password })
          await login({ email, password })
          navigate('/')
        }}
      />
      <p style={{ textAlign: 'center' }}>
        Have an account? <Link to="/login">Log in</Link>
      </p>
    </>
  )
}
