import { useState } from 'react'
import type { FormEvent } from 'react'
import { Link, NavLink, useNavigate } from 'react-router-dom'
import { Heart, Menu, Search, ShoppingBag, UserRound, X } from 'lucide-react'
import { useQuery } from '@tanstack/react-query'
import { cartApi } from '../../../entities/cart'
import { userApi } from '../../../entities/user'

const navigation = [
  { label: 'Женщинам', to: '/catalog?audience=women' },
  { label: 'Мужчинам', to: '/catalog?audience=men' },
  { label: 'Новинки', to: '/catalog?sort=newest' },
  { label: 'Одежда', to: '/catalog?category=clothing' },
  { label: 'Обувь', to: '/catalog?category=shoes' },
  { label: 'Аксессуары', to: '/catalog?category=accessories' },
]

export function SiteHeader() {
  const navigate = useNavigate()
  const [search, setSearch] = useState('')
  const [mobileOpen, setMobileOpen] = useState(false)
  const { data: user, isPending: sessionPending } = useQuery({ queryKey: ['user'], queryFn: userApi.session, retry: false })
  const { data: cart } = useQuery({ queryKey: ['cart'], queryFn: cartApi.read, enabled: !sessionPending })
  function submit(event: FormEvent) { event.preventDefault(); if (search.trim()) { navigate(`/catalog?search=${encodeURIComponent(search.trim())}`); setMobileOpen(false) } }
  return <header className="sticky top-0 z-40 border-b border-line bg-white/95 backdrop-blur-sm">
    <div className="page-container flex h-[62px] items-center gap-5 lg:h-[68px]">
      <button type="button" className="lg:hidden" aria-label={mobileOpen ? 'Закрыть меню' : 'Открыть меню'} onClick={() => setMobileOpen(!mobileOpen)}>{mobileOpen ? <X size={22} /> : <Menu size={22} />}</button>
      <Link to="/" className="shrink-0 text-[23px] font-medium tracking-[.28em] sm:text-[26px]" onClick={() => setMobileOpen(false)}>DATAM</Link>
      <nav aria-label="Основная навигация" className="ml-4 hidden items-center gap-5 text-[12px] xl:gap-7 lg:flex">{navigation.map((item) => <NavLink key={item.label} to={item.to} className="whitespace-nowrap transition-colors hover:text-muted">{item.label}</NavLink>)}</nav>
      <form onSubmit={submit} role="search" className="ml-auto hidden w-[220px] items-center rounded-full bg-mist px-3 py-2 lg:flex xl:w-[250px]"><Search size={16} className="text-muted" /><input value={search} onChange={(event) => setSearch(event.target.value)} aria-label="Поиск товаров" placeholder="Поиск товаров..." className="w-full bg-transparent pl-2 text-xs outline-none placeholder:text-[#98989d]" /></form>
      <div className="ml-auto flex items-center gap-3 sm:gap-5 lg:ml-3"><Link aria-label={user ? 'Личный кабинет' : 'Войти'} to={user ? '/account' : '/login'} className="link-hover"><UserRound size={21} strokeWidth={1.6} /></Link><Link aria-label="Избранное" to="/favorites" className="link-hover"><Heart size={22} strokeWidth={1.6} /></Link><Link aria-label={`Корзина, товаров: ${cart?.count ?? 0}`} to="/cart" className="relative link-hover"><ShoppingBag size={21} strokeWidth={1.6} />{Boolean(cart?.count) && <span className="absolute -right-2 -top-2 flex h-4 min-w-4 items-center justify-center rounded-full bg-ink px-1 text-[9px] leading-none text-white">{cart?.count}</span>}</Link></div>
    </div>
    {mobileOpen && <div className="border-t border-line bg-white p-5 lg:hidden"><form onSubmit={submit} role="search" className="mb-5 flex items-center bg-mist px-4 py-3"><Search size={17} /><input className="w-full bg-transparent pl-3 text-sm outline-none" placeholder="Поиск товаров" value={search} onChange={(event) => setSearch(event.target.value)} /></form><nav className="grid gap-1" aria-label="Мобильная навигация">{navigation.map((item) => <Link key={item.label} onClick={() => setMobileOpen(false)} to={item.to} className="border-b border-line py-3 text-sm">{item.label}</Link>)}</nav></div>}
  </header>
}
