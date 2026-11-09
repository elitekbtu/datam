import { useEffect, useRef, useState } from 'react'
import type { FormEvent } from 'react'
import { ArrowUp, Plus, SlidersHorizontal, Square } from 'lucide-react'
import { stylistApi } from '../../../features/stylist'
import type { Outfit, OutfitAudience, OutfitRequest } from '../../../features/stylist'
import { ApiError } from '../../../shared/api/client'
import { money } from '../../../shared/lib/format'
import { StylistOutfit } from './StylistOutfit'

type Message = { id: number; role: 'user'; text: string } | { id: number; role: 'assistant'; outfit: Outfit }
const starters = ['Образ для офиса', 'На свидание', 'Выходные в городе']

function history(messages: Message[]): OutfitRequest['history'] {
  return messages.slice(-8).map((message) => ({
    role: message.role,
    content: (message.role === 'user'
      ? message.text
      : [
          message.outfit.title,
          message.outfit.summary,
          ...message.outfit.items.map(({ product }) => product.name)
        ].join('. ')
    ).slice(0, 1000)
  }))
}

function errorText(error: unknown) {
  if (error instanceof ApiError && error.status === 401)
    return 'Сессия закончилась. Войдите в аккаунт ещё раз.'
  if (error instanceof ApiError && error.status === 503)
    return 'Стилист сейчас занят или недоступен. Попробуйте чуть позже.'
  return 'Не удалось получить ответ. Проверьте соединение и попробуйте снова.'
}

