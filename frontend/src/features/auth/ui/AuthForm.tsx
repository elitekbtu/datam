import { useState } from 'react'
import type { FormEvent } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { ArrowRight } from 'lucide-react'
import { authApi } from '../api/authApi'
import { Button } from '../../../shared/ui/Button'

export function AuthForm({ mode }: { mode: 'login' | 'register' }) {
  const [params] = useSearchParams()
  const navigate = useNavigate()
  const client = useQueryClient()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [username, setUsername] = useState('')
  const [fullName, setFullName] = useState('')
  const returnTo = params.get('returnTo')?.startsWith('/') && !params.get('returnTo')?.startsWith('//') ? params.get('returnTo')! : '/account'
  const mutation = useMutation({
    mutationFn: () => mode === 'login' ? authApi.login(email, password) : authApi.register({ email, password, username, full_name: fullName || null }),
    onSuccess: async (user) => {
      client.setQueryData(['user'], user)
      await Promise.all([client.invalidateQueries({ queryKey: ['cart'] }), client.invalidateQueries({ queryKey: ['favorites'] })])
      navigate(returnTo, { replace: true })
    },
  })
  function submit(event: FormEvent) { event.preventDefault(); mutation.mutate() }
  return <form onSubmit={submit} className="mx-auto w-full max-w-[430px]">
    <h1 className="font-display text-[48px] leading-none tracking-[-.05em]">{mode === 'login' ? 'С возвращением' : 'Присоединяйтесь'}</h1>
    <p className="mt-4 text-sm leading-6 text-muted">{mode === 'login' ? 'Войдите, чтобы продолжить покупки.' : 'Создайте аккаунт и сохраните свой стиль.'}</p>
    <div className="mt-9 space-y-5">
      {mode === 'register' && <><label><span className="field-label">Имя</span><input className="field" value={fullName} onChange={(event) => setFullName(event.target.value)} autoComplete="name" placeholder="Как к вам обращаться" /></label><label><span className="field-label">Имя пользователя</span><input className="field" required minLength={3} maxLength={32} value={username} onChange={(event) => setUsername(event.target.value)} autoComplete="username" placeholder="Ваш логин" /></label></>}
      <label className="block"><span className="field-label">Email</span><input className="field" required type="email" value={email} onChange={(event) => setEmail(event.target.value)} autoComplete="email" placeholder="you@example.com" /></label>
      <label className="block"><span className="field-label">Пароль</span><input className="field" required type="password" minLength={8} maxLength={72} value={password} onChange={(event) => setPassword(event.target.value)} autoComplete={mode === 'login' ? 'current-password' : 'new-password'} placeholder="Не менее 8 символов" /></label>
    </div>
    {mutation.isError && <p role="alert" className="mt-5 text-sm text-red-700">{mutation.error.message}</p>}
    <Button full type="submit" disabled={mutation.isPending} className="mt-7">{mutation.isPending ? 'Подождите...' : mode === 'login' ? 'Войти' : 'Зарегистрироваться'} <ArrowRight size={16} /></Button>
    <p className="mt-6 text-center text-sm text-muted">{mode === 'login' ? 'Нет аккаунта?' : 'Уже есть аккаунт?'} <Link className="ml-1 text-ink underline underline-offset-4" to={`${mode === 'login' ? '/register' : '/login'}?returnTo=${encodeURIComponent(returnTo)}`}>{mode === 'login' ? 'Зарегистрироваться' : 'Войти'}</Link></p>
  </form>
}
