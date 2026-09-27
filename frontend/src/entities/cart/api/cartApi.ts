import { api } from '../../../shared/api/client'
import type { Cart } from '../model/types'

export const cartApi = {
  read: () => api<Cart>('/cart'),
  add: (product_id: string, variant_id: string | null, quantity = 1) => api<Cart>('/cart/items', { method: 'POST', body: { product_id, variant_id, quantity } }),
  quantity: (id: string, quantity: number) => api<Cart>(`/cart/items/${id}`, { method: 'PATCH', body: { quantity } }),
  remove: (id: string) => api<Cart>(`/cart/items/${id}`, { method: 'DELETE' }),
}
