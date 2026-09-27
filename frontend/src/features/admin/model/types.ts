import type { Category, Page, Product, ProductVariant } from '../../../entities/product'
import type { User } from '../../../entities/user'

export type { Page, Product, Category, ProductVariant, User }

export type CategoryInput = {
  name: string; slug?: string; description: string | null; parent_id: string | null; is_active: boolean
}

export type ProductInput = {
  name: string; slug?: string; description: string | null; price: string; currency: string
  sku: string; stock: number; audience: Product['audience']; category_id: string; is_active: boolean
}

export type VariantInput = {
  name: string; sku: string; options: Record<string, string>; price: string | null
  stock: number; is_active: boolean
}

export type UserInput = {
  email: string; username: string; full_name: string | null; role: User['role']; is_active: boolean
}
