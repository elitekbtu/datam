import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Plus } from 'lucide-react'
import { adminApi } from '../../../features/admin'
import type { CategoryInput } from '../../../features/admin'
import type { Category } from '../../../entities/product'
import { Button } from '../../../shared/ui/Button'
import { Field } from '../../../shared/ui/Field'
import { ErrorState, Loading } from '../../../shared/ui/States'
import { ConfirmButton, FormError, PageHeading, Pagination } from './AdminParts'

const limit = 20
const allParams = new URLSearchParams({ limit: '100' })

function categoryValues(form: HTMLFormElement): CategoryInput {
  const data = new FormData(form)
  const text = (name: string) => String(data.get(name)).trim()
  return {
    name: text('name'),
    slug: text('slug') || undefined,
    description: text('description') || null,
    parent_id: String(data.get('parent_id')) || null,
    is_active: data.get('is_active') === 'on',
  }
}

type CategoryFormProps = { category?: Category; all: Category[]; onDone: () => void }

function CategoryForm({ category, all, onDone }: CategoryFormProps) {
  const client = useQueryClient()
  const save = useMutation({
    mutationFn: (body: CategoryInput) =>
      category ? adminApi.updateCategory(category.id, body) : adminApi.createCategory(body),
    onSuccess: () => {
      void client.invalidateQueries({ queryKey: ['admin'] })
      void client.invalidateQueries({ queryKey: ['categories'] })
      onDone()
    },
  })
  // A category cannot be its own parent.
  const parents = all.filter((item) => item.id !== category?.id)

  return (
    <form
      className="mb-8 border border-line bg-mist p-5 sm:p-7"
      onSubmit={(event) => {
        event.preventDefault()
        save.mutate(categoryValues(event.currentTarget))
      }}
    >
      <h3 className="font-display text-2xl">{category ? 'Изменить категорию' : 'Новая категория'}</h3>
      <div className="mt-5 grid gap-4 sm:grid-cols-2">
        <Field label="Название *">
          <input
            name="name"
            className="field"
            required
            minLength={2}
            maxLength={128}
            defaultValue={category?.name}
          />
        </Field>
        <Field label="URL название">
          <input
            name="slug"
            className="field"
            pattern="[a-z0-9]+(-[a-z0-9]+)*"
            defaultValue={category?.slug}
            placeholder="Создастся автоматически"
          />
        </Field>
        <Field label="Родительская категория">
          <select name="parent_id" className="field" defaultValue={category?.parent_id || ''}>
            <option value="">Нет</option>
            {parents.map((item) => (
              <option key={item.id} value={item.id}>
                {item.name}
              </option>
            ))}
          </select>
        </Field>
        <Field label="Описание" className="sm:col-span-2">
          <textarea name="description" className="field h-24 py-3" defaultValue={category?.description || ''} />
        </Field>
      </div>
      <label className="mt-4 flex items-center gap-2 text-xs">
        <input name="is_active" type="checkbox" defaultChecked={category?.is_active ?? true} />
        Активна
      </label>
      <div className="mt-5 flex gap-3">
        <Button type="submit" disabled={save.isPending}>
          {save.isPending ? 'Сохраняем...' : 'Сохранить'}
        </Button>
        <Button type="button" variant="outline" onClick={onDone}>
          Отмена
        </Button>
      </div>
      <FormError error={save.error} />
    </form>
  )
}

export function AdminCategoriesPage() {
  const [offset, setOffset] = useState(0)
  const [editing, setEditing] = useState<Category | 'new' | null>(null)
  const client = useQueryClient()

  const categories = useQuery({
    queryKey: ['admin', 'categories', offset],
    queryFn: () => adminApi.categories(new URLSearchParams({ limit: String(limit), offset: String(offset) })),
  })
  const all = useQuery({ queryKey: ['admin', 'all-categories'], queryFn: () => adminApi.categories(allParams) })
  const remove = useMutation({
    mutationFn: adminApi.deleteCategory,
    onSuccess: () => {
      void client.invalidateQueries({ queryKey: ['admin'] })
      void client.invalidateQueries({ queryKey: ['categories'] })
    },
  })

  const allCategories = all.data?.items ?? []
  const parentName = (category: Category) =>
    allCategories.find((item) => item.id === category.parent_id)?.name || 'категорию'

  const addButton = (
    <Button type="button" onClick={() => setEditing('new')}>
      <Plus size={17} />
      Добавить категорию
    </Button>
  )

  return (
    <section>
      <PageHeading title="Категории" action={addButton} />
      {editing && (
        <CategoryForm
          key={editing === 'new' ? 'new' : editing.id}
          category={editing === 'new' ? undefined : editing}
          all={allCategories}
          onDone={() => setEditing(null)}
        />
      )}

      {categories.isPending ? (
        <Loading />
      ) : categories.error ? (
        <ErrorState error={categories.error} retry={() => categories.refetch()} />
      ) : (
        <>
          <div className="divide-y divide-line border-y border-line">
            {categories.data?.items.map((category) => (
              <div key={category.id} className="flex flex-wrap items-center gap-4 py-5">
                <div className="min-w-[180px] flex-1">
                  <h3 className="text-sm font-medium">{category.name}</h3>
                  <p className="mt-1 text-xs text-muted">
                    /{category.slug}
                    {category.parent_id ? ` · Вложенная в ${parentName(category)}` : ''}
                  </p>
                </div>
                <span className="text-xs text-muted">{category.is_active ? 'Активна' : 'Скрыта'}</span>
                <button
                  type="button"
                  onClick={() => setEditing(category)}
                  className="text-xs underline underline-offset-4"
                >
                  Изменить
                </button>
                <ConfirmButton
                  label="Удалить"
                  disabled={remove.isPending}
                  onConfirm={() => remove.mutate(category.id)}
                />
              </div>
            ))}
            {!categories.data?.items.length && (
              <p className="py-12 text-center text-sm text-muted">Категорий пока нет.</p>
            )}
          </div>
          <Pagination total={categories.data?.total ?? 0} offset={offset} limit={limit} onChange={setOffset} />
        </>
      )}
      <FormError error={remove.error} />
    </section>
  )
}
