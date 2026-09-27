import { ArrowRight } from 'lucide-react'
import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { productApi } from '../../../entities/product'
import { ProductGrid } from '../../../widgets/product-grid'
import { ErrorState, Loading } from '../../../shared/ui/States'

const categories = [
  { title: 'Женщинам', to: '/catalog?audience=women', image: '/images/blazer.webp' },
  { title: 'Мужчинам', to: '/catalog?audience=men', image: '/images/coat.webp' },
  { title: 'Обувь', to: '/catalog?category=shoes', image: '/images/sneakers.webp' },
  { title: 'Аксессуары', to: '/catalog?category=accessories', image: '/images/bag.webp' },
]

export function HomePage() {
  const params = new URLSearchParams({ limit: '8', sort: 'newest' })
  const { data, isPending, error, refetch } = useQuery({ queryKey: ['home-products'], queryFn: () => productApi.list(params) })
  return <>
    <section className="grid min-h-[500px] lg:grid-cols-[39%_61%] lg:min-h-[570px]">
      <div className="flex flex-col justify-center bg-[#f5f5f5] px-7 py-14 sm:px-12 lg:px-[max(3rem,calc((100vw-1400px)/2))]"><h1 className="display-title max-w-[560px]">Новый сезон.<br />Свой ритм.</h1><p className="mt-6 max-w-[290px] text-base leading-6 text-muted">Современная мода для твоих новых историй.</p><Link to="/catalog?sort=newest" className="mt-7 inline-flex min-h-[50px] w-fit items-center gap-4 bg-ink px-7 text-sm text-white shadow-sm transition-[transform,box-shadow] hover:-translate-y-0.5 hover:shadow-tactile">Смотреть коллекцию <ArrowRight size={18} /></Link></div>
      <div className="min-h-[400px] overflow-hidden bg-[#d7d7d7] lg:min-h-0"><img src="/images/hero.webp" alt="Новая коллекция DATAM" fetchPriority="high" className="h-full w-full object-cover object-center" /></div>
    </section>
    <section className="page-container pt-5"><h2 className="sr-only">Категории</h2><div className="grid grid-cols-2 gap-3 lg:grid-cols-4">{categories.map((category, index) => <Link key={category.title} to={category.to} className="group relative aspect-[1.25/1] overflow-hidden bg-mist sm:aspect-[1.5/1]"><img src={category.image} alt="" loading="lazy" className={`h-full w-full object-cover transition-transform duration-500 group-hover:scale-[1.04] ${index < 2 ? 'object-[center_22%]' : ''}`} /><span className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-black/55 to-transparent px-4 pb-4 pt-12 text-lg text-white sm:text-xl">{category.title} <ArrowRight size={17} className="ml-1 inline" /></span></Link>)}</div></section>
    <section className="page-container py-14 sm:py-20"><div className="mb-7 flex items-end justify-between"><h2 className="section-title">Новинки</h2><Link to="/catalog?sort=newest" className="hidden items-center gap-2 text-xs link-hover sm:inline-flex">Смотреть всё <ArrowRight size={16} /></Link></div>{isPending ? <Loading /> : error ? <ErrorState error={error} retry={() => refetch()} /> : data?.items.length ? <ProductGrid products={data.items.slice(0, 4)} /> : <p className="py-20 text-center text-sm text-muted">Новые вещи скоро появятся.</p>}</section>
    <section className="grid min-h-[410px] lg:grid-cols-[60%_40%]"><div className="min-h-[330px] overflow-hidden"><img src="/images/almaty.webp" alt="Стиль DATAM на фоне Алматы" loading="lazy" className="h-full w-full object-cover object-center" /></div><div className="flex flex-col justify-center bg-[#f5f5f6] px-8 py-14 sm:px-12"><h2 className="section-title">Город<br />в твоём ритме</h2><p className="mt-4 max-w-[320px] text-sm leading-6 text-muted">Коллекция для каждого дня и новых маршрутов.</p><Link to="/catalog" className="mt-6 inline-flex min-h-11 w-fit items-center gap-3 bg-ink px-6 text-xs text-white shadow-sm transition hover:-translate-y-0.5 hover:shadow-tactile">Смотреть коллекцию <ArrowRight size={15} /></Link></div></section>
  </>
}
