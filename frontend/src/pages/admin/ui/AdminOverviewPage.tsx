import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { ArrowUpRight, Package, ShoppingBag, Tags, Users } from 'lucide-react'
import { adminApi } from '../../../features/admin'
import { ErrorState, Loading } from '../../../shared/ui/States'

const countParams = new URLSearchParams({ limit: '1' })

export function AdminOverviewPage() {
  const products = useQuery({ queryKey: ['admin', 'overview', 'products'], queryFn: () => adminApi.products(countParams) })
  const categories = useQuery({ queryKey: ['admin', 'overview', 'categories'], queryFn: () => adminApi.categories(countParams) })
  const orders = useQuery({ queryKey: ['admin', 'overview', 'orders'], queryFn: () => adminApi.orders(countParams) })
  const users = useQuery({ queryKey: ['admin', 'overview', 'users'], queryFn: () => adminApi.users(countParams) })
  if (products.isPending || categories.isPending || orders.isPending || users.isPending) return <Loading />
  if (products.error || categories.error || orders.error || users.error) return <ErrorState error={products.error || categories.error || orders.error || users.error} retry={() => { void products.refetch(); void categories.refetch(); void orders.refetch(); void users.refetch() }} />
  const sections = [
    { to: '/admin/products', title: 'Товары', count: products.data?.total ?? 0, icon: Package, body: 'Редактируйте карточки, варианты и фотографии.' },
    { to: '/admin/orders', title: 'Заказы', count: orders.data?.total ?? 0, icon: ShoppingBag, body: 'Просматривайте заказы и меняйте их статус.' },
    { to: '/admin/categories', title: 'Категории', count: categories.data?.total ?? 0, icon: Tags, body: 'Организуйте разделы каталога.' },
    { to: '/admin/users', title: 'Пользователи', count: users.data?.total ?? 0, icon: Users, body: 'Управляйте аккаунтами и ролями.' },
  ]
  return <section><h2 className="font-display text-3xl tracking-tight">Обзор магазина</h2><p className="mt-3 text-sm text-muted">Выберите раздел, чтобы перейти к управлению.</p><div className="mt-8 divide-y divide-line border-y border-line">{sections.map(({ to, title, count, icon: Icon, body }) => <Link key={to} to={to} className="group flex items-center gap-4 py-6 transition-colors hover:bg-mist sm:gap-6 sm:px-4"><Icon size={22} strokeWidth={1.5} className="shrink-0" /><div className="min-w-0 flex-1"><h3 className="text-base font-medium">{title}</h3><p className="mt-1 text-xs text-muted">{body}</p></div><span className="font-display text-3xl">{count}</span><ArrowUpRight size={17} className="text-muted transition group-hover:text-ink" /></Link>)}</div></section>
}
