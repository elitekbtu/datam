import { useState } from 'react'
import type { FormEvent } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { ArrowLeft, ArrowDown, ArrowUp } from 'lucide-react'
import { adminApi } from '../../../features/admin'
import type { ProductInput, VariantInput } from '../../../features/admin'
import type { Product, ProductVariant } from '../../../entities/product'
import { Button } from '../../../shared/ui/Button'
import { ErrorState, Loading } from '../../../shared/ui/States'
import { ConfirmButton, FormError, PageHeading } from './AdminParts'

const categoryParams = new URLSearchParams({ limit: '100', is_active: 'true' })

function productValues(form: HTMLFormElement): ProductInput {
  const data = new FormData(form)
  const slug = String(data.get('slug')).trim()
  return {
    name: String(data.get('name')).trim(), slug: slug || undefined,
    description: String(data.get('description')).trim() || null,
    price: String(data.get('price')), currency: String(data.get('currency')),
    sku: String(data.get('sku')).trim(), stock: Number(data.get('stock')),
    audience: String(data.get('audience')) as Product['audience'],
    category_id: String(data.get('category_id')), is_active: data.get('is_active') === 'on',
  }
}

function variantValues(form: HTMLFormElement): VariantInput {
  const data = new FormData(form)
  const size = String(data.get('size')).trim()
  const color = String(data.get('color')).trim()
  const price = String(data.get('price')).trim()
  return { name: String(data.get('name')).trim(), sku: String(data.get('sku')).trim(), options: { ...(size ? { size } : {}), ...(color ? { color } : {}) }, price: price || null, stock: Number(data.get('stock')), is_active: data.get('is_active') === 'on' }
}

function VariantEditor({ productId, variant, onChanged }: { productId: string; variant?: ProductVariant; onChanged: () => void }) {
  const [editing, setEditing] = useState(!variant)
  const save = useMutation({ mutationFn: (body: VariantInput) => variant ? adminApi.updateVariant(productId, variant.id, body) : adminApi.createVariant(productId, body), onSuccess: () => { onChanged(); if (!variant) setEditing(false) } })
  const remove = useMutation({ mutationFn: () => adminApi.deleteVariant(productId, variant!.id), onSuccess: onChanged })
  if (!editing) return <div className="flex flex-wrap items-center justify-between gap-3 border-b border-line py-4 text-sm"><div><strong className="font-medium">{variant?.name ?? 'Новый вариант'}</strong><span className="ml-3 text-xs text-muted">{variant?.sku} · Остаток: {variant?.stock}</span></div><div className="flex gap-4"><button className="text-xs underline underline-offset-4" onClick={() => setEditing(true)}>Изменить</button>{variant && <ConfirmButton label="Удалить" disabled={remove.isPending} onConfirm={() => remove.mutate()} />}</div><FormError error={remove.error} /></div>
  return <form onSubmit={(event) => { event.preventDefault(); save.mutate(variantValues(event.currentTarget)) }} className="border-b border-line py-5"><div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3"><label><span className="field-label">Название *</span><input name="name" className="field" required maxLength={120} defaultValue={variant?.name} placeholder="Например, размер M" /></label><label><span className="field-label">Артикул *</span><input name="sku" className="field" required minLength={2} maxLength={64} pattern="[A-Za-z0-9][A-Za-z0-9._\-]*" defaultValue={variant?.sku} /></label><label><span className="field-label">Остаток</span><input name="stock" className="field" type="number" min="0" required defaultValue={variant?.stock ?? 0} /></label><label><span className="field-label">Размер</span><input name="size" className="field" defaultValue={variant?.options.size || ''} /></label><label><span className="field-label">Цвет</span><input name="color" className="field" defaultValue={variant?.options.color || ''} /></label><label><span className="field-label">Своя цена</span><input name="price" className="field" type="number" min="0" step="0.01" defaultValue={variant?.price || ''} placeholder="Цена товара" /></label></div><label className="mt-4 flex items-center gap-2 text-xs"><input name="is_active" type="checkbox" defaultChecked={variant?.is_active ?? true} />Активен</label><div className="mt-4 flex gap-3"><Button type="submit" disabled={save.isPending}>{save.isPending ? 'Сохраняем...' : 'Сохранить вариант'}</Button>{variant && <Button type="button" variant="outline" onClick={() => setEditing(false)}>Отмена</Button>}</div><FormError error={save.error} /></form>
}

