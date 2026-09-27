import { api } from '../../../shared/api/client'
import type { Category, Page, Product } from '../model/types'

export const productApi = {
  categories: () => api<Page<Category>>('/catalog/categories?limit=100'),
  list: (params: URLSearchParams) => api<Page<Product>>(`/catalog/products?${params}`),
  detail: (slug: string) => api<Product>(`/catalog/products/${encodeURIComponent(slug)}`),
}
