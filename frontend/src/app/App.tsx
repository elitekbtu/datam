import { Suspense, lazy, useEffect } from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter, Link, Outlet, Route, Routes, useLocation } from 'react-router-dom'
import { SiteHeader } from '../widgets/site-header'
import { SiteFooter } from '../widgets/site-footer'
import { Loading } from '../shared/ui/States'

const HomePage = lazy(() => import('../pages/home').then((module) => ({ default: module.HomePage })))
const CatalogPage = lazy(() => import('../pages/catalog').then((module) => ({ default: module.CatalogPage })))
const ProductPage = lazy(() => import('../pages/product').then((module) => ({ default: module.ProductPage })))
const FavoritesPage = lazy(() => import('../pages/favorites').then((module) => ({ default: module.FavoritesPage })))
const CartPage = lazy(() => import('../pages/cart').then((module) => ({ default: module.CartPage })))
const CheckoutPage = lazy(() => import('../pages/checkout').then((module) => ({ default: module.CheckoutPage })))
const AuthPage = lazy(() => import('../pages/auth').then((module) => ({ default: module.AuthPage })))
const AccountLayout = lazy(() => import('../pages/account').then((module) => ({ default: module.AccountLayout })))
const AccountPage = lazy(() => import('../pages/account').then((module) => ({ default: module.AccountPage })))
const OrdersPage = lazy(() => import('../pages/orders').then((module) => ({ default: module.OrdersPage })))
const OrderDetailsPage = lazy(() => import('../pages/orders').then((module) => ({ default: module.OrderDetailsPage })))
const AdminLayout = lazy(() => import('../pages/admin').then((module) => ({ default: module.AdminLayout })))
const AdminOverviewPage = lazy(() => import('../pages/admin').then((module) => ({ default: module.AdminOverviewPage })))
const AdminProductsPage = lazy(() => import('../pages/admin').then((module) => ({ default: module.AdminProductsPage })))
const AdminProductPage = lazy(() => import('../pages/admin').then((module) => ({ default: module.AdminProductPage })))
const AdminOrdersPage = lazy(() => import('../pages/admin').then((module) => ({ default: module.AdminOrdersPage })))
const AdminOrderPage = lazy(() => import('../pages/admin').then((module) => ({ default: module.AdminOrderPage })))
const AdminCategoriesPage = lazy(() => import('../pages/admin').then((module) => ({ default: module.AdminCategoriesPage })))
const AdminUsersPage = lazy(() => import('../pages/admin').then((module) => ({ default: module.AdminUsersPage })))

function ScrollToTop() {
  const { pathname } = useLocation()
  useEffect(() => { window.scrollTo(0, 0) }, [pathname])
  return null
}

function Shell() {
  return <><ScrollToTop /><SiteHeader /><main className="min-h-[60vh]"><Outlet /></main><SiteFooter /></>
}

const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false, staleTime: 60_000, refetchOnWindowFocus: false } } })

export default function App() {
  return <QueryClientProvider client={queryClient}><BrowserRouter><Suspense fallback={<Loading />}><Routes><Route element={<Shell />}><Route index element={<HomePage />} /><Route path="catalog" element={<CatalogPage />} /><Route path="products/:slug" element={<ProductPage />} /><Route path="favorites" element={<FavoritesPage />} /><Route path="cart" element={<CartPage />} /><Route path="checkout" element={<CheckoutPage />} /><Route path="login" element={<AuthPage />} /><Route path="register" element={<AuthPage />} /><Route path="orders/:id/confirmed" element={<OrderDetailsPage confirmed />} /><Route path="account" element={<AccountLayout />}><Route index element={<AccountPage />} /><Route path="orders" element={<OrdersPage />} /><Route path="orders/:id" element={<OrderDetailsPage />} /></Route><Route path="admin" element={<AdminLayout />}><Route index element={<AdminOverviewPage />} /><Route path="products" element={<AdminProductsPage />} /><Route path="products/:id" element={<AdminProductPage />} /><Route path="orders" element={<AdminOrdersPage />} /><Route path="orders/:id" element={<AdminOrderPage />} /><Route path="categories" element={<AdminCategoriesPage />} /><Route path="users" element={<AdminUsersPage />} /></Route><Route path="*" element={<div className="page-container py-24 text-center"><h1 className="display-title">Страница не найдена</h1><Link to="/" className="mt-8 inline-block text-sm underline underline-offset-4">На главную</Link></div>} /></Route></Routes></Suspense></BrowserRouter></QueryClientProvider>
}
