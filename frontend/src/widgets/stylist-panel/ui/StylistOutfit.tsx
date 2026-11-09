import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Check, Plus } from 'lucide-react'
import { Link } from 'react-router-dom'
import { cartApi } from '../../../entities/cart'
import type { Outfit, OutfitItem } from '../../../features/stylist'
import { money } from '../../../shared/lib/format'

function OutfitProduct({ item, onNavigate }: { item: OutfitItem; onNavigate: () => void }) {
  const { product } = item
  const [size, setSize] = useState('')
  const client = useQueryClient()
  const variants = product.variants
    .filter((variant) => variant.is_active && variant.stock > 0)
    .sort((a, b) => a.position - b.position)
  const selected = variants.find((variant) => variant.id === size)
  const price = selected?.price ?? (variants.length ? item.price : product.price)
  const image = product.images.find((image) => image.is_primary) ?? product.images[0]
  const add = useMutation({
    mutationFn: () => cartApi.add(product.id, size || null),
    onSuccess: (cart) => client.setQueryData(['cart'], cart)
  })

  return (
    <div className="border-b border-line py-4 last:border-0">
      <div className="flex gap-3">
        <Link
          to={`/products/${product.slug}`}
          onClick={onNavigate}
          tabIndex={-1}
          aria-hidden="true"
          className="h-28 w-20 shrink-0 overflow-hidden bg-mist"
        >
          {image && <img src={image.url} alt="" loading="lazy" className="h-full w-full object-cover" />}
        </Link>
        <div className="min-w-0 flex-1">
          <Link
            to={`/products/${product.slug}`}
            onClick={onNavigate}
            className="text-xs leading-5 hover:underline underline-offset-4"
          >
            {product.name}
          </Link>
          <p className="mt-1 text-xs font-medium">
            {variants.length > 0 && !selected ? 'от ' : ''}
            {money(price, product.currency)}
          </p>
          {item.reason && <p className="mt-1.5 text-[11px] leading-4 text-muted">{item.reason}</p>}
          <div className="mt-3 flex items-center gap-2">
            {variants.length > 0 && (
              <select
                value={size}
                onChange={(event) => {
                  setSize(event.target.value)
                  add.reset()
                }}
                disabled={add.isPending}
                aria-label={`Размер: ${product.name}`}
                className="h-9 min-w-0 flex-1 border border-line bg-white px-2 text-[11px]"
              >
                <option value="">Размер</option>
                {variants.map((variant) => (
                  <option key={variant.id} value={variant.id}>
                    {variant.options.size ?? variant.name}
                  </option>
                ))}
              </select>
            )}
            <button
              type="button"
              aria-label={`Добавить ${product.name} в корзину`}
              onClick={() => add.mutate()}
              disabled={(variants.length > 0 && !selected) || add.isPending || add.isSuccess}
              className="flex min-h-9 items-center justify-center gap-1.5 border border-line px-3 text-[11px] transition hover:border-ink disabled:opacity-40"
            >
              {add.isSuccess ? <Check size={13} /> : <Plus size={13} />}
              {add.isPending ? 'Добавляем…' : add.isSuccess ? 'В корзине' : 'В корзину'}
            </button>
          </div>
        </div>
      </div>
      {add.isSuccess && (
        <p role="status" className="mt-2 text-[11px] text-muted">
          Добавлено в корзину
        </p>
      )}
      {add.isError && (
        <p role="alert" className="mt-2 text-xs text-red-700">
          {add.error.message}
        </p>
      )}
    </div>
  )
}

export function StylistOutfit({ outfit, onNavigate }: { outfit: Outfit; onNavigate: () => void }) {
  return (
    <article aria-label="Ответ стилиста">
      <p className="mb-3 text-[10px] uppercase tracking-[.18em] text-muted">DATAM · стилист</p>
      <h3 className="font-display text-2xl leading-tight tracking-[-.03em]">{outfit.title}</h3>
      {outfit.summary && (
        <p className="mt-3 whitespace-pre-wrap text-sm leading-6 text-muted">{outfit.summary}</p>
      )}
      <div className="mt-2">
        {outfit.items.map((item) => (
          <OutfitProduct key={item.product.id} item={item} onNavigate={onNavigate} />
        ))}
      </div>
      {outfit.notes.length > 0 && (
        <ul className="mt-3 space-y-2 border-l border-line pl-3 text-xs leading-5 text-muted">
          {outfit.notes.map((note) => (
            <li key={note}>{note}</li>
          ))}
        </ul>
      )}
      {outfit.items.length > 0 ? (
        <div className="mt-4 flex items-center justify-between text-xs">
          <span className="text-muted">Подборка от {money(outfit.total, outfit.currency)}</span>
          <Link to="/cart" onClick={onNavigate} className="underline underline-offset-4">
            Корзина
          </Link>
        </div>
      ) : (
        <Link
          to="/catalog"
          onClick={onNavigate}
          className="mt-4 inline-block text-xs underline underline-offset-4"
        >
          Посмотреть каталог
        </Link>
      )}
    </article>
  )
}
