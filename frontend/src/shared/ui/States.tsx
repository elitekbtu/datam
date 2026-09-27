import { Link } from 'react-router-dom'
import { Button } from './Button'
import { errorMessage } from '../lib/format'

export function Loading({ label = 'Загружаем...' }: { label?: string }) {
  return <div className="page-container flex min-h-[40vh] items-center justify-center text-sm text-muted" role="status">{label}</div>
}

export function ErrorState({ error, retry }: { error: unknown; retry?: () => void }) {
  return <div className="page-container flex min-h-[40vh] flex-col items-center justify-center gap-5 text-center"><h2 className="font-display text-3xl">Что-то пошло не так</h2><p className="max-w-md text-sm text-muted">{errorMessage(error)}</p>{retry && <Button onClick={retry}>Повторить</Button>}</div>
}

export function EmptyState({ title, body, action = 'Перейти в каталог' }: { title: string; body: string; action?: string }) {
  return <div className="mx-auto flex max-w-lg flex-col items-center gap-5 py-20 text-center"><h2 className="font-display text-4xl">{title}</h2><p className="text-sm leading-6 text-muted">{body}</p><Link to="/catalog" className="inline-flex min-h-12 items-center bg-ink px-7 text-sm text-white shadow-sm transition hover:-translate-y-0.5 hover:shadow-tactile">{action} →</Link></div>
}
