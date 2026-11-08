import { useState } from 'react'
import type { FormEvent } from 'react'
import { useMutation } from '@tanstack/react-query'
import { ArrowDown, ArrowUp } from 'lucide-react'
import { adminApi } from '../../../features/admin'
import type { Product, ProductImage } from '../../../entities/product'
import { Button } from '../../../shared/ui/Button'
import { Field } from '../../../shared/ui/Field'
import { ConfirmButton, FormError } from './AdminParts'

const IMAGE_TYPES = 'image/jpeg,image/png,image/webp,image/avif,image/gif'

type ImageLink = { url: string; alt_text: string | null; variant_id: string | null; is_primary: boolean }

export function GalleryEditor({ product, onChanged }: { product: Product; onChanged: () => void }) {
  const [mode, setMode] = useState<'file' | 'url'>('file')
  const [variantId, setVariantId] = useState('')
  const upload = useMutation({
    mutationFn: (data: FormData) => adminApi.uploadImage(product.id, data),
    onSuccess: onChanged,
  })
  const add = useMutation({
    mutationFn: (data: ImageLink) => adminApi.addImage(product.id, data),
    onSuccess: onChanged,
  })
  const remove = useMutation({
    mutationFn: (id: string) => adminApi.deleteImage(product.id, id),
    onSuccess: onChanged,
  })
  const primary = useMutation({
    mutationFn: (id: string) => adminApi.primaryImage(product.id, id),
    onSuccess: onChanged,
  })
  const reorder = useMutation({
    mutationFn: (ids: string[]) => adminApi.orderImages(product.id, ids),
    onSuccess: onChanged,
  })

  const images = [...product.images, ...product.variants.flatMap((variant) => variant.images)].sort(
    (a, b) => a.position - b.position,
  )

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const form = event.currentTarget
    const data = new FormData(form)
    const resetForm = { onSuccess: () => form.reset() }
    if (mode === 'url') {
      add.mutate(
        {
          url: String(data.get('url')).trim(),
          alt_text: String(data.get('alt_text')).trim() || null,
          variant_id: variantId || null,
          is_primary: false,
        },
        resetForm,
      )
      return
    }
    if (!data.get('file')) return
    if (!variantId) data.delete('variant_id')
    upload.mutate(data, resetForm)
  }

  // Each variant has its own gallery, so photos only swap places within one variant.
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

  const galleryName = (image: ProductImage) =>
    image.variant_id
      ? product.variants.find((variant) => variant.id === image.variant_id)?.name
      : 'Общая галерея'
  const isLast = (image: ProductImage) =>
    !images.some((item) => item.variant_id === image.variant_id && item.position > image.position)
  const tabClass = (active: boolean) => (active ? 'font-medium underline underline-offset-4' : 'text-muted')

  return (
    <section className="mt-11 border-t border-line pt-8">
      <h3 className="font-display text-3xl tracking-tight">Фотографии</h3>
      <div className="mt-5 grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
        {images.map((image, index) => (
          <div key={image.id} className="border border-line">
            <img
              src={image.url}
              alt={image.alt_text || product.name}
              className="aspect-[4/3] w-full bg-mist object-cover"
            />
            <div className="space-y-2 p-3 text-xs">
              <p className="truncate text-muted">
                {galleryName(image)} · {image.is_primary ? 'Главная' : `Фото ${image.position + 1}`}
              </p>
              <div className="flex flex-wrap items-center gap-3">
                <button
                  type="button"
                  aria-label="Выше"
                  disabled={reorder.isPending || image.position === 0}
                  onClick={() => move(index, -1)}
                >
                  <ArrowUp size={15} />
                </button>
                <button
                  type="button"
                  aria-label="Ниже"
                  disabled={reorder.isPending || isLast(image)}
                  onClick={() => move(index, 1)}
                >
                  <ArrowDown size={15} />
                </button>
                {!image.is_primary && (
                  <button
                    type="button"
                    className="underline underline-offset-4"
                    disabled={primary.isPending}
                    onClick={() => primary.mutate(image.id)}
                  >
                    Сделать главной
                  </button>
                )}
                <ConfirmButton
                  label="Удалить"
                  disabled={remove.isPending}
                  onConfirm={() => remove.mutate(image.id)}
                />
              </div>
            </div>
          </div>
        ))}
      </div>
      {!images.length && <p className="mt-4 text-sm text-muted">Фотографий пока нет.</p>}

      <div className="mt-8">
        <h4 className="text-sm font-medium">Добавить фотографию</h4>
        <div className="mt-4 flex gap-4 text-xs">
          <button type="button" className={tabClass(mode === 'file')} onClick={() => setMode('file')}>
            Загрузить файл
          </button>
          <button type="button" className={tabClass(mode === 'url')} onClick={() => setMode('url')}>
            Указать ссылку
          </button>
        </div>
        <form onSubmit={submit} className="mt-4 grid gap-4 sm:grid-cols-2">
          {mode === 'file' ? (
            <Field label="Файл изображения *">
              <input name="file" type="file" accept={IMAGE_TYPES} required className="field h-auto py-3" />
            </Field>
          ) : (
            <Field label="Ссылка на изображение *">
              <input name="url" type="url" required className="field" placeholder="https://..." />
            </Field>
          )}
          <Field label="Для варианта">
            <select
              name="variant_id"
              className="field"
              value={variantId}
              onChange={(event) => setVariantId(event.target.value)}
            >
              <option value="">Общая галерея</option>
              {product.variants.map((variant) => (
                <option key={variant.id} value={variant.id}>
                  {variant.name}
                </option>
              ))}
            </select>
          </Field>
          <Field label="Описание изображения" className="sm:col-span-2">
            <input name="alt_text" className="field" maxLength={255} />
          </Field>
          <Button type="submit" disabled={upload.isPending || add.isPending}>
            Добавить фото
          </Button>
        </form>
        <FormError
          error={upload.error || add.error || remove.error || primary.error || reorder.error}
        />
      </div>
    </section>
  )
}
