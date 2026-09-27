import { useLocation } from 'react-router-dom'
import { AuthForm } from '../../../features/auth'

export function AuthPage() {
  const location = useLocation()
  const mode = location.pathname === '/register' ? 'register' : 'login'
  return <div className="grid min-h-[620px] lg:grid-cols-2"><div className="flex items-center justify-center px-5 py-14 sm:px-10"><AuthForm key={mode} mode={mode} /></div><div className="relative hidden min-h-[620px] overflow-hidden bg-mist lg:block"><img src="/images/blazer.webp" alt="Новая коллекция DATAM" className="h-full w-full object-cover object-center" /><div className="absolute bottom-10 left-10 max-w-xs font-display text-4xl leading-none text-white [text-shadow:0_2px_14px_rgba(0,0,0,.5)]">Твой стиль.<br />Твой ритм.</div></div></div>
}