export function StylistChat({ open, onNavigate }: { open: boolean; onNavigate: () => void }) {
  const [messages, setMessages] = useState<Message[]>([])
  const [draft, setDraft] = useState('')
  const [budget, setBudget] = useState('150000')
  const [audience, setAudience] = useState<OutfitAudience | ''>('')
  const [pending, setPending] = useState(false)
  const [error, setError] = useState('')
  const [retry, setRetry] = useState<OutfitRequest | null>(null)
  const controller = useRef<AbortController | null>(null)
  const sequence = useRef(0)
  const scroll = useRef<HTMLDivElement>(null)
  const input = useRef<HTMLTextAreaElement>(null)

  useEffect(() => () => controller.current?.abort(), [])
  useEffect(() => {
    if (open && scroll.current) scroll.current.scrollTop = scroll.current.scrollHeight
  }, [messages, pending, error, open])

  async function send(payload: OutfitRequest) {
    if (controller.current) return
    const request = new AbortController()
    controller.current = request
    setPending(true)
    setError('')
    setRetry(null)
    try {
      const outfit = await stylistApi.outfit(
        payload,
        AbortSignal.any([request.signal, AbortSignal.timeout(135_000)])
      )
      if (!request.signal.aborted) {
        const id = ++sequence.current
        setMessages((current) => [...current, { id, role: 'assistant', outfit }])
      }
    } catch (failure) {
      if (!request.signal.aborted) {
        setError(errorText(failure))
        setRetry(payload)
      }
    } finally {
      if (controller.current === request) {
        controller.current = null
        setPending(false)
      }
    }
  }

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const prompt = draft.trim()
    if (!prompt || pending) return
    const payload: OutfitRequest = {
      prompt,
      budget: Number(budget),
      audience: audience || null,
      history: history(messages)
    }
    const id = ++sequence.current
    setMessages((current) => [...current, { id, role: 'user', text: prompt }])
    setDraft('')
    void send(payload)
  }

  function stop() {
    controller.current?.abort()
    controller.current = null
    setPending(false)
    const last = messages.at(-1)
    if (last?.role === 'user') {
      setDraft(last.text)
      setMessages((current) => current.slice(0, -1))
    }
  }

  function reset() {
    controller.current?.abort()
    controller.current = null
    setMessages([])
    setDraft('')
    setError('')
    setRetry(null)
    setPending(false)
    input.current?.focus()
  }

  return (
    <>
      <div className="flex shrink-0 items-center justify-between border-b border-line px-6 py-3 text-[11px] text-muted">
        <span>Вещи из нашего каталога</span>
        <button
          type="button"
          onClick={reset}
          className="flex min-h-8 items-center gap-1.5 text-ink hover:text-muted"
        >
          <Plus size={14} />
          Новый диалог
        </button>
      </div>
      <div
        ref={scroll}
        className="min-h-0 flex-1 overflow-y-auto overscroll-contain px-6 py-6"
        role="log"
        aria-label="Диалог со стилистом"
        aria-live="polite"
        aria-relevant="additions"
      >
        {!messages.length && (
          <div className="py-8">
            <p className="text-[10px] uppercase tracking-[.2em] text-muted">Меньше поисков. Больше вас.</p>
            <h3 className="mt-5 font-display text-[42px] leading-[1.08] tracking-[-.045em]">
              Что наденем
              <br />
              сегодня?
            </h3>
            <p className="mt-5 max-w-[310px] text-sm leading-6 text-muted">
              Расскажите о поводе, погоде или настроении. Соберём образ, в котором будет хорошо.
            </p>
            <div className="mt-7 flex flex-wrap gap-2">
              {starters.map((text) => (
                <button
                  type="button"
                  key={text}
                  onClick={() => {
                    setDraft(text)
                    input.current?.focus()
                  }}
                  className="rounded-full border border-line px-3.5 py-2.5 text-xs transition hover:border-ink"
                >
                  {text}
                </button>
              ))}
            </div>
          </div>
        )}
        <div className="space-y-7">
          {messages.map((message) =>
            message.role === 'user' ? (
              <div
                key={message.id}
                className="ml-auto w-fit max-w-[calc(100%-2.25rem)] whitespace-pre-wrap break-words rounded-2xl rounded-br-sm bg-mist px-4 py-3 text-sm leading-6"
              >
                <span className="sr-only">Вы: </span>
                {message.text}
              </div>
            ) : (
              <StylistOutfit key={message.id} outfit={message.outfit} onNavigate={onNavigate} />
            )
          )}
        </div>
        {pending && (
          <div role="status" className="mt-7 flex items-center gap-3 text-xs text-muted">
            <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-ink" />
            Подбираю вещи под ваш запрос…
          </div>
        )}
        {error && (
          <div className="mt-6 border-l-2 border-ink pl-4">
            <p role="alert" className="text-xs leading-5">
              {error}
            </p>
            {retry && (
              <button
                type="button"
                onClick={() => void send(retry)}
                disabled={pending}
                className="mt-2 text-xs underline underline-offset-4"
              >
                Повторить запрос
              </button>
            )}
          </div>
        )}
      </div>
      <form
        onSubmit={submit}
        className="shrink-0 border-t border-line bg-white px-6 pb-[max(1.25rem,env(safe-area-inset-bottom))] pt-4"
      >
        <details className="mb-3 text-xs">
          <summary className="flex cursor-pointer list-none items-center gap-2 text-muted">
            <SlidersHorizontal size={14} />
            <span>
              До {money(Number(budget) || 0)} ·{' '}
              {audience === 'women' ? 'Женское' : audience === 'men' ? 'Мужское' : 'Для всех'}
            </span>
          </summary>
          <div className="mt-3 grid grid-cols-2 gap-3">
            <label>
              <span className="mb-1.5 block text-muted">Бюджет, ₸</span>
              <input
                aria-label="Бюджет, ₸"
                type="number"
                required
                min="1"
                max="9999999999"
                step="1"
                value={budget}
                onChange={(event) => setBudget(event.target.value)}
                className="h-10 w-full border border-line px-3 outline-none focus:border-ink"
              />
            </label>
            <label>
              <span className="mb-1.5 block text-muted">Для кого</span>
              <select
                aria-label="Для кого"
                value={audience}
                onChange={(event) => setAudience(event.target.value as OutfitAudience | '')}
                className="h-10 w-full border border-line bg-white px-3"
              >
                <option value="">Для всех</option>
                <option value="women">Женское</option>
                <option value="men">Мужское</option>
              </select>
            </label>
          </div>
        </details>
        <div className="flex items-end gap-2 rounded-2xl border border-line p-3 transition focus-within:border-ink">
          <textarea
            ref={input}
            aria-label="Сообщение стилисту"
            placeholder={messages.length ? 'Что изменим в образе?' : 'Например, образ на вечер…'}
            value={draft}
            onChange={(event) => setDraft(event.target.value)}
            maxLength={1000}
            rows={2}
            onKeyDown={(event) => {
              if (event.key === 'Enter' && !event.shiftKey && !event.nativeEvent.isComposing) {
                event.preventDefault()
                event.currentTarget.form?.requestSubmit()
              }
            }}
            className="max-h-28 min-h-12 flex-1 resize-none bg-transparent text-sm leading-6 outline-none placeholder:text-muted"
          />
          {pending ? (
            <button
              key="stop"
              type="button"
              onClick={(event) => {
                event.preventDefault()
                stop()
              }}
              aria-label="Остановить подбор"
              className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-ink text-white"
            >
              <Square size={13} />
            </button>
          ) : (
            <button
              key="send"
              type="submit"
              disabled={!draft.trim()}
              aria-label="Отправить сообщение"
              className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-ink text-white transition disabled:bg-mist disabled:text-muted"
            >
              <ArrowUp size={18} />
            </button>
          )}
        </div>
        <p className="mt-3 text-center text-[10px] leading-4 text-muted">
          Подбор может занять до двух минут. Размер выбираете вы.
        </p>
      </form>
    </>
  )
}
