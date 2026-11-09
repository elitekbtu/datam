// The chat is not offered where it would interrupt a task: admin, sign-in and checkout.
export const CHAT_HIDDEN_PATHS = /^\/(admin|login|register|checkout)(\/|$)/

/** A link that opens the chat on the current page, or on the home page where the chat is hidden. */
export function chatHref(pathname: string, search: string): string {
  if (CHAT_HIDDEN_PATHS.test(pathname)) return '/?stylist=open'
  const params = new URLSearchParams(search)
  params.set('stylist', 'open')
  return `${pathname}?${params}`
}
