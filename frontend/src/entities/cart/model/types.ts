export interface CartItem { id: string; product_id: string; variant_id: string | null; slug: string; name: string; sku: string; options: Record<string, string>; image_url: string | null; unit_price: string; quantity: number; total: string; available: boolean; stock: number; currency: string }
export interface Cart { items: CartItem[]; total: string; count: number }
