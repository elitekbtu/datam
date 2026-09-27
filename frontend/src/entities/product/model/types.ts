export interface Category {
  id: string
  name: string
  slug: string
  description: string | null
  parent_id: string | null
  is_active: boolean
}

export interface ProductImage { id: string; url: string; alt_text: string | null; position: number; is_primary: boolean; variant_id: string | null }
export interface ProductVariant { id: string; name: string; sku: string; options: Record<string, string>; price: string | null; stock: number; is_active: boolean; position: number; images: ProductImage[] }
export interface Product {
  id: string; slug: string; name: string; description: string | null; price: string; currency: string
  sku: string; stock: number; total_stock: number; audience: 'women' | 'men' | 'unisex'
  category: Category; images: ProductImage[]; variants: ProductVariant[]; created_at: string; is_active: boolean
}
export interface Page<T> { items: T[]; total: number; limit: number; offset: number }
