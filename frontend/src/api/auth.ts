import { request } from './client'
import type { Credentials, Token, User } from './types'

export const authApi = {
  register: (c: Credentials) =>
    request<User>('/auth/register', { method: 'POST', body: JSON.stringify(c) }),
  login: (c: Credentials) =>
    request<Token>('/auth/login', { method: 'POST', body: JSON.stringify(c) }),
  logout: () => request<void>('/auth/logout', { method: 'POST' }),
  me: () => request<User>('/auth/me'),
  users: () => request<User[]>('/auth/users'),
}
