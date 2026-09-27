import { useState } from 'react'
import type { FormEvent } from 'react'
import type { Category } from '../../../entities/product'

export function CatalogFilters({ categories, params, setParams }: { categories: Category[]; params: URLSearchParams; setParams: (next: URLSearchParams) => void }) {
  const [min, setMin] = useState(params.get('min_price') ?? '')
  const [max, setMax] = useState(params.get('max_price') ?? '')
  function set(name: string, value: string) { const next = new URLSearchParams(params); if (value) next.set(name, value); else next.delete(name); next.delete('page'); setParams(next) }
  function submit(event: FormEvent) { event.preventDefault(); const next = new URLSearchParams(params); if (min) next.set('min_price', min); else next.delete('min_price'); if (max) next.set('max_price', max); else next.delete('max_price'); next.delete('page'); setParams(next) }
  const active = params.get('category')
  const orderedCategories = categories.filter((category) => !category.parent_id).flatMap((parent) => [parent, ...categories.filter((category) => category.parent_id === parent.id)])
  return <div><div className="mb-6 flex items-center justify-between"><h2 className="text-base font-semibold">Фильтры</h2><button type="button" className="text-xs text-muted underline underline-offset-4" onClick={() => { setMin(''); setMax(''); setParams(new URLSearchParams()) }}>Сбросить всё</button></div>
    <div className="border-t border-line py-5"><h3 className="mb-4 text-sm font-medium">Категория</h3><div className="space-y-3"><button type="button" onClick={() => set('category', '')} className={`block text-left text-xs ${!active ? 'font-semibold text-ink' : 'text-muted hover:text-ink'}`}>Все категории</button>{orderedCategories.map((category) => <button key={category.id} type="button" onClick={() => set('category', category.slug)} className={`block text-left text-xs ${category.parent_id ? 'pl-4' : 'font-medium'} ${active === category.slug ? 'text-ink underline underline-offset-4' : 'text-muted hover:text-ink'}`}>{category.name}</button>)}</div></div>
    <form onSubmit={submit} className="border-t border-line py-5"><h3 className="mb-4 text-sm font-medium">Цена, ₸</h3><div className="flex gap-2"><label className="sr-only" htmlFor="min-price">От</label><input id="min-price" className="field h-10 min-w-0" type="number" min="0" placeholder="От" value={min} onChange={(event) => setMin(event.target.value)} /><label className="sr-only" htmlFor="max-price">До</label><input id="max-price" className="field h-10 min-w-0" type="number" min="0" placeholder="До" value={max} onChange={(event) => setMax(event.target.value)} /></div><button type="submit" className="mt-3 text-xs underline underline-offset-4">Применить</button></form>
    <div className="border-t border-line py-5"><label className="flex cursor-pointer items-center gap-3 text-xs"><input type="checkbox" checked={params.get('in_stock') === 'true'} onChange={(event) => set('in_stock', event.target.checked ? 'true' : '')} className="h-4 w-4 accent-ink" />Только в наличии</label></div>
  </div>
}
