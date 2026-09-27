import { useQuery } from '@tanstack/react-query'
import { favoriteApi } from '../../../entities/favorite'
import { userApi } from '../../../entities/user'
import { ProductGrid } from '../../../widgets/product-grid'
import { EmptyState, ErrorState, Loading } from '../../../shared/ui/States'

export function FavoritesPage() {
  const session = useQuery({ queryKey: ['user'], queryFn: userApi.session, retry: false })
  const { data, error, isPending, refetch } = useQuery({ queryKey: ['favorites'], queryFn: favoriteApi.read, enabled: !session.isPending })
  return <div className="page-container pt-9"><h1 className="display-title">Избранное</h1><p className="mt-4 text-sm text-muted">Вещи, к которым хочется вернуться.</p><div className="mt-10">{isPending ? <Loading /> : error ? <ErrorState error={error} retry={() => refetch()} /> : data?.items.length ? <ProductGrid products={data.items} /> : <EmptyState title="Здесь пока пусто" body="Сохраняйте понравившиеся вещи нажатием на сердечко." />}</div></div>
}
