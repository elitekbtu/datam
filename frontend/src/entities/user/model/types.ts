export interface User { id: string; email: string; username: string; full_name: string | null; role: 'user' | 'admin'; is_active: boolean; updated_at: string }
