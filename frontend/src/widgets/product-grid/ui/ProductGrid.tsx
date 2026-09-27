import type { Product } from '../../../entities/product'
import { ProductCard } from '../../../entities/product'
import { FavoriteButton } from '../../../features/favorite-toggle'

export function ProductGrid({ products }: { products: Product[] }) {
  return <div className="grid grid-cols-2 gap-x-3 gap-y-9 sm:gap-x-5 lg:grid-cols-4 lg:gap-x-6">{products.map((product) => <ProductCard key={product.id} product={product} favorite={<FavoriteButton productId={product.id} />} />)}</div>
}
