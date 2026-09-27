import { useState } from 'react'
import type { FormEvent } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Plus } from 'lucide-react'
import { adminApi } from '../../../features/admin'
import type { CategoryInput } from '../../../features/admin'
import type { Category } from '../../../entities/product'
import { Button } from '../../../shared/ui/Button'
import { ErrorState, Loading } from '../../../shared/ui/States'
import { ConfirmButton, FormError, PageHeading, Pagination } from './AdminParts'

const limit = 20
const allParams = new URLSearchParams({ limit: '100' })

function values(form: HTMLFormElement): CategoryInput {
  const data = new FormData(form)
  return { name: String(data.get('name')).trim(), slug: String(data.get('slug')).trim() || undefined, description: String(data.get('description')).trim() || null, parent_id: String(data.get('parent_id')) || null, is_active: data.get('is_active') === 'on' }
}

function CategoryForm({ category, all, onDone }: { category?: Category; all: Category[]; onDone: () => void }) {
  const client = useQueryClient()
  const save = useMutation({ mutationFn: (body: CategoryInput) => category ? adminApi.updateCategory(category.id, body) : adminApi.createCategory(body), onSuccess: () => { void client.invalidateQueries({ queryKey: ['admin'] }); void client.invalidateQueries({ queryKey: ['categories'] }); onDone() } })
  return <form onSubmit={(event: FormEvent<HTMLFormElement>) => { event.preventDefault(); save.mutate(values(event.currentTarget)) }} className="mb-8 border border-line bg-mist p-5 sm:p-7"><h3 className="font-display text-2xl">{category ? 'Изменить категорию' : 'Новая категория'}</h3><div className="mt-5 grid gap-4 sm:grid-cols-2"><label><span className="field-label">Название *</span><input name="name" className="field" required minLength={2} maxLength={128} defaultValue={category?.name} /></label><label><span className="field-label">URL название</span><input name="slug" className="field" pattern="[a-z0-9]+(-[a-z0-9]+)*" defaultValue={category?.slug} placeholder="Создастся автоматически" /></label><label><span className="field-label">Родительская категория</span><select name="parent_id" className="field" defaultValue={category?.parent_id || ''}><option value="">Нет</option>{all.filter((item) => item.id !== category?.id).map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label><label className="sm:col-span-2"><span className="field-label">Описание</span><textarea name="description" className="field h-24 py-3" defaultValue={category?.description || ''} /></label></div><label className="mt-4 flex items-center gap-2 text-xs"><input name="is_active" type="checkbox" defaultChecked={category?.is_active ?? true} />Активна</label><div className="mt-5 flex gap-3"><Button type="submit" disabled={save.isPending}>{save.isPending ? 'Сохраняем...' : 'Сохранить'}</Button><Button type="button" variant="outline" onClick={onDone}>Отмена</Button></div><FormError error={save.error} /></form>
}

export function AdminCategoriesPage() {
  const [offset, setOffset] = useState(0)
  const [editing, setEditing] = useState<Category | 'new' | null>(null)
  const client = useQueryClient()
  const categories = useQuery({ queryKey: ['admin', 'categories', offset], queryFn: () => adminApi.categories(new URLSearchParams({ limit: String(limit), offset: String(offset) })) })
  const all = useQuery({ queryKey: ['admin', 'all-categories'], queryFn: () => adminApi.categories(allParams) })
  const remove = useMutation({ mutationFn: adminApi.deleteCategory, onSuccess: () => { void client.invalidateQueries({ queryKey: ['admin'] }); void client.invalidateQueries({ queryKey: ['categories'] }) } })
  return <section><PageHeading title="Категории" action={<Button type="button" onClick={() => setEditing('new')}><Plus size={17} />Добавить категорию</Button>} />{editing && <CategoryForm key={editing === 'new' ? 'new' : editing.id} category={editing === 'new' ? undefined : editing} all={all.data?.items ?? []} onDone={() => setEditing(null)} />}{categories.isPending ? <Loading /> : categories.error ? <ErrorState error={categories.error} retry={() => categories.refetch()} /> : <><div className="divide-y divide-line border-y border-line">{categories.data?.items.map((category) => <div key={category.id} className="flex flex-wrap items-center gap-4 py-5"><div className="min-w-[180px] flex-1"><h3 className="text-sm font-medium">{category.name}</h3><p className="mt-1 text-xs text-muted">/{category.slug}{category.parent_id ? ` · Вложенная в ${all.data?.items.find((item) => item.id === category.parent_id)?.name || 'категорию'}` : ''}</p></div><span className="text-xs text-muted">{category.is_active ? 'Активна' : 'Скрыта'}</span><button type="button" onClick={() => setEditing(category)} className="text-xs underline underline-offset-4">Изменить</button><ConfirmButton label="Удалить" disabled={remove.isPending} onConfirm={() => remove.mutate(category.id)} /></div>)}{!categories.data?.items.length && <p className="py-12 text-center text-sm text-muted">Категорий пока нет.</p>}</div><Pagination total={categories.data?.total ?? 0} offset={offset} limit={limit} onChange={setOffset} /></>}<FormError error={remove.error} /></section>
}
