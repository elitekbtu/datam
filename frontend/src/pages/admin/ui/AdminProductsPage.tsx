import { Link, useSearchParams } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Plus, Search } from 'lucide-react'
import { adminApi } from '../../../features/admin'
import { date, money } from '../../../shared/lib/format'
import { ErrorState, Loading } from '../../../shared/ui/States'
import { ConfirmButton, FormError, PageHeading, Pagination } from './AdminParts'

const limit = 20

export function AdminProductsPage() {
  const [params, setParams] = useSearchParams()
  const client = useQueryClient()
  const offset = Math.max(0, Number(params.get('offset')) || 0)
  const search = params.get('search') || ''
  const status = params.get('status') || ''
  const query = new URLSearchParams({ limit: String(limit), offset: String(offset) })
  if (search) query.set('search', search)
  if (status) query.set('is_active', status)
  const products = useQuery({ queryKey: ['admin', 'products', query.toString()], queryFn: () => adminApi.products(query) })
  const remove = useMutation({ mutationFn: adminApi.deleteProduct, onSuccess: () => { void client.invalidateQueries({ queryKey: ['admin'] }); void client.invalidateQueries({ queryKey: ['products'] }) } })
  function change(name: string, value: string) { const next = new URLSearchParams(params); if (value) next.set(name, value); else next.delete(name); next.delete('offset'); setParams(next) }
  return <section><PageHeading title="Товары" action={<Link to="/admin/products/new" className="inline-flex min-h-11 items-center gap-2 bg-ink px-5 text-sm text-white"><Plus size={17} />Добавить товар</Link>} /><div className="mb-6 flex flex-wrap gap-3"><label className="relative min-w-[220px] flex-1"><span className="sr-only">Поиск товаров</span><Search size={17} className="absolute left-4 top-1/2 -translate-y-1/2 text-muted" /><input className="field pl-11" placeholder="Название, описание или артикул" value={search} onChange={(event) => change('search', event.target.value)} /></label><label><span className="sr-only">Статус товара</span><select className="field min-w-[150px]" value={status} onChange={(event) => change('status', event.target.value)}><option value="">Все статусы</option><option value="true">Активные</option><option value="false">Скрытые</option></select></label></div>{products.isPending ? <Loading /> : products.error ? <ErrorState error={products.error} retry={() => products.refetch()} /> : <><div className="overflow-x-auto border-y border-line"><table className="w-full min-w-[690px] text-left text-xs"><thead className="text-muted"><tr className="border-b border-line"><th className="py-3 pr-3 font-normal">Товар</th><th className="px-3 py-3 font-normal">Цена</th><th className="px-3 py-3 font-normal">Остаток</th><th className="px-3 py-3 font-normal">Статус</th><th className="px-3 py-3 font-normal">Создан</th><th className="py-3 pl-3 text-right font-normal">Действия</th></tr></thead><tbody className="divide-y divide-line">{products.data?.items.map((product) => <tr key={product.id}><td className="py-3 pr-3"><Link to={`/admin/products/${product.id}`} className="flex items-center gap-3 hover:underline"><div className="h-12 w-10 shrink-0 bg-mist">{product.images[0] && <img src={product.images[0].url} alt="" className="h-full w-full object-cover" />}</div><span><strong className="block font-medium">{product.name}</strong><span className="mt-1 block text-muted">{product.sku}</span></span></Link></td><td className="px-3 py-3 whitespace-nowrap">{money(product.price)}</td><td className="px-3 py-3">{product.total_stock}</td><td className="px-3 py-3">{product.is_active ? 'Активен' : 'Скрыт'}</td><td className="px-3 py-3 whitespace-nowrap text-muted">{date(product.created_at)}</td><td className="py-3 pl-3 text-right"><ConfirmButton label="Удалить" disabled={remove.isPending} onConfirm={() => remove.mutate(product.id)} /></td></tr>)}</tbody></table>{!products.data?.items.length && <p className="py-12 text-center text-sm text-muted">Товары не найдены.</p>}</div><Pagination total={products.data?.total ?? 0} offset={offset} limit={limit} onChange={(value) => { const next = new URLSearchParams(params); next.set('offset', String(value)); setParams(next) }} /></>}<FormError error={remove.error} /></section>
}
