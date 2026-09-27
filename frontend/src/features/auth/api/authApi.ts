import { api } from '../../../shared/api/client'
import type { User } from '../../../entities/user'

export const authApi = {
  login: (email: string, password: string) => api<User>('/auth/login', { method: 'POST', body: { email, password } }),
  register: (payload: { email: string; username: string; full_name: string | null; password: string }) => api<User>('/auth/register', { method: 'POST', body: payload }),
  logout: () => api<void>('/auth/logout', { method: 'POST' }),
}
