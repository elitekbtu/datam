import { useEffect, useRef, useState } from 'react'
import type { FormEvent } from 'react'
import { X } from 'lucide-react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import type { Category } from '../../../entities/product'
import { formalityLabels, wardrobeApi } from '../../../entities/wardrobe'
import type { Formality, WardrobeItem, WardrobeItemPayload } from '../../../entities/wardrobe'
import { Button } from '../../../shared/ui/Button'
import { Field } from '../../../shared/ui/Field'
import { IMAGE_TYPES } from '../../../shared/lib/upload'

type Props = { item?: WardrobeItem; categories: Category[]; onClose: () => void }

function text(values: FormData, name: string): string | null {
  return String(values.get(name) ?? '').trim() || null
}

export function WardrobeItemDialog({ item, categories, onClose }: Props) {
  const client = useQueryClient()
  const createdId = useRef<string | null>(null)
  const [photoUrl, setPhotoUrl] = useState(item?.image_url ?? null)
  const [confirmDelete, setConfirmDelete] = useState(false)
  const refresh = () => client.invalidateQueries({ queryKey: ['wardrobe'] })

  const save = useMutation({
    mutationFn: async ({ payload, photo }: { payload: WardrobeItemPayload; photo: File | null }) => {
      const id = item?.id ?? createdId.current
      let saved = id ? await wardrobeApi.update(id, payload) : await wardrobeApi.create(payload)
      createdId.current = saved.id
      if (photo) {
        const body = new FormData()
        body.append('file', photo)
        saved = await wardrobeApi.uploadPhoto(saved.id, body)
      }
      return saved
    },
    onSettled: refresh,
    onSuccess: onClose,
  })
  const removePhoto = useMutation({
    mutationFn: (id: string) => wardrobeApi.removePhoto(id),
    onSuccess: (saved) => {
      setPhotoUrl(saved.image_url)
      void refresh()
    },
  })
  const remove = useMutation({
    mutationFn: (id: string) => wardrobeApi.remove(id),
    onSuccess: () => {
      void refresh()
      onClose()
    },
  })

  useEffect(() => {
    const close = (event: KeyboardEvent) => event.key === 'Escape' && onClose()
    window.addEventListener('keydown', close)
    return () => window.removeEventListener('keydown', close)
  }, [onClose])

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const values = new FormData(event.currentTarget)
    const photo = values.get('file')
    save.mutate({
      payload: {
        name: String(values.get('name')).trim(),
        category_id: text(values, 'category_id'),
        formality: text(values, 'formality') as Formality | null,
        color: text(values, 'color'),
        note: text(values, 'note'),
      },
      photo: photo instanceof File && photo.size > 0 ? photo : null,
    })
  }

  const error = save.error || removePhoto.error || remove.error
  const busy = save.isPending || removePhoto.isPending || remove.isPending

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4" onClick={onClose}>
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="wardrobe-dialog-title"
        onClick={(event) => event.stopPropagation()}
        className="max-h-[92vh] w-full max-w-xl overflow-y-auto bg-white p-6 shadow-panel sm:p-8"
      >
        <div className="flex items-start justify-between gap-4">
          <h2 id="wardrobe-dialog-title" className="font-display text-3xl tracking-tight">
            {item ? 'Редактировать вещь' : 'Новая вещь'}
          </h2>
          <button type="button" aria-label="Закрыть" onClick={onClose} className="p-1 hover:bg-mist">
            <X size={20} />
          </button>
        </div>

        <form onSubmit={submit} className="mt-6 grid gap-5 sm:grid-cols-2">
          <Field label="Название *" className="sm:col-span-2">
            <input
              name="name"
              required
              maxLength={200}
              className="field"
              defaultValue={item?.name}
              placeholder="Например, белая рубашка"
              autoFocus
            />
          </Field>
          <Field label="Категория">
            <select name="category_id" className="field" defaultValue={item?.category_id ?? ''}>
              <option value="">Не указана</option>
              {categories
                .filter((category) => category.is_active || category.id === item?.category_id)
                .map((category) => (
                  <option key={category.id} value={category.id}>
                    {category.name}
                  </option>
                ))}
            </select>
          </Field>
          <Field label="Стиль">
            <select name="formality" className="field" defaultValue={item?.formality ?? ''}>
              <option value="">Не указан</option>
              {Object.entries(formalityLabels).map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>
          </Field>
          <Field label="Цвет" className="sm:col-span-2">
            <input name="color" maxLength={64} className="field" defaultValue={item?.color ?? ''} />
          </Field>
          <Field label="Заметка" className="sm:col-span-2">
            <textarea
              name="note"
              maxLength={1000}
              rows={3}
              className="field h-auto py-3"
              defaultValue={item?.note ?? ''}
              placeholder="С чем носить, размер, где куплено"
            />
          </Field>

          <div className="sm:col-span-2">
            {photoUrl && (
              <div className="mb-4 flex items-center gap-4">
                <img src={photoUrl} alt={item?.name} className="h-24 w-20 bg-mist object-cover" />
                <button
                  type="button"
                  disabled={busy}
                  onClick={() => item && removePhoto.mutate(item.id)}
                  className="text-xs underline underline-offset-4"
                >
                  Удалить фото
                </button>
              </div>
            )}
            <Field label={photoUrl ? 'Заменить фото' : 'Фото'}>
              <input name="file" type="file" accept={IMAGE_TYPES} className="field h-auto py-3" />
            </Field>
          </div>

          <div className="flex flex-wrap items-center gap-3 sm:col-span-2">
            <Button type="submit" disabled={busy}>
              {save.isPending ? 'Сохраняем...' : 'Сохранить'}
            </Button>
            <Button type="button" variant="outline" onClick={onClose}>
              Отмена
            </Button>
            {item &&
              (confirmDelete ? (
                <span className="ml-auto flex items-center gap-3 text-xs">
                  Удалить вещь?
                  <button
                    type="button"
                    disabled={busy}
                    onClick={() => remove.mutate(item.id)}
                    className="text-red-700 underline underline-offset-4"
                  >
                    Да
                  </button>
                  <button
                    type="button"
                    onClick={() => setConfirmDelete(false)}
                    className="underline underline-offset-4"
                  >
                    Нет
                  </button>
                </span>
              ) : (
                <button
                  type="button"
                  onClick={() => setConfirmDelete(true)}
                  className="ml-auto text-xs text-red-700 underline underline-offset-4"
                >
                  Удалить
                </button>
              ))}
          </div>
        </form>
        {error && (
          <p role="alert" className="mt-4 text-sm text-red-700">
            {error.message}
          </p>
        )}
      </div>
    </div>
  )
}
