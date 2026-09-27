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
import { ErrorState, Loading } from '../../../shared/ui/States'
import { ConfirmButton, FormError, PageHeading } from './AdminParts'

const nextStatuses: Record<OrderStatus, OrderStatus[]> = {
  placed: ['processing', 'cancelled'],
  processing: ['shipped', 'cancelled'],
  shipped: ['delivered'],
  delivered: [],
  cancelled: [],
}

export function AdminOrderPage() {
  const { id = '' } = useParams()
  const client = useQueryClient()
  const [editingDelivery, setEditingDelivery] = useState(false)
  const order = useQuery({ queryKey: ['admin', 'order', id], queryFn: () => adminApi.order(id), enabled: Boolean(id) })
  function onChanged(updated: AdminOrder) {
    client.setQueryData(['admin', 'order', id], updated)
    if (updated.status !== 'placed' && updated.status !== 'processing') setEditingDelivery(false)
    void client.invalidateQueries({ queryKey: ['admin'] })
    void client.invalidateQueries({ queryKey: ['orders'] })
    void client.invalidateQueries({ queryKey: ['order', id] })
  }
  const save = useMutation({ mutationFn: (status: OrderStatus) => adminApi.updateOrderStatus(id, status), onSuccess: onChanged })
  const delivery = useMutation({ mutationFn: (body: OrderDeliveryInput) => adminApi.updateOrderDelivery(id, body), onSuccess: (updated) => { onChanged(updated); setEditingDelivery(false) } })

  function submitDelivery(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const data = new FormData(event.currentTarget)
    delivery.mutate({
      full_name: String(data.get('full_name')).trim(),
      phone: String(data.get('phone')).trim(),
      city: String(data.get('city')).trim(),
      address: String(data.get('address')).trim(),
      postal_code: String(data.get('postal_code')).trim() || null,
      note: String(data.get('note')).trim() || null,
    })
  }

  if (order.isPending) return <Loading />
  if (order.error || !order.data) return <ErrorState error={order.error} retry={() => order.refetch()} />
  const item = order.data
  const available = nextStatuses[item.status]

  return <section>
    <Link to="/admin/orders" className="mb-5 inline-flex items-center gap-2 text-xs text-muted hover:text-ink"><ArrowLeft size={15} />К заказам</Link>
    <PageHeading title={`Заказ № ${item.id.slice(0, 8).toUpperCase()}`} />
    <p className="break-all text-xs text-muted">{item.id}</p>
    <p className="mt-2 text-sm text-muted">{date(item.created_at)} · {item.items.length} позиций</p>

    <div className="mt-8 border-y border-line py-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div><p className="text-xs text-muted">Статус</p><p className="mt-1 text-lg font-medium">{orderStatusLabels[item.status]}</p></div>
        {available.length > 0 && <div className="flex flex-wrap items-center gap-3">
          {available.filter((status) => status !== 'cancelled').map((status) => <Button key={status} type="button" disabled={save.isPending} onClick={() => save.mutate(status)}>{orderStatusLabels[status]}</Button>)}
          {available.includes('cancelled') && <ConfirmButton label="Отменить заказ" disabled={save.isPending} onConfirm={() => save.mutate('cancelled')} />}
        </div>}
      </div>
      <FormError error={save.error} />
    </div>

    <div className="mt-8 grid gap-10 xl:grid-cols-[minmax(0,1fr)_300px]">
      <div>
        <h3 className="font-display text-2xl">Состав заказа</h3>
        <div className="mt-4 divide-y divide-line border-y border-line">
          {item.items.map((product) => <div key={product.id} className="flex gap-4 py-5">
            <div className="h-24 w-20 shrink-0 bg-mist">{product.image_url && <img src={product.image_url} alt="" className="h-full w-full object-cover" />}</div>
            <div className="min-w-0 flex-1">
              <p className="text-sm font-medium">{product.name}</p>
              <p className="mt-1 text-xs text-muted">{product.sku}{Object.keys(product.options).length ? ` · ${Object.values(product.options).join(' · ')}` : ''}</p>
              <p className="mt-2 text-xs text-muted">{product.quantity} шт. × {money(product.unit_price, item.currency)}</p>
            </div>
            <strong className="text-right text-sm font-medium">{money(product.total, item.currency)}</strong>
          </div>)}
        </div>
      </div>
      <aside className="h-fit bg-mist p-6">
        <div className="flex items-center justify-between gap-3"><h3 className="font-display text-2xl">Доставка</h3>{!editingDelivery && ['placed', 'processing'].includes(item.status) && <button type="button" className="text-xs underline underline-offset-4" onClick={() => setEditingDelivery(true)}>Изменить</button>}</div>
        {editingDelivery ? <form onSubmit={submitDelivery} className="mt-5 space-y-4">
          <label className="block"><span className="field-label">Получатель *</span><input name="full_name" className="field" required minLength={2} maxLength={128} defaultValue={item.full_name} /></label>
          <label className="block"><span className="field-label">Телефон *</span><input name="phone" className="field" required minLength={7} maxLength={32} defaultValue={item.phone} /></label>
          <label className="block"><span className="field-label">Город *</span><input name="city" className="field" required minLength={2} maxLength={128} defaultValue={item.city} /></label>
          <label className="block"><span className="field-label">Адрес *</span><input name="address" className="field" required minLength={5} maxLength={255} defaultValue={item.address} /></label>
          <label className="block"><span className="field-label">Индекс</span><input name="postal_code" className="field" maxLength={16} defaultValue={item.postal_code || ''} /></label>
          <label className="block"><span className="field-label">Комментарий</span><textarea name="note" className="field h-24 py-3" maxLength={1000} defaultValue={item.note || ''} /></label>
          <div className="flex flex-wrap gap-2"><Button type="submit" disabled={delivery.isPending}>Сохранить</Button><Button type="button" variant="outline" onClick={() => setEditingDelivery(false)}>Отмена</Button></div>
          <FormError error={delivery.error} />
        </form> : <>
          <p className="mt-5 text-xs text-muted">Получатель</p>
          <p className="mt-1 text-sm">{item.full_name}<br /><a href={`tel:${item.phone}`} className="underline underline-offset-4">{item.phone}</a></p>
          <p className="mt-5 text-xs text-muted">Адрес</p>
          <p className="mt-1 text-sm">{item.city}, {item.address}{item.postal_code ? `, ${item.postal_code}` : ''}</p>
          {item.note && <><p className="mt-5 text-xs text-muted">Комментарий</p><p className="mt-1 whitespace-pre-wrap text-sm">{item.note}</p></>}
        </>}
        <div className="mt-6 flex justify-between border-t border-line pt-5 text-sm font-medium"><span>Итого</span><span>{money(item.total, item.currency)}</span></div>
      </aside>
    </div>
  </section>
}
