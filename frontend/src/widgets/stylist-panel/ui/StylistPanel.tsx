import { useEffect, useRef, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Maximize2, MessageCircle, Minimize2, X } from 'lucide-react'
import { Link, useLocation, useSearchParams } from 'react-router-dom'
import { userApi } from '../../../entities/user'
import { CHAT_HIDDEN_PATHS, chatHref } from '../../../shared/lib/chat'
import { StylistChat } from './StylistChat'

export function StylistPanel() {
  const { pathname, search } = useLocation()
  const [params, setParams] = useSearchParams()
  const [expanded, setExpanded] = useState(false)
  const [wide, setWide] = useState(false)
  const dialog = useRef<HTMLDialogElement>(null)
  const user = useQuery({ queryKey: ['user'], queryFn: userApi.session, retry: false })
  const hidden = CHAT_HIDDEN_PATHS.test(pathname)
  const open = !hidden && (expanded || params.get('stylist') === 'open')

  function close() {
    setExpanded(false)
    if (params.has('stylist')) {
      const next = new URLSearchParams(params)
      next.delete('stylist')
      setParams(next, { replace: true })
    }
  }

  useEffect(() => {
    const element = dialog.current
    if (!open || !element) return
    const previous = document.activeElement
    const overflow = document.body.style.overflow
    element.showModal()
    document.body.style.overflow = 'hidden'
    return () => {
      element.close()
      document.body.style.overflow = overflow
      if (previous instanceof HTMLElement) previous.focus()
    }
  }, [open])

  const loginUrl = `/login?returnTo=${encodeURIComponent(chatHref(pathname, search))}`

  return (
    <>
      {!hidden && (
        <button
          type="button"
          onClick={() => setExpanded(true)}
          aria-haspopup="dialog"
          aria-expanded={open}
          aria-controls="stylist-panel"
          className="fixed bottom-5 right-5 z-40 flex items-center gap-3 rounded-full bg-ink py-2.5 pl-2.5 pr-6 text-left text-white shadow-tactile transition hover:-translate-y-0.5 hover:bg-black focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-ink sm:bottom-8 sm:right-8"
        >
          <span className="flex h-11 w-11 items-center justify-center rounded-full bg-white/10">
            <MessageCircle size={21} strokeWidth={1.6} />
          </span>
          <span className="flex flex-col leading-tight">
            <span className="text-sm font-medium">Чат</span>
            <span className="mt-0.5 hidden text-[11px] text-white/70 sm:block">Подберём образ</span>
          </span>
        </button>
      )}
      <dialog
        ref={dialog}
        id="stylist-panel"
        aria-labelledby="stylist-title"
        onCancel={(event) => {
          event.preventDefault()
          close()
        }}
        onClick={(event) => {
          if (event.target === event.currentTarget) close()
        }}
        className={`stylist-panel fixed inset-y-0 left-auto right-0 m-0 h-dvh max-h-none w-full max-w-full border-0 bg-white p-0 text-ink shadow-panel transition-[max-width] duration-200 backdrop:bg-black/20 sm:max-w-[540px] ${
          wide ? 'lg:max-w-[880px]' : 'lg:max-w-[600px]'
        }`}
      >
        <div className="flex h-full flex-col" onClick={(event) => event.stopPropagation()}>
          <header className="flex shrink-0 items-center justify-between gap-4 border-b border-line px-6 py-5">
            <div>
              <h2 id="stylist-title" className="font-display text-[28px] leading-none tracking-[-.03em]">
                Чат
              </h2>
              <p className="mt-2 text-[11px] text-muted">Персональный подбор · DATAM</p>
            </div>
            <div className="flex items-center gap-1">
              <button
                type="button"
                onClick={() => setWide(!wide)}
                aria-pressed={wide}
                aria-label={wide ? 'Свернуть чат' : 'Развернуть чат'}
                title={wide ? 'Свернуть' : 'Развернуть'}
                className="hidden h-10 w-10 items-center justify-center rounded-full transition hover:bg-mist focus-visible:outline lg:flex"
              >
                {wide ? <Minimize2 size={18} strokeWidth={1.5} /> : <Maximize2 size={18} strokeWidth={1.5} />}
              </button>
              <button
                type="button"
                onClick={close}
                aria-label="Закрыть чат"
                className="flex h-10 w-10 items-center justify-center rounded-full transition hover:bg-mist focus-visible:outline"
              >
                <X size={20} strokeWidth={1.5} />
              </button>
            </div>
          </header>
          {user.isPending ? (
            <p role="status" className="p-6 text-sm text-muted">
              Подключаемся…
            </p>
          ) : user.error ? (
            <div className="p-6">
              <p role="alert" className="text-sm">
                Не удалось подключиться.
              </p>
              <button
                type="button"
                onClick={() => user.refetch()}
                className="mt-4 text-sm underline underline-offset-4"
              >
                Попробовать снова
              </button>
            </div>
          ) : user.data ? (
            <StylistChat key={user.data.id} open={open} onNavigate={close} />
          ) : (
            <div className="flex flex-1 flex-col justify-center px-8 pb-16">
              <p className="text-[10px] uppercase tracking-[.2em] text-muted">Немного вдохновения</p>
              <h3 className="mt-5 font-display text-[42px] leading-[1.08] tracking-[-.045em]">
                Ваш стиль.
                <br />
                Начнём с диалога.
              </h3>
              <p className="mt-5 text-sm leading-6 text-muted">
                Расскажите о планах — подберём вещи из каталога под ваш повод и бюджет.
              </p>
              <Link
                to={loginUrl}
                onClick={close}
                className="mt-8 flex min-h-12 items-center justify-center bg-ink px-6 text-sm text-white"
              >
                Войти и начать
              </Link>
              <p className="mt-4 text-center text-xs text-muted">Диалог доступен после входа</p>
            </div>
          )}
        </div>
      </dialog>
    </>
  )
}
