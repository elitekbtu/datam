import type { Product } from '../../../entities/product'

export type OutfitAudience = 'women' | 'men'
export interface OutfitRequest { prompt: string; budget: number; audience: OutfitAudience | null }
export interface OutfitItem { product: Product; variant_id: string | null; price: string; reason: string | null }
export interface Outfit { title: string; summary: string; items: OutfitItem[]; total: string; budget: string; currency: string; notes: string[] }
