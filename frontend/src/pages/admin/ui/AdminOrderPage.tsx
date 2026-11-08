import { useState } from 'react'
import type { FormEvent } from 'react'
import { Link, useParams } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { ArrowLeft } from 'lucide-react'
import { orderStatusLabels } from '../../../entities/order'
import { adminApi } from '../../../features/admin'
import type { AdminOrder, OrderDeliveryInput, OrderStatus } from '../../../features/admin'
import { date, money } from '../../../shared/lib/format'
import { Button } from '../../../shared/ui/Button'
import { Field } from '../../../shared/ui/Field'
import { ErrorState, Loading } from '../../../shared/ui/States'
import { ConfirmButton, FormError, PageHeading } from './AdminParts'

// Allowed transitions; the backend enforces the same rules.
const nextStatuses: Record<OrderStatus, OrderStatus[]> = {
  placed: ['processing', 'cancelled'],
  processing: ['shipped', 'cancelled'],
  shipped: ['delivered'],
  delivered: [],
  cancelled: [],
}

// Delivery details can change only until the order ships.
const canEditDelivery = (status: OrderStatus) => status === 'placed' || status === 'processing'

function deliveryValues(form: HTMLFormElement): OrderDeliveryInput {
  const data = new FormData(form)
  const text = (name: string) => String(data.get(name)).trim()
  return {
    full_name: text('full_name'),
    phone: text('phone'),
    city: text('city'),
    address: text('address'),
    postal_code: text('postal_code') || null,
    note: text('note') || null,
  }
}

function OrderItems({ order }: { order: AdminOrder }) {
  return (
    <div>
      <h3 className="font-display text-2xl">Состав заказа</h3>
      <div className="mt-4 divide-y divide-line border-y border-line">
        {order.items.map((product) => {
          const options = Object.values(product.options)
          return (
            <div key={product.id} className="flex gap-4 py-5">
              <div className="h-24 w-20 shrink-0 bg-mist">
                {product.image_url && <img src={product.image_url} alt="" className="h-full w-full object-cover" />}
              </div>
              <div className="min-w-0 flex-1">
                <p className="text-sm font-medium">{product.name}</p>
                <p className="mt-1 text-xs text-muted">
                  {product.sku}
                  {options.length ? ` · ${options.join(' · ')}` : ''}
                </p>
                <p className="mt-2 text-xs text-muted">
                  {product.quantity} шт. × {money(product.unit_price, order.currency)}
                </p>
              </div>
              <strong className="text-right text-sm font-medium">{money(product.total, order.currency)}</strong>
            </div>
          )
        })}
      </div>
    </div>
  )
}

type DeliveryFormProps = {
  order: AdminOrder
  saving: boolean
  error: Error | null
  onSubmit: (event: FormEvent<HTMLFormElement>) => void
  onCancel: () => void
}

function DeliveryForm({ order, saving, error, onSubmit, onCancel }: DeliveryFormProps) {
  return (
    <form onSubmit={onSubmit} className="mt-5 space-y-4">
      <Field label="Получатель *" className="block">
        <input name="full_name" className="field" required minLength={2} maxLength={128} defaultValue={order.full_name} />
      </Field>
      <Field label="Телефон *" className="block">
        <input name="phone" className="field" required minLength={7} maxLength={32} defaultValue={order.phone} />
      </Field>
      <Field label="Город *" className="block">
        <input name="city" className="field" required minLength={2} maxLength={128} defaultValue={order.city} />
      </Field>
      <Field label="Адрес *" className="block">
        <input name="address" className="field" required minLength={5} maxLength={255} defaultValue={order.address} />
      </Field>
      <Field label="Индекс" className="block">
        <input name="postal_code" className="field" maxLength={16} defaultValue={order.postal_code || ''} />
      </Field>
      <Field label="Комментарий" className="block">
        <textarea name="note" className="field h-24 py-3" maxLength={1000} defaultValue={order.note || ''} />
      </Field>
      <div className="flex flex-wrap gap-2">
        <Button type="submit" disabled={saving}>
          Сохранить
        </Button>
        <Button type="button" variant="outline" onClick={onCancel}>
          Отмена
        </Button>
      </div>
      <FormError error={error} />
    </form>
  )
}

