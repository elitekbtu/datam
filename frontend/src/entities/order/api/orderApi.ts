import { api } from '../../../shared/api/client'
import type { Order, OrderPage, OrderPayload } from '../model/types'

export const orderApi = {
  list: (offset = 0) => api<OrderPage>(`/orders?limit=20&offset=${offset}`),
  detail: (id: string) => api<Order>(`/orders/${id}`),
  place: (payload: OrderPayload, key: string) => api<Order>('/orders', { method: 'POST', headers: { 'Idempotency-Key': key }, body: payload }),
}
