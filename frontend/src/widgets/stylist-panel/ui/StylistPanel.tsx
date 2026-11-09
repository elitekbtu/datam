import { useEffect, useRef, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Sparkles, X } from 'lucide-react'
import { Link, useLocation, useSearchParams } from 'react-router-dom'
import { userApi } from '../../../entities/user'
import { StylistChat } from './StylistChat'

export function StylistPanel() {
  const { pathname, search } = useLocation()
  const [params, setParams] = useSearchParams()
  const [expanded, setExpanded] = useState(false)
  const dialog = useRef<HTMLDialogElement>(null)
  const user = useQuery({ queryKey: ['user'], queryFn: userApi.session, retry: false })
  const hidden = /^\/(admin|login|register|checkout)(\/|$)/.test(pathname)
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

  const returnParams = new URLSearchParams(search)
  returnParams.set('stylist', 'open')
  const loginUrl = `/login?returnTo=${encodeURIComponent(`${pathname}?${returnParams}`)}`

  return (
    <>
      {!hidden && (
        <button
          type="button"
          onClick={() => setExpanded(true)}
          aria-haspopup="dialog"
          aria-expanded={open}
          aria-controls="stylist-panel"
          className="fixed bottom-5 right-5 z-40 flex min-h-12 items-center gap-3 rounded-full border border-line bg-white px-5 text-xs shadow-panel transition hover:-translate-y-0.5 hover:border-ink focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-4 sm:bottom-7 sm:right-8"
        >
          <Sparkles size={17} strokeWidth={1.5} />
          <span>ИИ-стилист</span>
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
        className="stylist-panel fixed inset-y-0 left-auto right-0 m-0 h-dvh max-h-none w-full max-w-[460px] border-0 bg-white p-0 text-ink shadow-panel backdrop:bg-black/20"
      >
        <div className="flex h-full flex-col" onClick={(event) => event.stopPropagation()}>
          <header className="flex shrink-0 items-center justify-between border-b border-line px-6 py-5">
            <div className="flex items-center gap-3">
              <Sparkles size={20} strokeWidth={1.3} />
              <div>
                <h2 id="stylist-title" className="text-sm font-medium">
                  Ваш ИИ-стилист
                </h2>
                <p className="mt-1 text-[11px] text-muted">Персональный подбор · DATAM</p>
              </div>
            </div>
            <button
              type="button"
              onClick={close}
              aria-label="Закрыть чат"
              className="flex h-10 w-10 items-center justify-center rounded-full transition hover:bg-mist focus-visible:outline"
            >
              <X size={20} strokeWidth={1.5} />
            </button>
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
