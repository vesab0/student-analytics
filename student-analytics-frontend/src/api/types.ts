// Mirrors backend schemas (app/schemas/user.py)
export type Role = 'student' | 'admin' | (string & {})

export interface User {
  id: number
  email: string
  role: Role
  is_active: boolean
  created_at: string
}

export interface Token {
  access_token: string
  token_type: string
  expires_in: number
}

export interface Credentials {
  email: string
  password: string
}
