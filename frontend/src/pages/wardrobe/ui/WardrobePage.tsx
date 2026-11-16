import { useState } from 'react'
import type { FormEvent } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { Plus, Search } from 'lucide-react'
import { useQuery } from '@tanstack/react-query'
import { productApi } from '../../../entities/product'
import { formalityLabels, wardrobeApi } from '../../../entities/wardrobe'
import type { WardrobeItem } from '../../../entities/wardrobe'
import { withFilter } from '../../../shared/lib/searchParams'
import { Button } from '../../../shared/ui/Button'
import { ErrorState, Loading } from '../../../shared/ui/States'
import { WardrobeItemCard } from './WardrobeItemCard'
import { WardrobeItemDialog } from './WardrobeItemDialog'

const PAGE_SIZE = 24
const FILTERS = ['search', 'category_id', 'formality'] as const

export function WardrobePage() {
  const [params, setParams] = useSearchParams()
  const [editing, setEditing] = useState<WardrobeItem | 'new' | null>(null)
  const page = Math.max(1, Number(params.get('page')) || 1)
  const offset = (page - 1) * PAGE_SIZE
  const filtered = FILTERS.some((name) => params.get(name))

  const query = new URLSearchParams({ limit: String(PAGE_SIZE), offset: String(offset) })
  for (const name of FILTERS) {
    const value = params.get(name)
    if (value) query.set(name, value)
  }
  const { data, error, isPending, refetch } = useQuery({
    queryKey: ['wardrobe', query.toString()],
    queryFn: () => wardrobeApi.list(query),
  })
  const { data: categoryData } = useQuery({ queryKey: ['categories'], queryFn: productApi.categories })
  const allCategories = categoryData?.items ?? []
  const categories = allCategories.filter((category) => category.is_active)
  const categoryName = (id: string | null) => allCategories.find((category) => category.id === id)?.name

  const setFilter = (name: string, value: string) => setParams(withFilter(params, name, value))
  function goTo(nextPage: number) {
    const next = new URLSearchParams(params)
    if (nextPage <= 1) next.delete('page')
    else next.set('page', String(nextPage))
    setParams(next)
  }
  function submitSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setFilter('search', String(new FormData(event.currentTarget).get('search')).trim())
  }

  return (
    <section>
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h2 className="font-display text-3xl tracking-tight">Мой гардероб</h2>
          <p className="mt-2 text-sm text-muted">Вещи, которые у вас уже есть.</p>
        </div>
        <Button onClick={() => setEditing('new')}>
          <Plus size={17} /> Добавить вещь
        </Button>
      </div>

      <div className="mt-6 grid gap-3 sm:grid-cols-[minmax(0,1fr)_200px_180px]">
        <form onSubmit={submitSearch} className="relative">
          <input
            key={params.get('search') ?? ''}
            name="search"
            type="search"
            maxLength={128}
            defaultValue={params.get('search') ?? ''}
            placeholder="Название, цвет, заметка"
            aria-label="Поиск по гардеробу"
            className="field pr-11"
          />
          <button
            type="submit"
            aria-label="Найти"
            className="absolute right-0 top-0 flex h-12 w-11 items-center justify-center text-muted hover:text-ink"
          >
            <Search size={17} />
          </button>
        </form>
        <select
          aria-label="Категория"
          className="field"
          value={params.get('category_id') ?? ''}
          onChange={(event) => setFilter('category_id', event.target.value)}
        >
          <option value="">Все категории</option>
          {categories.map((category) => (
            <option key={category.id} value={category.id}>
              {category.name}
            </option>
          ))}
        </select>
        <select
          aria-label="Стиль"
          className="field"
          value={params.get('formality') ?? ''}
          onChange={(event) => setFilter('formality', event.target.value)}
        >
          <option value="">Любой стиль</option>
          {Object.entries(formalityLabels).map(([value, label]) => (
            <option key={value} value={value}>
              {label}
            </option>
          ))}
        </select>
      </div>

      <div className="mt-8">
        {isPending ? (
          <Loading />
        ) : error ? (
          <ErrorState error={error} retry={() => refetch()} />
        ) : data.items.length ? (
          <>
            <p className="mb-4 text-xs text-muted">Вещей: {data.total}</p>
            <div className="grid grid-cols-2 gap-x-4 gap-y-8 sm:grid-cols-3 xl:grid-cols-4">
              {data.items.map((item) => (
                <WardrobeItemCard
                  key={item.id}
                  item={item}
                  categoryName={categoryName(item.category_id)}
                  onOpen={() => setEditing(item)}
                />
              ))}
            </div>
            <div className="mt-8 flex items-center gap-3">
              {offset > 0 && (
                <Button variant="outline" onClick={() => goTo(page - 1)}>
                  Назад
                </Button>
              )}
              {offset + PAGE_SIZE < data.total && (
                <Button variant="outline" onClick={() => goTo(page + 1)}>
                  Далее
                </Button>
              )}
            </div>
          </>
        ) : filtered ? (
          <p className="py-12 text-sm text-muted">
            Ничего не нашлось.{' '}
            <button
              type="button"
              onClick={() => setParams(new URLSearchParams())}
              className="text-ink underline underline-offset-4"
            >
              Сбросить фильтры
            </button>
          </p>
        ) : (
          <div className="border border-dashed border-line px-6 py-14 text-center">
            <h3 className="font-display text-3xl">Гардероб пока пуст</h3>
            <p className="mx-auto mt-3 max-w-md text-sm leading-6 text-muted">
              Добавьте вещи, которые у вас уже есть, или отметьте купленное на странице товара в{' '}
              <Link to="/catalog" className="text-ink underline underline-offset-4">
                каталоге
              </Link>
              .
            </p>
          </div>
        )}
      </div>

      {editing && (
        <WardrobeItemDialog
          item={editing === 'new' ? undefined : editing}
          categories={allCategories}
          onClose={() => setEditing(null)}
        />
      )}
    </section>
  )
}
