import type { Product } from '../../product'

export type Formality = NonNullable<Product['formality']>

export interface WardrobeItem {
  id: string
  name: string
  category_id: string | null
  product_id: string | null
  formality: Formality | null
  color: string | null
  note: string | null
  image_url: string | null
  created_at: string
  updated_at: string
}

export interface WardrobeItemPayload {
  name: string
  category_id: string | null
  formality: Formality | null
  color: string | null
  note: string | null
}

export const formalityLabels: Record<Formality, string> = {
  casual: 'Повседневный',
  smart_casual: 'Smart casual',
  formal: 'Строгий',
}
