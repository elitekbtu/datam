import { Link, useSearchParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { orderStatusLabels } from '../../../entities/order'
import { adminApi } from '../../../features/admin'
import type { AdminOrder, OrderStatus } from '../../../features/admin'
import { date, money } from '../../../shared/lib/format'
import { ErrorState, Loading } from '../../../shared/ui/States'
import { PageHeading, Pagination, SearchField } from './AdminParts'

const limit = 20

function OrderRow({ order }: { order: AdminOrder }) {
  return (
    <Link
      to={`/admin/orders/${order.id}`}
      className="flex flex-wrap items-center gap-4 py-5 transition-colors hover:bg-mist sm:px-3"
    >
      <div className="min-w-[190px] flex-1">
        <p className="text-sm font-medium">Заказ № {order.id.slice(0, 8).toUpperCase()}</p>
        <p className="mt-1 text-xs text-muted">
          {date(order.created_at)} · {order.items.length} позиций
        </p>
      </div>
      <div className="min-w-[160px] flex-1 text-xs">
        <p>{order.full_name}</p>
        <p className="mt-1 text-muted">{order.phone}</p>
      </div>
      <span className="min-w-[100px] text-xs text-muted">{orderStatusLabels[order.status]}</span>
      <strong className="min-w-[100px] text-right text-sm font-medium">{money(order.total, order.currency)}</strong>
    </Link>
  )
}

export function AdminOrdersPage() {
  const [params, setParams] = useSearchParams()
  const offset = Math.max(0, Number(params.get('offset')) || 0)
  const search = params.get('search') || ''
  const status = params.get('status') || ''

  const query = new URLSearchParams({ limit: String(limit), offset: String(offset) })
  if (search) query.set('search', search)
  if (status) query.set('status', status)
  const orders = useQuery({
    queryKey: ['admin', 'orders', query.toString()],
    queryFn: () => adminApi.orders(query),
  })

  // A new filter starts from the first page.
  function change(name: string, value: string) {
    const next = new URLSearchParams(params)
    if (value) next.set(name, value)
    else next.delete(name)
    next.delete('offset')
    setParams(next)
  }

  function goTo(value: number) {
    const next = new URLSearchParams(params)
    next.set('offset', String(value))
    setParams(next)
  }

  return (
    <section>
      <PageHeading title="Заказы" />
      <div className="mb-6 flex flex-wrap gap-3">
        <SearchField
          label="Поиск заказов"
          placeholder="Номер, имя или телефон"
          value={search}
          onChange={(value) => change('search', value)}
          className="relative min-w-[220px] flex-1"
        />
        <label>
          <span className="sr-only">Статус заказа</span>
          <select
            className="field min-w-[170px]"
            value={status}
            onChange={(event) => change('status', event.target.value)}
          >
            <option value="">Все статусы</option>
            {(Object.keys(orderStatusLabels) as OrderStatus[]).map((value) => (
              <option key={value} value={value}>
                {orderStatusLabels[value]}
              </option>
            ))}
          </select>
        </label>
      </div>

      {orders.isPending ? (
        <Loading />
      ) : orders.error ? (
        <ErrorState error={orders.error} retry={() => orders.refetch()} />
      ) : (
        <>
          <div className="divide-y divide-line border-y border-line">
            {orders.data?.items.map((order) => <OrderRow key={order.id} order={order} />)}
            {!orders.data?.items.length && (
              <p className="py-12 text-center text-sm text-muted">Заказы не найдены.</p>
            )}
          </div>
          <Pagination total={orders.data?.total ?? 0} offset={offset} limit={limit} onChange={goTo} />
        </>
      )}
    </section>
  )
}
