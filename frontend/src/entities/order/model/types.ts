export interface OrderItem { id: string; product_id: string; variant_id: string | null; name: string; sku: string; options: Record<string, string>; image_url: string | null; unit_price: string; quantity: number; total: string }
export type OrderStatus = 'placed' | 'processing' | 'shipped' | 'delivered' | 'cancelled'
export interface Order { id: string; status: OrderStatus; full_name: string; phone: string; city: string; address: string; postal_code: string | null; note: string | null; subtotal: string; total: string; currency: string; items: OrderItem[]; created_at: string }
export interface OrderPage { items: Order[]; total: number; limit: number; offset: number }
export interface OrderPayload { full_name: string; phone: string; city: string; address: string; postal_code: string | null; note: string | null }
