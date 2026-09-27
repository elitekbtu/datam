import { Link, useSearchParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { Search } from 'lucide-react'
import { orderStatusLabels } from '../../../entities/order'
import { adminApi } from '../../../features/admin'
import type { OrderStatus } from '../../../features/admin'
import { date, money } from '../../../shared/lib/format'
import { ErrorState, Loading } from '../../../shared/ui/States'
import { PageHeading, Pagination } from './AdminParts'

const limit = 20

export function AdminOrdersPage() {
  const [params, setParams] = useSearchParams()
  const offset = Math.max(0, Number(params.get('offset')) || 0)
  const search = params.get('search') || ''
  const status = params.get('status') || ''
  const query = new URLSearchParams({ limit: String(limit), offset: String(offset) })
  if (search) query.set('search', search)
  if (status) query.set('status', status)
  const orders = useQuery({ queryKey: ['admin', 'orders', query.toString()], queryFn: () => adminApi.orders(query) })

  function change(name: string, value: string) {
    const next = new URLSearchParams(params)
    if (value) next.set(name, value)
    else next.delete(name)
    next.delete('offset')
    setParams(next)
  }

  return <section>
    <PageHeading title="Заказы" />
    <div className="mb-6 flex flex-wrap gap-3">
      <label className="relative min-w-[220px] flex-1">
        <span className="sr-only">Поиск заказов</span>
        <Search size={17} className="absolute left-4 top-1/2 -translate-y-1/2 text-muted" />
        <input className="field pl-11" placeholder="Номер, имя или телефон" value={search} onChange={(event) => change('search', event.target.value)} />
      </label>
      <label>
        <span className="sr-only">Статус заказа</span>
        <select className="field min-w-[170px]" value={status} onChange={(event) => change('status', event.target.value)}>
          <option value="">Все статусы</option>
          {(Object.keys(orderStatusLabels) as OrderStatus[]).map((value) => <option key={value} value={value}>{orderStatusLabels[value]}</option>)}
        </select>
      </label>
    </div>
    {orders.isPending ? <Loading /> : orders.error ? <ErrorState error={orders.error} retry={() => orders.refetch()} /> : <>
      <div className="divide-y divide-line border-y border-line">
        {orders.data?.items.map((order) => <Link key={order.id} to={`/admin/orders/${order.id}`} className="flex flex-wrap items-center gap-4 py-5 transition-colors hover:bg-mist sm:px-3">
          <div className="min-w-[190px] flex-1">
            <p className="text-sm font-medium">Заказ № {order.id.slice(0, 8).toUpperCase()}</p>
            <p className="mt-1 text-xs text-muted">{date(order.created_at)} · {order.items.length} позиций</p>
          </div>
          <div className="min-w-[160px] flex-1 text-xs">
            <p>{order.full_name}</p>
            <p className="mt-1 text-muted">{order.phone}</p>
          </div>
          <span className="min-w-[100px] text-xs text-muted">{orderStatusLabels[order.status]}</span>
          <strong className="min-w-[100px] text-right text-sm font-medium">{money(order.total, order.currency)}</strong>
        </Link>)}
        {!orders.data?.items.length && <p className="py-12 text-center text-sm text-muted">Заказы не найдены.</p>}
      </div>
      <Pagination total={orders.data?.total ?? 0} offset={offset} limit={limit} onChange={(value) => { const next = new URLSearchParams(params); next.set('offset', String(value)); setParams(next) }} />
    </>}
  </section>
}
