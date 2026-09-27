import type { ButtonHTMLAttributes, ReactNode } from 'react'

type Props = ButtonHTMLAttributes<HTMLButtonElement> & { children: ReactNode; variant?: 'dark' | 'outline'; full?: boolean }

export function Button({ children, variant = 'dark', full = false, className = '', ...props }: Props) {
  return <button {...props} className={`${full ? 'w-full' : ''} inline-flex min-h-12 items-center justify-center gap-2 px-6 text-sm font-medium transition-[transform,box-shadow,background-color] duration-200 hover:-translate-y-0.5 hover:shadow-tactile active:translate-y-0 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ink disabled:translate-y-0 disabled:opacity-50 disabled:shadow-none ${variant === 'dark' ? 'bg-ink text-white hover:bg-[#292929]' : 'border border-ink bg-white text-ink hover:bg-mist'} ${className}`}>{children}</button>
}