function GalleryEditor({ product, onChanged }: { product: Product; onChanged: () => void }) {
  const [mode, setMode] = useState<'file' | 'url'>('file')
  const [variantId, setVariantId] = useState('')
  const upload = useMutation({ mutationFn: (data: FormData) => adminApi.uploadImage(product.id, data), onSuccess: onChanged })
  const add = useMutation({ mutationFn: (data: { url: string; alt_text: string | null; variant_id: string | null; is_primary: boolean }) => adminApi.addImage(product.id, data), onSuccess: onChanged })
  const remove = useMutation({ mutationFn: (id: string) => adminApi.deleteImage(product.id, id), onSuccess: onChanged })
  const primary = useMutation({ mutationFn: (id: string) => adminApi.primaryImage(product.id, id), onSuccess: onChanged })
  const reorder = useMutation({ mutationFn: (ids: string[]) => adminApi.orderImages(product.id, ids), onSuccess: onChanged })
  const images = [...product.images, ...product.variants.flatMap((variant) => variant.images)].sort((a, b) => a.position - b.position)
  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const form = event.currentTarget
    const data = new FormData(form)
    if (mode === 'file') { if (!data.get('file')) return; if (!variantId) data.delete('variant_id'); upload.mutate(data, { onSuccess: () => form.reset() }) }
    else add.mutate({ url: String(data.get('url')).trim(), alt_text: String(data.get('alt_text')).trim() || null, variant_id: variantId || null, is_primary: false }, { onSuccess: () => form.reset() })
  }
  function move(index: number, direction: -1 | 1) {
    const current = images[index]
    const group = images.filter((image) => image.variant_id === current.variant_id)
    const from = group.findIndex((image) => image.id === current.id)
    const target = from + direction
    if (target < 0 || target >= group.length) return
    const ordered = [...group]
    ;[ordered[from], ordered[target]] = [ordered[target], ordered[from]]
    reorder.mutate(ordered.map((image) => image.id))
  }
  return <section className="mt-11 border-t border-line pt-8"><h3 className="font-display text-3xl tracking-tight">Фотографии</h3><div className="mt-5 grid gap-4 sm:grid-cols-2 xl:grid-cols-3">{images.map((image, index) => <div key={image.id} className="border border-line"><img src={image.url} alt={image.alt_text || product.name} className="aspect-[4/3] w-full bg-mist object-cover" /><div className="space-y-2 p-3 text-xs"><p className="truncate text-muted">{image.variant_id ? product.variants.find((item) => item.id === image.variant_id)?.name : 'Общая галерея'} · {image.is_primary ? 'Главная' : `Фото ${image.position + 1}`}</p><div className="flex flex-wrap items-center gap-3"><button type="button" aria-label="Выше" disabled={reorder.isPending || image.position === 0} onClick={() => move(index, -1)}><ArrowUp size={15} /></button><button type="button" aria-label="Ниже" disabled={reorder.isPending || !images.some((item) => item.variant_id === image.variant_id && item.position > image.position)} onClick={() => move(index, 1)}><ArrowDown size={15} /></button>{!image.is_primary && <button type="button" className="underline underline-offset-4" disabled={primary.isPending} onClick={() => primary.mutate(image.id)}>Сделать главной</button>}<ConfirmButton label="Удалить" disabled={remove.isPending} onConfirm={() => remove.mutate(image.id)} /></div></div></div>)}</div>{!images.length && <p className="mt-4 text-sm text-muted">Фотографий пока нет.</p>}<div className="mt-8"><h4 className="text-sm font-medium">Добавить фотографию</h4><div className="mt-4 flex gap-4 text-xs"><button type="button" className={mode === 'file' ? 'font-medium underline underline-offset-4' : 'text-muted'} onClick={() => setMode('file')}>Загрузить файл</button><button type="button" className={mode === 'url' ? 'font-medium underline underline-offset-4' : 'text-muted'} onClick={() => setMode('url')}>Указать ссылку</button></div><form onSubmit={submit} className="mt-4 grid gap-4 sm:grid-cols-2"><label><span className="field-label">{mode === 'file' ? 'Файл изображения *' : 'Ссылка на изображение *'}</span>{mode === 'file' ? <input name="file" type="file" accept="image/jpeg,image/png,image/webp,image/avif,image/gif" required className="field h-auto py-3" /> : <input name="url" type="url" required className="field" placeholder="https://..." />}</label><label><span className="field-label">Для варианта</span><select name="variant_id" className="field" value={variantId} onChange={(event) => setVariantId(event.target.value)}><option value="">Общая галерея</option>{product.variants.map((variant) => <option key={variant.id} value={variant.id}>{variant.name}</option>)}</select></label><label className="sm:col-span-2"><span className="field-label">Описание изображения</span><input name="alt_text" className="field" maxLength={255} /></label><Button type="submit" disabled={upload.isPending || add.isPending}>Добавить фото</Button></form><FormError error={upload.error || add.error || remove.error || primary.error || reorder.error} /></div></section>
}

