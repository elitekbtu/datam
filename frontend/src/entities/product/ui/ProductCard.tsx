import type { ReactNode } from 'react'
import { Link } from 'react-router-dom'
import { money } from '../../../shared/lib/format'
import type { Product } from '../model/types'

export function ProductCard({ product, favorite }: { product: Product; favorite?: ReactNode }) {
  const image = product.images.find((item) => item.is_primary) ?? product.images[0]
  return <article className="group min-w-0">
    <div className="relative overflow-hidden bg-mist">
      <Link to={`/products/${product.slug}`} aria-label={product.name} className="block aspect-[4/5] overflow-hidden">
        {image ? <img src={image.url} alt={image.alt_text || product.name} loading="lazy" className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-[1.025]" /> : <div className="flex h-full items-center justify-center text-xs text-muted">Фото скоро появится</div>}
      </Link>
      {favorite && <div className="absolute right-3 top-3">{favorite}</div>}
    </div>
    <Link to={`/products/${product.slug}`} className="mt-3 block text-[13px] leading-5 link-hover">{product.name}</Link>
    <p className="mt-0.5 text-[13px] font-semibold">{money(product.price, product.currency)}</p>
  </article>
}
