import { useState } from 'react'
import type { FormEvent } from 'react'
import { Link, Navigate } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Check, ShoppingBag, Sparkles } from 'lucide-react'
import { cartApi } from '../../../entities/cart'
import type { Cart } from '../../../entities/cart'
import { ProductCard } from '../../../entities/product'
import { userApi } from '../../../entities/user'
import { stylistApi } from '../../../features/stylist'
import type { OutfitAudience, OutfitItem } from '../../../features/stylist'
import { ApiError } from '../../../shared/api/client'
import { money } from '../../../shared/lib/format'
import { Button } from '../../../shared/ui/Button'
import { ErrorState, Loading } from '../../../shared/ui/States'

const examples = [
  'Свидание вечером в ресторане, на улице +5 и дождь, хочу выглядеть элегантно',
  'Первый день в офисе, дресс-код business casual, весна',
  'Прогулка по городу на выходных, солнечно, около +20',
]

type Sizes = Record<string, string | null>

function stylistError(error: Error): string {
  return error instanceof ApiError && error.status === 503 ? 'ИИ-стилист сейчас недоступен. Проверьте, что Ollama запущена, и попробуйте ещё раз.' : error.message
}

function sizesOf(item: OutfitItem) {
  return item.product.variants.filter((variant) => variant.is_active && variant.stock > 0).sort((a, b) => a.position - b.position)
}

function priceOf(item: OutfitItem, variantId: string | null): number {
  return Number(item.product.variants.find((variant) => variant.id === variantId)?.price ?? item.product.price)
}

function OutfitPiece({ item, size, onSize }: { item: OutfitItem; size: string | null; onSize: (id: string) => void }) {
  const sizes = sizesOf(item)
  return <div>
    <ProductCard product={item.product} />
    {item.reason && <p className="mt-2 text-xs leading-5 text-muted">{item.reason}</p>}
    {sizes.length > 0 && <div className="mt-3 flex flex-wrap gap-1.5" role="group" aria-label={`Размер: ${item.product.name}`}>{sizes.map((variant) => <button key={variant.id} type="button" onClick={() => onSize(variant.id)} aria-pressed={size === variant.id} className={`min-h-9 min-w-10 border px-2 text-xs transition-colors ${size === variant.id ? 'border-ink bg-ink text-white' : 'border-line hover:border-ink'}`}>{variant.options.size ?? variant.name}</button>)}</div>}
  </div>
}

