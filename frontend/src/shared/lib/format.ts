export function money(value: string | number, currency = 'KZT'): string {
  return new Intl.NumberFormat('ru-KZ', { style: 'currency', currency, maximumFractionDigits: 0 }).format(Number(value))
}

export function date(value: string): string {
  return new Intl.DateTimeFormat('ru-KZ', { day: 'numeric', month: 'long', year: 'numeric' }).format(new Date(value))
}

export function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : 'Попробуйте ещё раз'
}
