import { Link, useSearchParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { orderApi } from '../../../entities/order'
import { date, money } from '../../../shared/lib/format'
import { Button } from '../../../shared/ui/Button'
import { ErrorState, Loading } from '../../../shared/ui/States'

export function OrdersPage() {
  const [params, setParams] = useSearchParams()
  const page = Math.max(1, Number(params.get('page')) || 1)
  const offset = (page - 1) * 20
  function goTo(nextPage: number) { const next = new URLSearchParams(params); if (nextPage <= 1) next.delete('page'); else next.set('page', String(nextPage)); setParams(next) }
  const { data, error, isPending, refetch } = useQuery({ queryKey: ['orders', offset], queryFn: () => orderApi.list(offset) })
  if (isPending) return <Loading />
  if (error) return <ErrorState error={error} retry={() => refetch()} />
  return <section><h2 className="font-display text-3xl tracking-tight">Мои заказы</h2>{data?.items.length ? <><div className="mt-6 divide-y divide-line border-y border-line">{data.items.map((order) => <Link key={order.id} to={`/account/orders/${order.id}`} className="flex flex-wrap items-center justify-between gap-4 py-5 hover:bg-mist"><div><p className="text-sm font-medium">Заказ № {order.id.slice(0, 8).toUpperCase()}</p><p className="mt-2 text-xs text-muted">{date(order.created_at)} · {order.items.length} позиций</p></div><div className="text-right"><strong className="text-sm">{money(order.total)}</strong><p className="mt-2 text-xs text-[#458052]">Оформлен</p></div></Link>)}</div><div className="mt-6 flex items-center gap-3">{offset > 0 && <Button variant="outline" onClick={() => goTo(page - 1)}>Назад</Button>}{offset + 20 < data.total && <Button variant="outline" onClick={() => goTo(page + 1)}>Далее</Button>}</div></> : <p className="mt-8 text-sm text-muted">Вы ещё не оформили заказ. <Link to="/catalog" className="text-ink underline">Посмотреть коллекцию</Link></p>}</section>
}
