import { Link, NavLink, Navigate, Outlet } from 'react-router-dom'
import { LayoutDashboard, Package, Tags, Users } from 'lucide-react'
import { useQuery } from '@tanstack/react-query'
import { userApi } from '../../../entities/user'
import { ErrorState, Loading } from '../../../shared/ui/States'

const links = [
  { to: '/admin', label: 'Обзор', icon: LayoutDashboard, end: true },
  { to: '/admin/products', label: 'Товары', icon: Package, end: false },
  { to: '/admin/categories', label: 'Категории', icon: Tags, end: false },
  { to: '/admin/users', label: 'Пользователи', icon: Users, end: false },
]

export function AdminLayout() {
  const session = useQuery({ queryKey: ['user'], queryFn: userApi.session, retry: false })
  if (session.isPending) return <Loading />
  if (session.error) return <ErrorState error={session.error} retry={() => session.refetch()} />
  if (!session.data) return <Navigate to={`/login?returnTo=${encodeURIComponent(window.location.pathname)}`} replace />
  if (session.data.role !== 'admin') return <div className="page-container py-24 text-center"><h1 className="section-title">Доступ закрыт</h1><p className="mt-4 text-sm text-muted">Эта страница доступна только администратору.</p><Link to="/account" className="mt-6 inline-block text-sm underline underline-offset-4">В личный кабинет</Link></div>
  return <div className="page-container pb-20 pt-8"><div className="mb-7 text-xs text-muted"><Link to="/" className="link-hover">Главная</Link><span className="mx-2">/</span>Управление магазином</div><div className="mb-9 flex flex-wrap items-end justify-between gap-4"><div><h1 className="display-title">Управление</h1><p className="mt-3 text-sm text-muted">Каталог и доступы магазина DATAM.</p></div><Link to="/" className="text-xs underline underline-offset-4">Открыть магазин ↗</Link></div><div className="grid gap-8 lg:grid-cols-[220px_minmax(0,1fr)] lg:gap-10"><nav aria-label="Администрирование" className="flex gap-2 overflow-x-auto border-b border-line pb-4 lg:flex-col lg:gap-1 lg:border-b-0 lg:border-r lg:pr-5">{links.map(({ to, label, icon: Icon, end }) => <NavLink key={to} to={to} end={end} className={({ isActive }) => `flex shrink-0 items-center gap-3 px-4 py-3 text-sm ${isActive ? 'bg-mist font-medium' : 'hover:bg-mist'}`}><Icon size={18} />{label}</NavLink>)}</nav><div className="min-w-0"><Outlet /></div></div></div>
}
