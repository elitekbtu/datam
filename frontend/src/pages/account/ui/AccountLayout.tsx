import { Link, NavLink, Navigate, Outlet, useNavigate } from 'react-router-dom'
import { Heart, LogOut, Package, UserRound } from 'lucide-react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { userApi } from '../../../entities/user'
import { authApi } from '../../../features/auth'
import { ErrorState, Loading } from '../../../shared/ui/States'

export function AccountLayout() {
  const client = useQueryClient()
  const navigate = useNavigate()
  const session = useQuery({ queryKey: ['user'], queryFn: userApi.session, retry: false })
  const { data: user, error, isPending, refetch } = useQuery({ queryKey: ['account'], queryFn: userApi.me, enabled: Boolean(session.data), retry: false })
  const logout = useMutation({ mutationFn: authApi.logout, onSuccess: () => { client.clear(); navigate('/', { replace: true }) } })
  if (session.isPending) return <Loading />
  if (session.error) return <ErrorState error={session.error} retry={() => session.refetch()} />
  if (!session.data) return <Navigate to={`/login?returnTo=${encodeURIComponent(window.location.pathname)}`} replace />
  if (isPending) return <Loading />
  if (error) return <ErrorState error={error} retry={() => refetch()} />
  if (!user) return <Loading />
  return <div className="page-container pt-9"><div className="mb-4 text-xs text-muted"><Link to="/">Главная</Link> / Личный кабинет</div><h1 className="display-title">Личный кабинет</h1><p className="mt-4 text-sm text-muted">Ваши данные, заказы и любимые вещи.</p><div className="mt-10 grid gap-10 lg:grid-cols-[215px_minmax(0,1fr)]"><aside className="flex gap-2 overflow-x-auto border-b border-line pb-4 lg:flex-col lg:gap-1 lg:border-b-0 lg:border-r lg:pr-5"><NavLink end to="/account" className={({ isActive }) => `flex shrink-0 items-center gap-3 px-4 py-3 text-sm ${isActive ? 'bg-mist font-medium' : 'hover:bg-mist'}`}><UserRound size={18} /> Профиль</NavLink><NavLink to="/account/orders" className={({ isActive }) => `flex shrink-0 items-center gap-3 px-4 py-3 text-sm ${isActive ? 'bg-mist font-medium' : 'hover:bg-mist'}`}><Package size={18} /> Мои заказы</NavLink><Link to="/favorites" className="flex shrink-0 items-center gap-3 px-4 py-3 text-sm hover:bg-mist"><Heart size={18} /> Избранное</Link><button type="button" onClick={() => logout.mutate()} disabled={logout.isPending} className="flex shrink-0 items-center gap-3 px-4 py-3 text-left text-sm hover:bg-mist"><LogOut size={18} /> Выйти</button></aside><div className="min-w-0"><Outlet context={user} /></div></div>{logout.isError && <p role="alert" className="mt-3 text-sm text-red-700">{logout.error.message}</p>}</div>
}
