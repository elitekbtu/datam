import { Link, useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { productApi } from '../../../entities/product'
import { AddToCart } from '../../../features/add-to-cart'
import { FavoriteButton } from '../../../features/favorite-toggle'
import { ProductGrid } from '../../../widgets/product-grid'
import { ErrorState, Loading } from '../../../shared/ui/States'

export function ProductPage() {
  const { slug = '' } = useParams()
  const { data: product, error, isPending, refetch } = useQuery({ queryKey: ['product', slug], queryFn: () => productApi.detail(slug) })
  const audience = product?.audience
  const { data: related } = useQuery({ queryKey: ['related', audience], queryFn: () => productApi.list(new URLSearchParams({ audience: audience!, limit: '6' })), enabled: Boolean(audience) })
  if (isPending) return <Loading />
  if (error || !product) return <ErrorState error={error} retry={() => refetch()} />
  const images = [...product.images].sort((a, b) => a.position - b.position)
  return <div className="page-container pt-5"><div className="grid gap-9 lg:grid-cols-[57%_minmax(0,1fr)] lg:gap-10"><div className="grid grid-cols-2 gap-2 self-start">{images.length ? images.map((image) => <div key={image.id} className="aspect-[4/5] overflow-hidden bg-mist"><img src={image.url} alt={image.alt_text || product.name} className="h-full w-full object-cover" /></div>) : <div className="col-span-2 flex aspect-square items-center justify-center bg-mist text-sm text-muted">Фото скоро появится</div>}</div><div className="lg:sticky lg:top-24 lg:self-start"><div className="mb-7 text-xs text-muted"><Link to="/" className="link-hover">Главная</Link><span className="mx-2">/</span><Link to={`/catalog?category=${product.category.slug}`} className="link-hover">{product.category.name}</Link></div><div className="flex items-start justify-between gap-3"><h1 className="font-display font-normal text-[44px] leading-[1.03] tracking-[-.05em] sm:text-[56px]">{product.name}</h1><FavoriteButton productId={product.id} className="border border-line shadow-none" /></div><AddToCart product={product} /><p className="mt-8 text-xs text-muted">Артикул: {product.sku}</p></div></div>
    <section className="mt-14 border-t border-line pt-9"><div className="grid gap-7 lg:grid-cols-[33%_1fr]"><h2 className="section-title">Детали</h2><div className="max-w-2xl text-sm leading-7 text-muted"><p>{product.description || 'Описание товара скоро появится.'}</p><p className="mt-4">Категория: {product.category.name}. Доступные размеры и наличие указаны выше.</p></div></div></section>
    {related?.items.some((item) => item.id !== product.id) && <section className="mt-16"><div className="mb-7 flex items-end justify-between"><h2 className="section-title">Вам может понравиться</h2><Link to={`/catalog?category=${product.category.slug}`} className="text-xs underline underline-offset-4">Смотреть всё</Link></div><ProductGrid products={related.items.filter((item) => item.id !== product.id).slice(0, 4)} /></section>}
  </div>
}
