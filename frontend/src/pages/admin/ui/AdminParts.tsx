import type { ReactNode } from 'react'
import { Button } from '../../../shared/ui/Button'

export function PageHeading({ title, action }: { title: string; action?: ReactNode }) {
  return <div className="mb-7 flex flex-wrap items-end justify-between gap-4"><h2 className="font-display text-3xl tracking-tight sm:text-4xl">{title}</h2>{action}</div>
}

export function FormError({ error }: { error: Error | null }) {
  return error ? <p role="alert" className="mt-4 text-sm text-red-700">{error.message}</p> : null
}

export function Pagination({ total, offset, limit, onChange }: { total: number; offset: number; limit: number; onChange: (offset: number) => void }) {
  if (total <= limit) return null
  return <div className="mt-7 flex items-center justify-between gap-3 text-xs"><span className="text-muted">{offset + 1}–{Math.min(offset + limit, total)} из {total}</span><div className="flex gap-2"><Button variant="outline" className="min-h-9 px-3 text-xs" disabled={offset === 0} onClick={() => onChange(Math.max(0, offset - limit))}>Назад</Button><Button variant="outline" className="min-h-9 px-3 text-xs" disabled={offset + limit >= total} onClick={() => onChange(offset + limit)}>Далее</Button></div></div>
}

export function ConfirmButton({ label, onConfirm, disabled = false }: { label: string; onConfirm: () => void; disabled?: boolean }) {
  return <button type="button" disabled={disabled} onClick={() => { if (window.confirm(`Подтвердить: ${label.toLowerCase()}?`)) onConfirm() }} className="text-xs text-red-700 underline underline-offset-4 disabled:opacity-50">{label}</button>
}
