import { Shirt } from 'lucide-react'
import { formalityLabels } from '../../../entities/wardrobe'
import type { WardrobeItem } from '../../../entities/wardrobe'

type Props = { item: WardrobeItem; categoryName?: string; onOpen: () => void }

export function WardrobeItemCard({ item, categoryName, onOpen }: Props) {
  const details = [categoryName, item.formality && formalityLabels[item.formality], item.color].filter(
    Boolean,
  )
  return (
    <button
      type="button"
      onClick={onOpen}
      className="group text-left focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ink"
    >
      <div className="aspect-[4/5] overflow-hidden bg-mist">
        {item.image_url ? (
          <img
            src={item.image_url}
            alt={item.name}
            loading="lazy"
            className="h-full w-full object-cover transition-transform duration-300 group-hover:scale-[1.03]"
          />
        ) : (
          <div className="flex h-full items-center justify-center text-muted">
            <Shirt size={40} strokeWidth={1.2} />
          </div>
        )}
      </div>
      <p className="mt-3 truncate text-sm font-medium">{item.name}</p>
      <p className="mt-1 truncate text-xs text-muted">{details.join(' · ') || 'Без описания'}</p>
    </button>
  )
}