function DeliveryDetails({ order }: { order: AdminOrder }) {
  return (
    <>
      <p className="mt-5 text-xs text-muted">Получатель</p>
      <p className="mt-1 text-sm">
        {order.full_name}
        <br />
        <a href={`tel:${order.phone}`} className="underline underline-offset-4">
          {order.phone}
        </a>
      </p>
      <p className="mt-5 text-xs text-muted">Адрес</p>
      <p className="mt-1 text-sm">
        {order.city}, {order.address}
        {order.postal_code ? `, ${order.postal_code}` : ''}
      </p>
      {order.note && (
        <>
          <p className="mt-5 text-xs text-muted">Комментарий</p>
          <p className="mt-1 whitespace-pre-wrap text-sm">{order.note}</p>
        </>
      )}
    </>
  )
}

export function AdminOrderPage() {
  const { id = '' } = useParams()
  const client = useQueryClient()
  const [editingDelivery, setEditingDelivery] = useState(false)
  const order = useQuery({
    queryKey: ['admin', 'order', id],
    queryFn: () => adminApi.order(id),
    enabled: Boolean(id),
  })

  function onChanged(updated: AdminOrder) {
    client.setQueryData(['admin', 'order', id], updated)
    if (!canEditDelivery(updated.status)) setEditingDelivery(false)
    void client.invalidateQueries({ queryKey: ['admin'] })
    void client.invalidateQueries({ queryKey: ['orders'] })
    void client.invalidateQueries({ queryKey: ['order', id] })
  }

  const save = useMutation({
    mutationFn: (status: OrderStatus) => adminApi.updateOrderStatus(id, status),
    onSuccess: onChanged,
  })
  const delivery = useMutation({
    mutationFn: (body: OrderDeliveryInput) => adminApi.updateOrderDelivery(id, body),
    onSuccess: (updated) => {
      onChanged(updated)
      setEditingDelivery(false)
    },
  })

  function submitDelivery(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    delivery.mutate(deliveryValues(event.currentTarget))
  }

  if (order.isPending) return <Loading />
  if (order.error || !order.data) return <ErrorState error={order.error} retry={() => order.refetch()} />

  const item = order.data
  const available = nextStatuses[item.status]
  const forward = available.filter((status) => status !== 'cancelled')

  return (
    <section>
      <Link to="/admin/orders" className="mb-5 inline-flex items-center gap-2 text-xs text-muted hover:text-ink">
        <ArrowLeft size={15} />
        К заказам
      </Link>
      <PageHeading title={`Заказ № ${item.id.slice(0, 8).toUpperCase()}`} />
      <p className="break-all text-xs text-muted">{item.id}</p>
      <p className="mt-2 text-sm text-muted">
        {date(item.created_at)} · {item.items.length} позиций
      </p>

      <div className="mt-8 border-y border-line py-6">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <p className="text-xs text-muted">Статус</p>
            <p className="mt-1 text-lg font-medium">{orderStatusLabels[item.status]}</p>
          </div>
          {available.length > 0 && (
            <div className="flex flex-wrap items-center gap-3">
              {forward.map((status) => (
                <Button key={status} type="button" disabled={save.isPending} onClick={() => save.mutate(status)}>
                  {orderStatusLabels[status]}
                </Button>
              ))}
              {available.includes('cancelled') && (
                <ConfirmButton
                  label="Отменить заказ"
                  disabled={save.isPending}
                  onConfirm={() => save.mutate('cancelled')}
                />
              )}
            </div>
          )}
        </div>
        <FormError error={save.error} />
      </div>

      <div className="mt-8 grid gap-10 xl:grid-cols-[minmax(0,1fr)_300px]">
        <OrderItems order={item} />
        <aside className="h-fit bg-mist p-6">
          <div className="flex items-center justify-between gap-3">
            <h3 className="font-display text-2xl">Доставка</h3>
            {!editingDelivery && canEditDelivery(item.status) && (
              <button
                type="button"
                className="text-xs underline underline-offset-4"
                onClick={() => setEditingDelivery(true)}
              >
                Изменить
              </button>
            )}
          </div>
          {editingDelivery ? (
            <DeliveryForm
              order={item}
              saving={delivery.isPending}
              error={delivery.error}
              onSubmit={submitDelivery}
              onCancel={() => setEditingDelivery(false)}
            />
          ) : (
            <DeliveryDetails order={item} />
          )}
          <div className="mt-6 flex justify-between border-t border-line pt-5 text-sm font-medium">
            <span>Итого</span>
            <span>{money(item.total, item.currency)}</span>
          </div>
        </aside>
      </div>
    </section>
  )
}
