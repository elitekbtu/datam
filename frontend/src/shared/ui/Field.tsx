import type { ReactNode } from 'react'

type FieldProps = { label: string; className?: string; children: ReactNode }

export function Field({ label, className, children }: FieldProps) {
  return (
    <label className={className}>
      <span className="field-label">{label}</span>
      {children}
    </label>
  )
}
