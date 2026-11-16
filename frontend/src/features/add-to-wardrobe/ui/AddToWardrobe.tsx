import { Link } from 'react-router-dom'
import { Shirt } from 'lucide-react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { userApi } from '../../../entities/user'
import { wardrobeApi } from '../../../entities/wardrobe'
import { Button } from '../../../shared/ui/Button'

export function AddToWardrobe({ productId }: { productId: string }) {
  const client = useQueryClient()
  const session = useQuery({ queryKey: ['user'], queryFn: userApi.session, retry: false })
  const mutation = useMutation({
    mutationFn: () => wardrobeApi.fromProduct(productId),
    onSuccess: () => client.invalidateQueries({ queryKey: ['wardrobe'] }),
  })
  if (!session.data) return null
  return (
    <div className="mt-2">
      {mutation.isSuccess ? (
        <p
          role="status"
          className="flex min-h-12 items-center justify-center gap-2 border border-line text-sm"
        >
          <Shirt size={17} /> В вашем гардеробе ·
          <Link to="/account/wardrobe" className="underline underline-offset-4">
            Открыть
          </Link>
        </p>
      ) : (
        <Button variant="outline" full onClick={() => mutation.mutate()} disabled={mutation.isPending}>
          <Shirt size={17} />
          {mutation.isPending ? 'Добавляем...' : 'У меня уже есть — в гардероб'}
        </Button>
      )}
      {mutation.isError && (
        <p role="alert" className="mt-3 text-sm text-red-700">
          {mutation.error.message}
        </p>
      )}
    </div>
  )
}
