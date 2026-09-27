import type { OrderStatus } from './types'

export const orderStatusLabels: Record<OrderStatus, string> = {
  placed: 'Оформлен',
  processing: 'В обработке',
  shipped: 'Отправлен',
  delivered: 'Доставлен',
  cancelled: 'Отменён',
}
