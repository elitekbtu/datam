import { api } from '../../../shared/api/client'
import type { Outfit, OutfitRequest } from '../model/types'

export const stylistApi = {
  outfit: (payload: OutfitRequest, signal: AbortSignal) =>
    api<Outfit>('/stylist/outfit', { method: 'POST', body: payload, signal })
}
