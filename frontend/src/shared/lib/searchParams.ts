/** A copy of the filters with one value set (or removed when empty), back on the first page. */
export function withFilter(params: URLSearchParams, name: string, value: string): URLSearchParams {
  const next = new URLSearchParams(params)
  if (value) next.set(name, value)
  else next.delete(name)
  next.delete('page')
  return next
}
