import { Link, useNavigate, useParams } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { ArrowLeft } from 'lucide-react'
import { adminApi } from '../../../features/admin'
import type { ProductInput } from '../../../features/admin'
import type { Category, Product } from '../../../entities/product'
import { Button } from '../../../shared/ui/Button'
import { Field } from '../../../shared/ui/Field'
import { ErrorState, Loading } from '../../../shared/ui/States'
import { FormError, PageHeading } from './AdminParts'
import { GalleryEditor } from './GalleryEditor'
import { VariantEditor } from './VariantEditor'

const categoryParams = new URLSearchParams({ limit: '100', is_active: 'true' })
const CURRENCIES = ['KZT', 'USD', 'EUR', 'RUB']

function productValues(form: HTMLFormElement): ProductInput {
  const data = new FormData(form)
  const text = (name: string) => String(data.get(name)).trim()
  return {
    name: text('name'),
    slug: text('slug') || undefined,
    description: text('description') || null,
    price: String(data.get('price')),
    currency: String(data.get('currency')),
    sku: text('sku'),
    stock: Number(data.get('stock')),
    audience: String(data.get('audience')) as Product['audience'],
    formality: (String(data.get('formality')) || null) as Product['formality'],
    color: text('color') || null,
    category_id: String(data.get('category_id')),
    is_active: data.get('is_active') === 'on',
  }
}

function ProductFields({ item, categories }: { item?: Product; categories: Category[] }) {
  return (
    <div className="grid gap-5 sm:grid-cols-2">
      <Field label="Название *">
        <input
          name="name"
          className="field"
          required
          minLength={2}
          maxLength={200}
          defaultValue={item?.name}
        />
      </Field>
      <Field label="Артикул *">
        <input
          name="sku"
          className="field"
          required
          minLength={2}
          maxLength={64}
          pattern="[A-Za-z0-9][A-Za-z0-9._\-]*"
          defaultValue={item?.sku}
        />
      </Field>
      <Field label="URL название">
        <input
          name="slug"
          className="field"
          pattern="[a-z0-9]+(-[a-z0-9]+)*"
          defaultValue={item?.slug}
          placeholder="Создастся автоматически"
        />
      </Field>
      <Field label="Категория *">
        <select name="category_id" className="field" required defaultValue={item?.category.id || ''}>
          <option value="">Выберите категорию</option>
          {categories.map((category) => (
            <option key={category.id} value={category.id}>
              {category.name}
            </option>
          ))}
        </select>
      </Field>
      <Field label="Цена *">
        <input
          name="price"
          className="field"
          required
          type="number"
          min="0"
          step="0.01"
          defaultValue={item?.price}
        />
      </Field>
      <Field label="Валюта">
        <select name="currency" className="field" defaultValue={item?.currency || 'KZT'}>
          {CURRENCIES.map((currency) => (
            <option key={currency}>{currency}</option>
          ))}
        </select>
      </Field>
      <Field label="Остаток без вариантов">
        <input
          name="stock"
          className="field"
          required
          type="number"
          min="0"
          defaultValue={item?.stock ?? 0}
        />
      </Field>
      <Field label="Для кого">
        <select name="audience" className="field" defaultValue={item?.audience || 'unisex'}>
          <option value="unisex">Для всех</option>
          <option value="women">Женщинам</option>
          <option value="men">Мужчинам</option>
        </select>
      </Field>
      <Field label="Стиль">
        <select name="formality" className="field" defaultValue={item?.formality || ''}>
          <option value="">Не указан</option>
          <option value="casual">Повседневный</option>
          <option value="smart_casual">Smart casual</option>
          <option value="formal">Строгий</option>
        </select>
      </Field>
      <Field label="Цвет">
        <input
          name="color"
          className="field"
          maxLength={64}
          defaultValue={item?.color || ''}
          placeholder="Например, black"
        />
      </Field>
      <Field label="Описание" className="sm:col-span-2">
        <textarea name="description" className="field h-28 py-3" defaultValue={item?.description || ''} />
      </Field>
    </div>
  )
}

export function AdminProductPage() {
  const { id = '' } = useParams()
  const isNew = id === 'new'
  const navigate = useNavigate()
  const client = useQueryClient()

  const product = useQuery({
    queryKey: ['admin', 'product', id],
    queryFn: () => adminApi.product(id),
    enabled: !isNew,
  })
  const categories = useQuery({
    queryKey: ['admin', 'active-categories'],
    queryFn: () => adminApi.categories(categoryParams),
  })
  const save = useMutation({
    mutationFn: (body: ProductInput) =>
      isNew ? adminApi.createProduct(body) : adminApi.updateProduct(id, body),
    onSuccess: async (value) => {
      await client.invalidateQueries({ queryKey: ['admin'] })
      await client.invalidateQueries({ queryKey: ['products'] })
      if (isNew) navigate(`/admin/products/${value.id}`, { replace: true })
    },
  })
  const refresh = () => {
    void client.invalidateQueries({ queryKey: ['admin', 'product', id] })
    void client.invalidateQueries({ queryKey: ['admin', 'products'] })
  }

  if (categories.isPending || (!isNew && product.isPending)) return <Loading />
  if (categories.error || product.error) {
    const retry = () => {
      void categories.refetch()
      void product.refetch()
    }
    return <ErrorState error={categories.error || product.error} retry={retry} />
  }

  const item = product.data
  const categoryList = categories.data?.items ?? []

  return (
    <section>
      <Link to="/admin/products" className="mb-5 inline-flex items-center gap-2 text-xs text-muted hover:text-ink">
        <ArrowLeft size={15} />
        К товарам
      </Link>
      <PageHeading title={isNew ? 'Новый товар' : 'Редактировать товар'} />
      {!categoryList.length && (
        <p className="mb-6 text-sm text-muted">
          Сначала <Link to="/admin/categories" className="underline">создайте категорию</Link>.
        </p>
      )}

      <form
        key={item?.id || 'new'}
        onSubmit={(event) => {
          event.preventDefault()
          save.mutate(productValues(event.currentTarget))
        }}
      >
        <ProductFields item={item} categories={categoryList} />
        <label className="mt-5 flex items-center gap-2 text-xs">
          <input name="is_active" type="checkbox" defaultChecked={item?.is_active ?? true} />
          Показывать в магазине
        </label>
        <div className="mt-6 flex flex-wrap items-center gap-4">
          <Button type="submit" disabled={save.isPending || !categoryList.length}>
            {save.isPending ? 'Сохраняем...' : isNew ? 'Создать товар' : 'Сохранить изменения'}
          </Button>
          {save.isSuccess && !isNew && (
            <span role="status" className="text-xs text-[#458052]">
              Изменения сохранены
            </span>
          )}
        </div>
        <FormError error={save.error} />
      </form>

      {item && (
        <>
          <section className="mt-11 border-t border-line pt-8">
            <div className="flex flex-wrap items-end justify-between gap-3">
              <h3 className="font-display text-3xl tracking-tight">Варианты</h3>
              <span className="text-xs text-muted">Размеры, цвета и отдельные остатки</span>
            </div>
            <div className="mt-4">
              {item.variants.map((variant) => (
                <VariantEditor key={variant.id} productId={item.id} variant={variant} onChanged={refresh} />
              ))}
              <VariantEditor key={`new-${item.variants.length}`} productId={item.id} onChanged={refresh} />
            </div>
          </section>
          <GalleryEditor product={item} onChanged={refresh} />
        </>
      )}
    </section>
  )
}
