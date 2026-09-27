import { api } from '../../../shared/api/client'
import type { AdminOrder, Category, CategoryInput, OrderDeliveryInput, OrderStatus, Page, Product, ProductInput, ProductVariant, User, UserInput, VariantInput } from '../model/types'

const admin = '/admin'
const catalog = `${admin}/catalog`
const productPath = (id: string) => `${catalog}/products/${encodeURIComponent(id)}`

export const adminApi = {
  categories: (params: URLSearchParams) => api<Page<Category>>(`${catalog}/categories?${params}`),
  createCategory: (body: CategoryInput) => api<Category>(`${catalog}/categories`, { method: 'POST', body }),
  updateCategory: (id: string, body: Partial<CategoryInput>) => api<Category>(`${catalog}/categories/${encodeURIComponent(id)}`, { method: 'PATCH', body }),
  deleteCategory: (id: string) => api<void>(`${catalog}/categories/${encodeURIComponent(id)}`, { method: 'DELETE' }),
  products: (params: URLSearchParams) => api<Page<Product>>(`${catalog}/products?${params}`),
  product: (id: string) => api<Product>(productPath(id)),
  createProduct: (body: ProductInput) => api<Product>(`${catalog}/products`, { method: 'POST', body }),
  updateProduct: (id: string, body: ProductInput) => api<Product>(productPath(id), { method: 'PATCH', body }),
  deleteProduct: (id: string) => api<void>(productPath(id), { method: 'DELETE' }),
  createVariant: (id: string, body: VariantInput) => api<ProductVariant>(`${productPath(id)}/variants`, { method: 'POST', body }),
  updateVariant: (id: string, variantId: string, body: VariantInput) => api<ProductVariant>(`${productPath(id)}/variants/${variantId}`, { method: 'PATCH', body }),
  deleteVariant: (id: string, variantId: string) => api<void>(`${productPath(id)}/variants/${variantId}`, { method: 'DELETE' }),
  addImage: (id: string, body: { url: string; alt_text: string | null; variant_id: string | null; is_primary: boolean }) => api<Product>(`${productPath(id)}/images`, { method: 'POST', body }),
  uploadImage: (id: string, body: FormData) => api<Product>(`${productPath(id)}/images/upload`, { method: 'POST', body }),
  deleteImage: (id: string, imageId: string) => api<Product>(`${productPath(id)}/images/${imageId}`, { method: 'DELETE' }),
  primaryImage: (id: string, imageId: string) => api<Product>(`${productPath(id)}/images/${imageId}/primary`, { method: 'PUT' }),
  orderImages: (id: string, image_ids: string[]) => api<Product>(`${productPath(id)}/images/order`, { method: 'PUT', body: { image_ids } }),
  orders: (params: URLSearchParams) => api<Page<AdminOrder>>(`${admin}/orders?${params}`),
  order: (id: string) => api<AdminOrder>(`${admin}/orders/${encodeURIComponent(id)}`),
  updateOrderDelivery: (id: string, body: OrderDeliveryInput) => api<AdminOrder>(`${admin}/orders/${encodeURIComponent(id)}`, { method: 'PATCH', body }),
  updateOrderStatus: (id: string, status: OrderStatus) => api<AdminOrder>(`${admin}/orders/${encodeURIComponent(id)}/status`, { method: 'PATCH', body: { status } }),
  users: (params: URLSearchParams) => api<Page<User>>(`${admin}/users?${params}`),
  createUser: (body: UserInput & { password: string }) => api<User>(`${admin}/users`, { method: 'POST', body }),
  updateUser: (id: string, body: Partial<UserInput> & { password?: string }) => api<User>(`${admin}/users/${id}`, { method: 'PATCH', body }),
  deleteUser: (id: string) => api<void>(`${admin}/users/${id}`, { method: 'DELETE' }),
}