export function StylistPage() {
  const client = useQueryClient()
  const user = useQuery({ queryKey: ['user'], queryFn: userApi.session, retry: false })
  const [prompt, setPrompt] = useState('')
  const [sizes, setSizes] = useState<Sizes>({})
  const addAll = useMutation({
    mutationFn: async (items: OutfitItem[]) => {
      let cart: Cart | undefined
      for (const item of items) cart = await cartApi.add(item.product.id, sizes[item.product.id] ?? null)
      return cart
    },
    onSuccess: (cart) => client.setQueryData(['cart'], cart),
    onError: () => client.invalidateQueries({ queryKey: ['cart'] }),
  })
  const outfit = useMutation({
    mutationFn: stylistApi.outfit,
    onSuccess: (data) => { setSizes(Object.fromEntries(data.items.map((item) => [item.product.id, item.variant_id]))); addAll.reset() },
  })

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const data = new FormData(event.currentTarget)
    const audience = String(data.get('audience'))
    outfit.mutate({ prompt: prompt.trim(), budget: Number(data.get('budget')), audience: audience ? audience as OutfitAudience : null })
  }

  if (user.isPending) return <Loading />
  if (user.error) return <ErrorState error={user.error} retry={() => user.refetch()} />
  if (!user.data) return <Navigate to="/login?returnTo=%2Fstylist" replace />

  const result = outfit.data
  const total = result ? result.items.reduce((sum, item) => sum + priceOf(item, sizes[item.product.id] ?? null), 0) : 0

  return <div className="page-container pt-9">
    <h1 className="display-title">ИИ-стилист</h1>
    <p className="mt-4 max-w-2xl text-sm leading-6 text-muted">Опишите повод, погоду и дресс-код, и стилист соберёт образ из вещей, которые есть в наличии, не выходя за ваш бюджет.</p>
    <div className="mt-10 grid gap-10 lg:grid-cols-[380px_minmax(0,1fr)]">
      <form onSubmit={submit} className="h-fit bg-mist p-6 sm:p-8 lg:sticky lg:top-24">
        <label className="block"><span className="field-label">Что за повод?</span><textarea value={prompt} onChange={(event) => setPrompt(event.target.value)} required minLength={5} maxLength={1000} rows={5} className="w-full resize-y border border-line bg-white p-4 text-sm outline-none focus:border-ink" placeholder="Например: свидание вечером, на улице прохладно, дресс-код smart casual" /></label>
        <div className="mt-3 flex flex-wrap gap-2">{examples.map((example) => <button key={example} type="button" onClick={() => setPrompt(example)} className="border border-line bg-white px-3 py-1.5 text-left text-[11px] leading-4 transition-colors hover:border-ink">{example}</button>)}</div>
        <div className="mt-6 grid gap-5 sm:grid-cols-2 lg:grid-cols-1">
          <label><span className="field-label">Бюджет, ₸</span><input name="budget" type="number" required min={1000} step={1000} defaultValue={150000} className="field" /></label>
          <label><span className="field-label">Для кого</span><select name="audience" defaultValue="" className="field"><option value="">Не важно</option><option value="women">Женское</option><option value="men">Мужское</option></select></label>
        </div>
        <Button full type="submit" className="mt-7" disabled={outfit.isPending}><Sparkles size={17} />{outfit.isPending ? 'Подбираем образ...' : 'Подобрать образ'}</Button>
      </form>

      <section aria-live="polite">
        {outfit.isPending && <div className="flex min-h-[320px] flex-col items-center justify-center gap-3 border border-line text-center" role="status"><Sparkles size={22} className="animate-pulse" /><p className="text-sm">Стилист подбирает образ...</p><p className="text-xs text-muted">Обычно это занимает от 10 секунд до минуты.</p></div>}
        {outfit.isError && <p role="alert" className="border border-red-200 bg-red-50 p-5 text-sm text-red-700">{stylistError(outfit.error)}</p>}
        {!outfit.isPending && !outfit.isError && !result && <div className="flex min-h-[320px] items-center justify-center border border-dashed border-line p-8 text-center text-sm text-muted">Здесь появится ваш образ</div>}
        {!outfit.isPending && result && <div>
          <h2 className="section-title">{result.title}</h2>
          {result.summary && <p className="mt-3 max-w-2xl text-sm leading-6 text-muted">{result.summary}</p>}
          {result.notes.length > 0 && <ul className="mt-5 space-y-1.5 border-l-2 border-amber-500 bg-amber-50 px-4 py-3 text-sm text-amber-900">{result.notes.map((note) => <li key={note}>{note}</li>)}</ul>}
          {result.items.length === 0 ? <Link to="/catalog" className="mt-6 inline-block text-sm underline underline-offset-4">Посмотреть весь каталог</Link> : <>
            <div className="mt-8 grid grid-cols-2 gap-x-4 gap-y-9 xl:grid-cols-3">{result.items.map((item) => <OutfitPiece key={item.product.id} item={item} size={sizes[item.product.id] ?? null} onSize={(id) => { setSizes({ ...sizes, [item.product.id]: id }); addAll.reset() }} />)}</div>
            <div className="mt-10 flex flex-col gap-4 border-t border-line pt-6 sm:flex-row sm:items-center sm:justify-between">
              <div><p className="text-base font-medium">Итого {money(total)}</p><p className="mt-1 text-xs text-muted">Бюджет {money(result.budget)}</p>{total > Number(result.budget) && <p className="mt-1 text-xs text-red-700">С выбранными размерами образ дороже бюджета</p>}</div>
              <Button onClick={() => addAll.mutate(result.items)} disabled={addAll.isPending || addAll.isSuccess}>{addAll.isSuccess ? <><Check size={17} />В корзине</> : <><ShoppingBag size={17} />{addAll.isPending ? 'Добавляем...' : 'Добавить весь образ в корзину'}</>}</Button>
            </div>
            {addAll.isSuccess && <p role="status" className="mt-3 text-right text-sm text-[#458052]">Образ добавлен. <Link to="/cart" className="underline underline-offset-4">Перейти в корзину</Link></p>}
            {addAll.isError && <p role="alert" className="mt-3 text-right text-sm text-red-700">{addAll.error.message}</p>}
          </>}
        </div>}
      </section>
    </div>
  </div>
}
