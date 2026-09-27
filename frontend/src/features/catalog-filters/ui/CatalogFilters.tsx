import { useState } from 'react'
import type { FormEvent } from 'react'
import { ChevronRight } from 'lucide-react'
import type { Category } from '../../../entities/product'

function categoryRows(categories: Category[], expanded: Map<string, boolean>, active: string | null) {
  const ids = new Set(categories.map((category) => category.id))
  const byId = new Map(categories.map((category) => [category.id, category]))
  const children = new Map<string | null, Category[]>()
  for (const category of categories) {
    const parent = category.parent_id && ids.has(category.parent_id) ? category.parent_id : null
    const siblings = children.get(parent) ?? []
    siblings.push(category)
    children.set(parent, siblings)
  }

  const activeAncestors = new Set<string>()
  let parentId = categories.find((category) => category.slug === active)?.parent_id
  while (parentId && byId.has(parentId) && !activeAncestors.has(parentId)) {
    activeAncestors.add(parentId)
    parentId = byId.get(parentId)?.parent_id
  }

  const rows: { category: Category; depth: number; hasChildren: boolean; isExpanded: boolean }[] = []
  const seen = new Set<string>()
  function visit(parent: string | null, depth: number) {
    for (const category of children.get(parent) ?? []) {
      if (seen.has(category.id)) continue
      seen.add(category.id)
      const hasChildren = Boolean(children.get(category.id)?.length)
      const isExpanded = depth === 0 || (expanded.get(category.id) ?? activeAncestors.has(category.id))
      rows.push({ category, depth, hasChildren, isExpanded })
      if (isExpanded) visit(category.id, depth + 1)
    }
  }
  visit(null, 0)
  return rows
}

export function CatalogFilters({ categories, params, setParams }: { categories: Category[]; params: URLSearchParams; setParams: (next: URLSearchParams) => void }) {
  const [expanded, setExpanded] = useState<Map<string, boolean>>(() => new Map())
  function set(name: string, value: string) { const next = new URLSearchParams(params); if (value) next.set(name, value); else next.delete(name); next.delete('page'); setParams(next) }
  function toggle(id: string, isExpanded: boolean) { setExpanded((current) => new Map(current).set(id, !isExpanded)) }
  function submitPrice(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const data = new FormData(event.currentTarget)
    const next = new URLSearchParams(params)
    for (const name of ['min_price', 'max_price']) {
      const value = String(data.get(name) ?? '').trim()
      if (value) next.set(name, value)
      else next.delete(name)
    }
    next.delete('page')
    setParams(next)
  }
  const active = params.get('category')
  const audience = params.get('audience')
  const orderedCategories = categoryRows(categories, expanded, active)
  return <div><div className="mb-6 flex items-center justify-between"><h2 className="text-base font-semibold">Фильтры</h2><button type="button" className="text-xs text-muted underline underline-offset-4" onClick={() => { setExpanded(new Map()); setParams(new URLSearchParams()) }}>Сбросить всё</button></div>
    <div className="border-t border-line py-5"><h3 className="mb-4 text-sm font-medium">Категория</h3><div className="space-y-3"><button type="button" onClick={() => set('category', '')} className={`block text-left text-xs ${!active ? 'font-semibold text-ink' : 'text-muted hover:text-ink'}`}>Все категории</button>{orderedCategories.map(({ category, depth, hasChildren, isExpanded }) => <div key={category.id} className="flex items-center gap-1" style={{ paddingLeft: depth * 16 }}><button type="button" onClick={() => set('category', category.slug)} className={`min-w-0 flex-1 text-left text-xs ${depth === 0 ? 'font-medium' : ''} ${active === category.slug ? 'text-ink underline underline-offset-4' : 'text-muted hover:text-ink'}`}>{category.name}</button>{depth > 0 && hasChildren && <button type="button" aria-label={`${isExpanded ? 'Скрыть' : 'Показать'} подкатегории: ${category.name}`} aria-expanded={isExpanded} onClick={() => toggle(category.id, isExpanded)} className="flex h-6 w-6 shrink-0 items-center justify-center text-muted hover:text-ink"><ChevronRight size={16} className={isExpanded ? 'rotate-90' : ''} /></button>}</div>)}</div></div>
    <div className="border-t border-line py-5"><h3 className="mb-4 text-sm font-medium">Для кого</h3><div className="space-y-3">{[{ value: '', label: 'Все' }, { value: 'women', label: 'Женщинам' }, { value: 'men', label: 'Мужчинам' }, { value: 'unisex', label: 'Унисекс' }].map((option) => <button key={option.value} type="button" onClick={() => set('audience', option.value)} className={`block text-left text-xs ${audience === (option.value || null) ? 'font-semibold text-ink underline underline-offset-4' : 'text-muted hover:text-ink'}`}>{option.label}</button>)}</div></div>
    <form key={`${params.get('min_price') ?? ''}:${params.get('max_price') ?? ''}`} onSubmit={submitPrice} className="border-t border-line py-5"><h3 className="mb-4 text-sm font-medium">Цена, ₸</h3><div className="flex gap-2"><label className="min-w-0 flex-1"><span className="sr-only">Цена от</span><input name="min_price" className="field h-10 min-w-0" type="number" min="0" step="0.01" placeholder="От" defaultValue={params.get('min_price') ?? ''} /></label><label className="min-w-0 flex-1"><span className="sr-only">Цена до</span><input name="max_price" className="field h-10 min-w-0" type="number" min="0" step="0.01" placeholder="До" defaultValue={params.get('max_price') ?? ''} /></label></div><button type="submit" className="mt-3 text-xs underline underline-offset-4">Применить</button></form>
    <div className="border-t border-line py-5"><label className="flex cursor-pointer items-center gap-3 text-xs"><input type="checkbox" checked={params.get('in_stock') === 'true'} onChange={(event) => set('in_stock', event.target.checked ? 'true' : '')} className="h-4 w-4 accent-ink" />Только в наличии</label></div>
  </div>
}
