import { Heart } from 'lucide-react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { favoriteApi } from '../../../entities/favorite'
import { userApi } from '../../../entities/user'

export function FavoriteButton({ productId, className = '' }: { productId: string; className?: string }) {
  const client = useQueryClient()
  const session = useQuery({ queryKey: ['user'], queryFn: userApi.session, retry: false })
  const { data } = useQuery({ queryKey: ['favorites'], queryFn: favoriteApi.read, enabled: !session.isPending })
  const active = data?.items.some((item) => item.id === productId) ?? false
  const mutation = useMutation({
    mutationFn: () => active ? favoriteApi.remove(productId) : favoriteApi.add(productId),
    onSuccess: (value) => client.setQueryData(['favorites'], value),
  })
  return <button type="button" onClick={() => mutation.mutate()} disabled={session.isPending || mutation.isPending} aria-label={active ? 'Убрать из избранного' : 'Добавить в избранное'} aria-pressed={active} title={mutation.error instanceof Error ? mutation.error.message : undefined} className={`flex h-9 w-9 items-center justify-center bg-white/95 text-ink shadow-sm transition-[transform,box-shadow] hover:-translate-y-0.5 hover:shadow-tactile focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ink ${className}`}><Heart size={19} strokeWidth={1.65} fill={active ? 'currentColor' : 'none'} /></button>
}
