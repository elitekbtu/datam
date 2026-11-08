import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { adminApi } from '../../../features/admin'
import type { VariantInput } from '../../../features/admin'
import type { ProductVariant } from '../../../entities/product'
import { Button } from '../../../shared/ui/Button'
import { Field } from '../../../shared/ui/Field'
import { ConfirmButton, FormError } from './AdminParts'

function variantValues(form: HTMLFormElement): VariantInput {
  const data = new FormData(form)
  const text = (name: string) => String(data.get(name)).trim()
  const size = text('size')
  const color = text('color')
  return {
    name: text('name'),
    sku: text('sku'),
    options: { ...(size ? { size } : {}), ...(color ? { color } : {}) },
    price: text('price') || null,
    stock: Number(data.get('stock')),
    is_active: data.get('is_active') === 'on',
  }
}

type VariantEditorProps = { productId: string; variant?: ProductVariant; onChanged: () => void }

export function VariantEditor({ productId, variant, onChanged }: VariantEditorProps) {
  const [editing, setEditing] = useState(!variant)
  const save = useMutation({
    mutationFn: (body: VariantInput) =>
      variant
        ? adminApi.updateVariant(productId, variant.id, body)
        : adminApi.createVariant(productId, body),
    onSuccess: () => {
      onChanged()
      if (!variant) setEditing(false)
    },
  })
  const remove = useMutation({
    mutationFn: () => adminApi.deleteVariant(productId, variant!.id),
    onSuccess: onChanged,
  })

  if (!editing) {
    return (
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-line py-4 text-sm">
        <div>
          <strong className="font-medium">{variant?.name ?? 'Новый вариант'}</strong>
          <span className="ml-3 text-xs text-muted">
            {variant?.sku} · Остаток: {variant?.stock}
          </span>
        </div>
        <div className="flex gap-4">
          <button className="text-xs underline underline-offset-4" onClick={() => setEditing(true)}>
            Изменить
          </button>
          {variant && (
            <ConfirmButton
              label="Удалить"
              disabled={remove.isPending}
              onConfirm={() => remove.mutate()}
            />
          )}
        </div>
        <FormError error={remove.error} />
      </div>
    )
  }

  return (
    <form
      className="border-b border-line py-5"
      onSubmit={(event) => {
        event.preventDefault()
        save.mutate(variantValues(event.currentTarget))
      }}
    >
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
        <Field label="Название *">
          <input
            name="name"
            className="field"
            required
            maxLength={120}
            defaultValue={variant?.name}
            placeholder="Например, размер M"
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
            defaultValue={variant?.sku}
          />
        </Field>
        <Field label="Остаток">
          <input
            name="stock"
            className="field"
            type="number"
            min="0"
            required
            defaultValue={variant?.stock ?? 0}
          />
        </Field>
        <Field label="Размер">
          <input name="size" className="field" defaultValue={variant?.options.size || ''} />
        </Field>
        <Field label="Цвет">
          <input name="color" className="field" defaultValue={variant?.options.color || ''} />
        </Field>
        <Field label="Своя цена">
          <input
            name="price"
            className="field"
            type="number"
            min="0"
            step="0.01"
            defaultValue={variant?.price || ''}
            placeholder="Цена товара"
          />
        </Field>
      </div>
      <label className="mt-4 flex items-center gap-2 text-xs">
        <input name="is_active" type="checkbox" defaultChecked={variant?.is_active ?? true} />
        Активен
      </label>
      <div className="mt-4 flex gap-3">
        <Button type="submit" disabled={save.isPending}>
          {save.isPending ? 'Сохраняем...' : 'Сохранить вариант'}
        </Button>
        {variant && (
          <Button type="button" variant="outline" onClick={() => setEditing(false)}>
            Отмена
          </Button>
        )}
      </div>
      <FormError error={save.error} />
    </form>
  )
}
