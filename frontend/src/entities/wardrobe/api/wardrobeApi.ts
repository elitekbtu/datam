import { api } from '../../../shared/api/client'
import type { Page } from '../../product'
import type { WardrobeItem, WardrobeItemPayload } from '../model/types'

const itemPath = (id: string) => `/wardrobe/${id}`

export const wardrobeApi = {
  list: (params: URLSearchParams) => api<Page<WardrobeItem>>(`/wardrobe?${params}`),
  create: (body: WardrobeItemPayload) => api<WardrobeItem>('/wardrobe', { method: 'POST', body }),
  fromProduct: (productId: string) =>
    api<WardrobeItem>('/wardrobe/from-product', { method: 'POST', body: { product_id: productId } }),
  update: (id: string, body: Partial<WardrobeItemPayload>) =>
    api<WardrobeItem>(itemPath(id), { method: 'PATCH', body }),
  remove: (id: string) => api<void>(itemPath(id), { method: 'DELETE' }),
  uploadPhoto: (id: string, body: FormData) =>
    api<WardrobeItem>(`${itemPath(id)}/photo`, { method: 'PUT', body }),
  removePhoto: (id: string) => api<WardrobeItem>(`${itemPath(id)}/photo`, { method: 'DELETE' }),
}
