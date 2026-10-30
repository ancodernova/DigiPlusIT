import { NextResponse } from 'next/server'
import { getBackendUrl } from '@/lib/backend-url'

function findToken(value: unknown): string | null {
  if (!value || typeof value !== 'object') return null
  if (Array.isArray(value)) {
    for (const item of value) {
      const token = findToken(item)
      if (token) return token
    }
    return null
  }
  for (const [key, nested] of Object.entries(value)) {
    if (typeof nested === 'string' && /token/i.test(key) && nested.length > 20) return nested
    const token = findToken(nested)
    if (token) return token
  }
  return null
}

export async function POST(request: Request) {
  const apiUrl = getBackendUrl()

  const body = await request.json()
  const response = await fetch(`${apiUrl}/api/v1/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
    cache: 'no-store',
  })
  const payload = await response.json().catch(() => ({}))
  if (!response.ok) return NextResponse.json(payload, { status: response.status })

  const token = findToken(payload)
  if (!token) return NextResponse.json({ detail: 'Login succeeded but no access token was returned by the backend.' }, { status: 502 })

  const result = NextResponse.json({ user: payload.user ?? payload.data?.user ?? null })
  result.cookies.set('contextflow_access_token', token, {
    httpOnly: true,
    secure: process.env.NODE_ENV === 'production',
    sameSite: 'lax',
    path: '/',
    maxAge: 60 * 60 * 8,
  })
  return result
}
