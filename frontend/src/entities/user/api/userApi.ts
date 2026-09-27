import { api } from '../../../shared/api/client'
import type { User } from '../model/types'

export const userApi = {
  session: () => api<User | null>('/auth/session', { method: 'POST' }),
  me: () => api<User>('/account'),
  update: (payload: { full_name: string | null; username: string; email: string }) => api<User>('/account', { method: 'PATCH', body: payload }),
  password: (payload: { current_password: string; new_password: string }) => api<void>('/account/password', { method: 'PUT', body: payload }),
  deactivate: () => api<void>('/account', { method: 'DELETE' }),
}
