import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Check, ShoppingBag } from 'lucide-react'
import { cartApi } from '../../../entities/cart'
import type { Product, ProductVariant } from '../../../entities/product'
import { money } from '../../../shared/lib/format'
import { Button } from '../../../shared/ui/Button'

export function AddToCart({ product }: { product: Product }) {
  const [selected, setSelected] = useState<ProductVariant | null>(null)
  const [message, setMessage] = useState('')
  const client = useQueryClient()
  const variants = product.variants.filter((variant) => variant.is_active).sort((a, b) => a.position - b.position)
  const price = selected?.price ?? product.price
  const mutation = useMutation({
    mutationFn: () => cartApi.add(product.id, selected?.id ?? null),
    onSuccess: (cart) => { client.setQueryData(['cart'], cart); setMessage('Товар добавлен в корзину') },
  })
  return <div>
    <p className="mt-3 text-2xl font-medium">{money(price, product.currency)}</p>
    {product.description && <p className="mt-5 max-w-md text-sm leading-6 text-muted">{product.description}</p>}
    {variants.length > 0 && <div className="mt-8 border-t border-line pt-6"><div className="mb-3 flex items-center justify-between"><span className="text-sm font-medium">Размер</span><span className="text-xs text-muted">Выберите размер</span></div><div className="flex flex-wrap gap-2">{variants.map((variant) => <button key={variant.id} type="button" disabled={variant.stock < 1} onClick={() => { setSelected(variant); setMessage('') }} aria-pressed={selected?.id === variant.id} className={`min-h-11 min-w-14 border px-3 text-sm transition-colors ${selected?.id === variant.id ? 'border-ink bg-ink text-white' : 'border-line hover:border-ink'} disabled:cursor-not-allowed disabled:opacity-35`}>{variant.options.size ?? variant.name}</button>)}</div></div>}
    <p className={`mt-5 text-xs ${product.total_stock ? 'text-[#458052]' : 'text-muted'}`}>{product.total_stock ? '● В наличии' : 'Нет в наличии'}</p>
    <div className="mt-5 flex gap-2"><Button full onClick={() => { setMessage(''); mutation.mutate() }} disabled={!product.total_stock || (variants.length > 0 && !selected) || mutation.isPending}><ShoppingBag size={17} />{mutation.isPending ? 'Добавляем...' : 'Добавить в корзину'}</Button></div>
    {message && <p role="status" className="mt-4 flex items-center gap-2 text-sm text-[#458052]"><Check size={16} />{message}</p>}
    {mutation.isError && <p role="alert" className="mt-3 text-sm text-red-700">{mutation.error.message}</p>}
    <p className="mt-7 border-t border-line pt-5 text-xs leading-5 text-muted">Бесплатная доставка по Казахстану. Оплата при получении.</p>
  </div>
}
