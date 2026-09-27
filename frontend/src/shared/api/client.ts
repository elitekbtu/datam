export class ApiError extends Error {
  status: number
  constructor(status: number, message: string) { super(message); this.status = status }
}

type Options = Omit<RequestInit, 'body'> & { body?: unknown }
let csrfToken: string | null = null
let refreshPromise: Promise<boolean> | null = null

async function ensureCsrf(): Promise<string> {
  if (csrfToken) return csrfToken
  const response = await fetch('/api/auth/csrf', { credentials: 'include' })
  if (!response.ok) throw new ApiError(response.status, 'Не удалось подготовить безопасное соединение')
  const data = await response.json() as { csrf_token: string }
  csrfToken = data.csrf_token
  return csrfToken
}

async function send<T>(path: string, options: Options, canRefresh: boolean): Promise<T> {
  const method = options.method?.toUpperCase() ?? 'GET'
  const headers = new Headers(options.headers)
  if (options.body !== undefined && !(options.body instanceof FormData)) headers.set('Content-Type', 'application/json')
  if (!['GET', 'HEAD'].includes(method)) headers.set('X-CSRF-Token', await ensureCsrf())
  const response = await fetch(`/api${path}`, {
    ...options,
    method,
    body: options.body === undefined ? undefined : options.body instanceof FormData ? options.body : JSON.stringify(options.body),
    credentials: 'include',
    headers,
  })
  if (response.status === 401 && canRefresh && !path.startsWith('/auth/')) {
    refreshPromise ??= send('/auth/refresh', { method: 'POST' }, false).then(() => true).catch(() => false).finally(() => { refreshPromise = null })
    if (await refreshPromise) return send<T>(path, options, false)
  }
  if (!response.ok) {
    const data = await response.json().catch(() => null) as { detail?: string | Array<{ msg: string }> } | null
    const detail = data?.detail
    const message = typeof detail === 'string' ? detail : Array.isArray(detail) ? detail.map((item) => item.msg).join(', ') : 'Не удалось выполнить запрос'
    throw new ApiError(response.status, message)
  }
  if (response.status === 204) return undefined as T
  return response.json() as Promise<T>
}

export function api<T>(path: string, options: Options = {}): Promise<T> {
  return send<T>(path, options, true)
}
