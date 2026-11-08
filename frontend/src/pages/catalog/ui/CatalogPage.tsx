import { useMemo } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { productApi } from '../../../entities/product'
import type { Category } from '../../../entities/product'
import { CatalogFilters } from '../../../features/catalog-filters'
import { ProductGrid } from '../../../widgets/product-grid'
import { withFilter } from '../../../shared/lib/searchParams'
import { EmptyState, ErrorState, Loading } from '../../../shared/ui/States'

const PAGE_SIZE = 12

const sortOptions = [
  ['newest', 'Сначала новые'],
  ['price', 'Сначала дешевле'],
  ['price_desc', 'Сначала дороже'],
  ['name', 'По названию'],
] as const

function catalogTitle(params: URLSearchParams, category: Category | undefined): string {
  if (params.get('search')) return 'Результаты поиска'
  if (category) return category.name
  if (params.get('audience') === 'women') return 'Женская коллекция'
  if (params.get('audience') === 'men') return 'Мужская коллекция'
  return 'Все товары'
}

function CollectionBanner({ audience }: { audience: 'women' | 'men' }) {
  return (
    <section className="mb-9 grid overflow-hidden bg-[#f2f2f2] sm:h-[270px] sm:grid-cols-[1fr_43%]">
      <div className="flex flex-col justify-center px-8 py-10 sm:px-12">
        <p className="text-[10px] uppercase tracking-[.25em] text-muted">Коллекция DATAM</p>
        <h2 className="mt-4 font-display text-[34px] font-normal leading-none tracking-[-.04em] sm:text-[43px]">
          Стиль в каждом
          <br />
          движении
        </h2>
        <p className="mt-4 max-w-[310px] text-sm leading-6 text-muted">
          Продуманные вещи на каждый день, в котором есть место новому.
        </p>
      </div>
      <div className="h-[230px] overflow-hidden sm:h-full">
        <img
          src={audience === 'women' ? '/images/ivory-blazer.webp' : '/images/coat.webp'}
          alt="Образ из коллекции DATAM"
          className="h-full w-full object-cover object-top"
        />
      </div>
    </section>
  )
}

type PageNavProps = { page: number; lastPage: number; onPage: (page: number) => void }

function PageNav({ page, lastPage, onPage }: PageNavProps) {
  if (lastPage <= 1) return null
  return (
    <nav aria-label="Страницы каталога" className="mt-12 flex items-center justify-center gap-2">
      {Array.from({ length: lastPage }, (_, index) => index + 1).map((number) => (
        <button
          key={number}
          type="button"
          aria-current={number === page ? 'page' : undefined}
          onClick={() => onPage(number)}
          className={`h-10 w-10 text-xs ${number === page ? 'bg-ink text-white' : 'border border-line hover:border-ink'}`}
        >
          {number}
        </button>
      ))}
    </nav>
  )
}

export function CatalogPage() {
  const [params, setParams] = useSearchParams()
  const page = Math.max(1, Number(params.get('page')) || 1)

  // The URL keeps a page number; the API wants limit/offset instead.
  const requestParams = useMemo(() => {
    const next = new URLSearchParams(params)
    next.delete('page')
    next.set('limit', String(PAGE_SIZE))
    next.set('offset', String((page - 1) * PAGE_SIZE))
    return next
  }, [params, page])

  const { data, error, isPending, refetch } = useQuery({
    queryKey: ['products', requestParams.toString()],
    queryFn: () => productApi.list(requestParams),
  })
  const { data: categoryData } = useQuery({ queryKey: ['categories'], queryFn: productApi.categories })

  const categories = categoryData?.items ?? []
  const category = categories.find((item) => item.slug === params.get('category'))
  const title = catalogTitle(params, category)
  const search = params.get('search')
  const audience = params.get('audience')
  const showBanner = !search && !params.get('category') && (audience === 'women' || audience === 'men')
  const lastPage = Math.ceil((data?.total ?? 0) / PAGE_SIZE)
  const tabs = [
    { name: 'Все товары', slug: '' },
    ...categories.filter((item) => !item.parent_id).map((item) => ({ name: item.name, slug: item.slug })),
  ]

  const update = (name: string, value: string) => setParams(withFilter(params, name, value))

  function goToPage(number: number) {
    const next = new URLSearchParams(params)
    next.set('page', String(number))
    setParams(next)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  return (
    <div className="page-container pb-10 pt-8">
      <div className="mb-7 text-xs text-muted">
        <Link to="/" className="link-hover">
          Главная
        </Link>
        <span className="mx-2">/</span>
        {title}
      </div>
      <div className="mb-9">
        <h1 className="display-title">{title}</h1>
        {search && <p className="mt-4 text-sm text-muted">По запросу «{search}»</p>}
      </div>

      {showBanner && <CollectionBanner audience={audience} />}

      <div className="mb-8 flex flex-wrap gap-x-6 gap-y-3 border-b border-line pb-4 text-xs">
        {tabs.map((item) => (
          <button
            type="button"
            key={item.name}
            onClick={() => update('category', item.slug)}
            className={
              params.get('category') === (item.slug || null)
                ? 'font-semibold underline underline-offset-[8px]'
                : 'text-muted hover:text-ink'
            }
          >
            {item.name}
          </button>
        ))}
      </div>

      <div className="grid gap-8 lg:grid-cols-[215px_minmax(0,1fr)] xl:grid-cols-[245px_minmax(0,1fr)]">
        <aside className="hidden lg:block">
          <CatalogFilters categories={categories} params={params} setParams={setParams} />
        </aside>
        <div className="min-w-0">
          <div className="mb-5 flex items-center justify-between gap-3">
            <p className="text-xs text-muted">{isPending ? 'Ищем товары...' : `${data?.total ?? 0} товаров`}</p>
            <div className="flex items-center gap-3">
              <details className="relative lg:hidden">
                <summary className="cursor-pointer list-none border border-line px-3 py-2 text-xs">Фильтры</summary>
                <div className="absolute right-0 top-11 z-20 w-[min(90vw,320px)] border border-line bg-white p-5 shadow-panel">
                  <CatalogFilters categories={categories} params={params} setParams={setParams} />
                </div>
              </details>
              <label className="sr-only" htmlFor="catalog-sort">
                Сортировка
              </label>
              <select
                id="catalog-sort"
                className="border border-line bg-white px-3 py-2 text-xs outline-none"
                value={params.get('sort') ?? 'newest'}
                onChange={(event) => update('sort', event.target.value)}
              >
                {sortOptions.map(([value, label]) => (
                  <option key={value} value={value}>
                    {label}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {isPending ? (
            <Loading />
          ) : error ? (
            <ErrorState error={error} retry={() => refetch()} />
          ) : data?.items.length ? (
            <ProductGrid products={data.items} />
          ) : (
            <EmptyState title="Ничего не найдено" body="Попробуйте изменить фильтры или посмотреть всю коллекцию." />
          )}
          <PageNav page={page} lastPage={lastPage} onPage={goToPage} />
        </div>
      </div>
    </div>
  )
}
