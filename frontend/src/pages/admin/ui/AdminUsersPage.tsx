import { useState } from 'react'
import type { FormEvent } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Plus } from 'lucide-react'
import { adminApi } from '../../../features/admin'
import type { UserInput } from '../../../features/admin'
import type { User } from '../../../entities/user'
import { userApi } from '../../../entities/user'
import { Button } from '../../../shared/ui/Button'
import { Field } from '../../../shared/ui/Field'
import { ErrorState, Loading } from '../../../shared/ui/States'
import { ConfirmButton, FormError, PageHeading, Pagination, SearchField } from './AdminParts'

const limit = 20

type UserBody = UserInput & { password?: string }

function UserForm({ user, onDone }: { user?: User; onDone: () => void }) {
  const client = useQueryClient()
  const save = useMutation({
    mutationFn: (body: UserBody) =>
      user
        ? adminApi.updateUser(user.id, body)
        : adminApi.createUser(body as UserInput & { password: string }),
    onSuccess: () => {
      void client.invalidateQueries({ queryKey: ['admin'] })
      void client.invalidateQueries({ queryKey: ['user'] })
      onDone()
    },
  })

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const data = new FormData(event.currentTarget)
    const text = (name: string) => String(data.get(name)).trim()
    // An empty password on edit means "keep the current one".
    const password = String(data.get('password'))
    save.mutate({
      email: text('email'),
      username: text('username'),
      full_name: text('full_name') || null,
      role: String(data.get('role')) as User['role'],
      is_active: data.get('is_active') === 'on',
      ...(password ? { password } : {}),
    })
  }

  return (
    <form onSubmit={submit} className="mb-8 border border-line bg-mist p-5 sm:p-7">
      <h3 className="font-display text-2xl">{user ? 'Изменить пользователя' : 'Новый пользователь'}</h3>
      <div className="mt-5 grid gap-4 sm:grid-cols-2">
        <Field label="Email *">
          <input name="email" type="email" className="field" required defaultValue={user?.email} />
        </Field>
        <Field label="Имя пользователя *">
          <input
            name="username"
            className="field"
            required
            minLength={3}
            maxLength={32}
            pattern="[a-zA-Z0-9_.\-]+"
            defaultValue={user?.username}
          />
        </Field>
        <Field label="Полное имя">
          <input name="full_name" className="field" maxLength={128} defaultValue={user?.full_name || ''} />
        </Field>
        <Field label={`Пароль ${user ? '(оставьте пустым, чтобы не менять)' : '*'}`}>
          <input
            name="password"
            type="password"
            className="field"
            minLength={8}
            maxLength={72}
            required={!user}
            autoComplete="new-password"
          />
        </Field>
        <Field label="Роль">
          <select name="role" className="field" defaultValue={user?.role || 'user'}>
            <option value="user">Пользователь</option>
            <option value="admin">Администратор</option>
          </select>
        </Field>
      </div>
      <label className="mt-4 flex items-center gap-2 text-xs">
        <input name="is_active" type="checkbox" defaultChecked={user?.is_active ?? true} />
        Аккаунт активен
      </label>
      <div className="mt-5 flex gap-3">
        <Button type="submit" disabled={save.isPending}>
          {save.isPending ? 'Сохраняем...' : 'Сохранить'}
        </Button>
        <Button type="button" variant="outline" onClick={onDone}>
          Отмена
        </Button>
      </div>
      <FormError error={save.error} />
    </form>
  )
}

type UserRowProps = { user: User; isSelf: boolean; deleting: boolean; onEdit: () => void; onDelete: () => void }

function UserRow({ user, isSelf, deleting, onEdit, onDelete }: UserRowProps) {
  return (
    <div className="flex flex-wrap items-center gap-4 py-5">
      <div className="min-w-[210px] flex-1">
        <h3 className="text-sm font-medium">
          {user.full_name || user.username}
          {isSelf ? ' · Вы' : ''}
        </h3>
        <p className="mt-1 text-xs text-muted">
          {user.email} · @{user.username}
        </p>
      </div>
      <span className="text-xs text-muted">
        {user.role === 'admin' ? 'Администратор' : 'Пользователь'} · {user.is_active ? 'Активен' : 'Отключён'}
      </span>
      <button type="button" className="text-xs underline underline-offset-4" onClick={onEdit}>
        Изменить
      </button>
      {!isSelf && <ConfirmButton label="Удалить" disabled={deleting} onConfirm={onDelete} />}
    </div>
  )
}

export function AdminUsersPage() {
  const [offset, setOffset] = useState(0)
  const [search, setSearch] = useState('')
  const [editing, setEditing] = useState<User | 'new' | null>(null)
  const client = useQueryClient()
  const current = useQuery({ queryKey: ['user'], queryFn: userApi.session })

  const params = new URLSearchParams({ limit: String(limit), offset: String(offset) })
  if (search) params.set('search', search)
  const users = useQuery({
    queryKey: ['admin', 'users', params.toString()],
    queryFn: () => adminApi.users(params),
  })
  const remove = useMutation({
    mutationFn: adminApi.deleteUser,
    onSuccess: () => {
      void client.invalidateQueries({ queryKey: ['admin'] })
    },
  })

  const addButton = (
    <Button type="button" onClick={() => setEditing('new')}>
      <Plus size={17} />
      Добавить пользователя
    </Button>
  )

  return (
    <section>
      <PageHeading title="Пользователи" action={addButton} />
      {editing && (
        <UserForm
          key={editing === 'new' ? 'new' : editing.id}
          user={editing === 'new' ? undefined : editing}
          onDone={() => setEditing(null)}
        />
      )}
      <SearchField
        label="Поиск пользователей"
        placeholder="Email, имя пользователя или имя"
        value={search}
        onChange={(value) => {
          setSearch(value)
          setOffset(0)
        }}
        className="relative mb-6 block"
      />

      {users.isPending ? (
        <Loading />
      ) : users.error ? (
        <ErrorState error={users.error} retry={() => users.refetch()} />
      ) : (
        <>
          <div className="divide-y divide-line border-y border-line">
            {users.data?.items.map((user) => (
              <UserRow
                key={user.id}
                user={user}
                isSelf={user.id === current.data?.id}
                deleting={remove.isPending}
                onEdit={() => setEditing(user)}
                onDelete={() => remove.mutate(user.id)}
              />
            ))}
            {!users.data?.items.length && (
              <p className="py-12 text-center text-sm text-muted">Пользователи не найдены.</p>
            )}
          </div>
          <Pagination total={users.data?.total ?? 0} offset={offset} limit={limit} onChange={setOffset} />
        </>
      )}
      <FormError error={remove.error} />
    </section>
  )
}