export function AdminProductPage() {
  const { id = '' } = useParams()
  const isNew = id === 'new'
  const navigate = useNavigate()
  const client = useQueryClient()
  const product = useQuery({ queryKey: ['admin', 'product', id], queryFn: () => adminApi.product(id), enabled: !isNew })
  const categories = useQuery({ queryKey: ['admin', 'active-categories'], queryFn: () => adminApi.categories(categoryParams) })
  const save = useMutation({ mutationFn: (body: ProductInput) => isNew ? adminApi.createProduct(body) : adminApi.updateProduct(id, body), onSuccess: async (value) => { await client.invalidateQueries({ queryKey: ['admin'] }); await client.invalidateQueries({ queryKey: ['products'] }); if (isNew) navigate(`/admin/products/${value.id}`, { replace: true }) } })
  const refresh = () => { void client.invalidateQueries({ queryKey: ['admin', 'product', id] }); void client.invalidateQueries({ queryKey: ['admin', 'products'] }) }
  if (categories.isPending || (!isNew && product.isPending)) return <Loading />
  if (categories.error || product.error) return <ErrorState error={categories.error || product.error} retry={() => { void categories.refetch(); void product.refetch() }} />
  const item = product.data
  return <section><Link to="/admin/products" className="mb-5 inline-flex items-center gap-2 text-xs text-muted hover:text-ink"><ArrowLeft size={15} />К товарам</Link><PageHeading title={isNew ? 'Новый товар' : 'Редактировать товар'} />{!categories.data?.items.length && <p className="mb-6 text-sm text-muted">Сначала <Link to="/admin/categories" className="underline">создайте категорию</Link>.</p>}<form key={item?.id || 'new'} onSubmit={(event) => { event.preventDefault(); save.mutate(productValues(event.currentTarget)) }}><div className="grid gap-5 sm:grid-cols-2"><label><span className="field-label">Название *</span><input name="name" className="field" required minLength={2} maxLength={200} defaultValue={item?.name} /></label><label><span className="field-label">Артикул *</span><input name="sku" className="field" required minLength={2} maxLength={64} pattern="[A-Za-z0-9][A-Za-z0-9._\-]*" defaultValue={item?.sku} /></label><label><span className="field-label">URL название</span><input name="slug" className="field" pattern="[a-z0-9]+(-[a-z0-9]+)*" defaultValue={item?.slug} placeholder="Создастся автоматически" /></label><label><span className="field-label">Категория *</span><select name="category_id" className="field" required defaultValue={item?.category.id || ''}><option value="">Выберите категорию</option>{categories.data?.items.map((category) => <option key={category.id} value={category.id}>{category.name}</option>)}</select></label><label><span className="field-label">Цена *</span><input name="price" className="field" required type="number" min="0" step="0.01" defaultValue={item?.price} /></label><label><span className="field-label">Валюта</span><select name="currency" className="field" defaultValue={item?.currency || 'KZT'}>{['KZT', 'USD', 'EUR', 'RUB'].map((currency) => <option key={currency}>{currency}</option>)}</select></label><label><span className="field-label">Остаток без вариантов</span><input name="stock" className="field" required type="number" min="0" defaultValue={item?.stock ?? 0} /></label><label><span className="field-label">Для кого</span><select name="audience" className="field" defaultValue={item?.audience || 'unisex'}><option value="unisex">Для всех</option><option value="women">Женщинам</option><option value="men">Мужчинам</option></select></label><label className="sm:col-span-2"><span className="field-label">Описание</span><textarea name="description" className="field h-28 py-3" defaultValue={item?.description || ''} /></label></div><label className="mt-5 flex items-center gap-2 text-xs"><input name="is_active" type="checkbox" defaultChecked={item?.is_active ?? true} />Показывать в магазине</label><div className="mt-6 flex flex-wrap items-center gap-4"><Button type="submit" disabled={save.isPending || !categories.data?.items.length}>{save.isPending ? 'Сохраняем...' : isNew ? 'Создать товар' : 'Сохранить изменения'}</Button>{save.isSuccess && !isNew && <span role="status" className="text-xs text-[#458052]">Изменения сохранены</span>}</div><FormError error={save.error} /></form>{item && <><section className="mt-11 border-t border-line pt-8"><div className="flex flex-wrap items-end justify-between gap-3"><h3 className="font-display text-3xl tracking-tight">Варианты</h3><span className="text-xs text-muted">Размеры, цвета и отдельные остатки</span></div><div className="mt-4">{item.variants.map((variant) => <VariantEditor key={variant.id} productId={item.id} variant={variant} onChanged={refresh} />)}<VariantEditor key={`new-${item.variants.length}`} productId={item.id} onChanged={refresh} /></div></section><GalleryEditor product={item} onChanged={refresh} /></>}</section>
}
