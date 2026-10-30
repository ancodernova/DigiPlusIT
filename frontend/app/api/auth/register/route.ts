import { NextResponse } from 'next/server'

function findToken(value: unknown): string | null {
  if (!value || typeof value !== 'object') return null
  if (Array.isArray(value)) return value.map(findToken).find(Boolean) ?? null
  for (const [key, nested] of Object.entries(value)) {
    if (typeof nested === 'string' && /token/i.test(key) && nested.length > 20) return nested
    const token = findToken(nested)
    if (token) return token
  }
  return null
}

export async function POST(request: Request) {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL
  if (!apiUrl) return NextResponse.json({ detail: 'NEXT_PUBLIC_API_URL is not configured.' }, { status: 503 })
  const response = await fetch(`${apiUrl}/api/v1/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: await request.text(),
    cache: 'no-store',
  })
  const payload = await response.json().catch(() => ({}))
  if (!response.ok) return NextResponse.json(payload, { status: response.status })
  const token = findToken(payload)
  if (!token) return NextResponse.json({ detail: 'Registration succeeded but no access token was returned by the backend.' }, { status: 502 })
  const result = NextResponse.json({ user: payload.user ?? null, workspace: payload.workspace ?? null })
  result.cookies.set('contextflow_access_token', token, {
    httpOnly: true,
    secure: process.env.NODE_ENV === 'production',
    sameSite: 'lax',
    path: '/',
    maxAge: 60 * 60 * 8,
  })
  return result
}
