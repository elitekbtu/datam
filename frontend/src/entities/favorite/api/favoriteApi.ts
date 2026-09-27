import { api } from '../../../shared/api/client'
import type { Product } from '../../product'

export interface Favorites { items: Product[] }
export const favoriteApi = {
  read: () => api<Favorites>('/favorites'),
  add: (id: string) => api<Favorites>(`/favorites/${id}`, { method: 'PUT' }),
  remove: (id: string) => api<Favorites>(`/favorites/${id}`, { method: 'DELETE' }),
}
