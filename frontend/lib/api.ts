export type ApiState = 'connected' | 'pending'

export const apiState: ApiState = process.env.NEXT_PUBLIC_API_URL ? 'connected' : 'pending'

export async function apiRequest<T>(path: string, init?: RequestInit): Promise<T> {
  if (!path.startsWith('/api/v1/')) throw new Error('API paths must use the /api/v1/ prefix.')
  const response = await fetch(`/api/backend?path=${encodeURIComponent(path)}`, {
    ...init,
    headers: { 'Content-Type': 'application/json', ...(init?.headers || {}) },
  })
  if (!response.ok) {
    const payload = await response.json().catch(() => ({}))
    throw new Error(payload.detail ?? `API request failed (${response.status})`)
  }
  return response.json() as Promise<T>
}
