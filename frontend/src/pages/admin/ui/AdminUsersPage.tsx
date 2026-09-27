import { useState } from 'react'
import type { FormEvent } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Plus, Search } from 'lucide-react'
import { adminApi } from '../../../features/admin'
import type { UserInput } from '../../../features/admin'
import type { User } from '../../../entities/user'
import { userApi } from '../../../entities/user'
import { Button } from '../../../shared/ui/Button'
import { ErrorState, Loading } from '../../../shared/ui/States'
import { ConfirmButton, FormError, PageHeading, Pagination } from './AdminParts'

const limit = 20

function UserForm({ user, onDone }: { user?: User; onDone: () => void }) {
  const client = useQueryClient()
  const save = useMutation({ mutationFn: (body: UserInput & { password?: string }) => user ? adminApi.updateUser(user.id, body) : adminApi.createUser(body as UserInput & { password: string }), onSuccess: () => { void client.invalidateQueries({ queryKey: ['admin'] }); void client.invalidateQueries({ queryKey: ['user'] }); onDone() } })
  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const data = new FormData(event.currentTarget)
    const password = String(data.get('password'))
    save.mutate({ email: String(data.get('email')).trim(), username: String(data.get('username')).trim(), full_name: String(data.get('full_name')).trim() || null, role: String(data.get('role')) as User['role'], is_active: data.get('is_active') === 'on', ...(password ? { password } : {}) })
  }
  return <form onSubmit={submit} className="mb-8 border border-line bg-mist p-5 sm:p-7"><h3 className="font-display text-2xl">{user ? 'Изменить пользователя' : 'Новый пользователь'}</h3><div className="mt-5 grid gap-4 sm:grid-cols-2"><label><span className="field-label">Email *</span><input name="email" type="email" className="field" required defaultValue={user?.email} /></label><label><span className="field-label">Имя пользователя *</span><input name="username" className="field" required minLength={3} maxLength={32} pattern="[a-zA-Z0-9_.\-]+" defaultValue={user?.username} /></label><label><span className="field-label">Полное имя</span><input name="full_name" className="field" maxLength={128} defaultValue={user?.full_name || ''} /></label><label><span className="field-label">Пароль {user ? '(оставьте пустым, чтобы не менять)' : '*'}</span><input name="password" type="password" className="field" minLength={8} maxLength={72} required={!user} autoComplete="new-password" /></label><label><span className="field-label">Роль</span><select name="role" className="field" defaultValue={user?.role || 'user'}><option value="user">Пользователь</option><option value="admin">Администратор</option></select></label></div><label className="mt-4 flex items-center gap-2 text-xs"><input name="is_active" type="checkbox" defaultChecked={user?.is_active ?? true} />Аккаунт активен</label><div className="mt-5 flex gap-3"><Button type="submit" disabled={save.isPending}>{save.isPending ? 'Сохраняем...' : 'Сохранить'}</Button><Button type="button" variant="outline" onClick={onDone}>Отмена</Button></div><FormError error={save.error} /></form>
}

export function AdminUsersPage() {
  const [offset, setOffset] = useState(0)
  const [search, setSearch] = useState('')
  const [editing, setEditing] = useState<User | 'new' | null>(null)
  const client = useQueryClient()
  const current = useQuery({ queryKey: ['user'], queryFn: userApi.session })
  const params = new URLSearchParams({ limit: String(limit), offset: String(offset) })
  if (search) params.set('search', search)
  const users = useQuery({ queryKey: ['admin', 'users', params.toString()], queryFn: () => adminApi.users(params) })
  const remove = useMutation({ mutationFn: adminApi.deleteUser, onSuccess: () => { void client.invalidateQueries({ queryKey: ['admin'] }) } })
  return <section><PageHeading title="Пользователи" action={<Button type="button" onClick={() => setEditing('new')}><Plus size={17} />Добавить пользователя</Button>} />{editing && <UserForm key={editing === 'new' ? 'new' : editing.id} user={editing === 'new' ? undefined : editing} onDone={() => setEditing(null)} />}<label className="relative mb-6 block"><span className="sr-only">Поиск пользователей</span><Search size={17} className="absolute left-4 top-1/2 -translate-y-1/2 text-muted" /><input className="field pl-11" placeholder="Email, имя пользователя или имя" value={search} onChange={(event) => { setSearch(event.target.value); setOffset(0) }} /></label>{users.isPending ? <Loading /> : users.error ? <ErrorState error={users.error} retry={() => users.refetch()} /> : <><div className="divide-y divide-line border-y border-line">{users.data?.items.map((user) => <div key={user.id} className="flex flex-wrap items-center gap-4 py-5"><div className="min-w-[210px] flex-1"><h3 className="text-sm font-medium">{user.full_name || user.username}{user.id === current.data?.id ? ' · Вы' : ''}</h3><p className="mt-1 text-xs text-muted">{user.email} · @{user.username}</p></div><span className="text-xs text-muted">{user.role === 'admin' ? 'Администратор' : 'Пользователь'} · {user.is_active ? 'Активен' : 'Отключён'}</span><button type="button" className="text-xs underline underline-offset-4" onClick={() => setEditing(user)}>Изменить</button>{user.id !== current.data?.id && <ConfirmButton label="Удалить" disabled={remove.isPending} onConfirm={() => remove.mutate(user.id)} />}</div>)}{!users.data?.items.length && <p className="py-12 text-center text-sm text-muted">Пользователи не найдены.</p>}</div><Pagination total={users.data?.total ?? 0} offset={offset} limit={limit} onChange={setOffset} /></>}<FormError error={remove.error} /></section>
}
