import { NextResponse } from 'next/server'
import { getBackendUrl } from '@/lib/backend-url'

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

function findWorkspaceId(value: unknown): string | null {
  if (!value || typeof value !== 'object' || Array.isArray(value)) return null
  const workspace = (value as { workspace?: { _id?: unknown; id?: unknown } }).workspace
  if (!workspace || typeof workspace !== 'object') return null
  const id = workspace._id ?? workspace.id
  return typeof id === 'string' ? id : null
}

export async function POST(request: Request) {
  let apiUrl: string
  try {
    apiUrl = getBackendUrl()
  } catch (error) {
    return NextResponse.json({ detail: error instanceof Error ? error.message : 'Backend URL is not configured.' }, { status: 503 })
  }
  let response: Response
  try {
    response = await fetch(`${apiUrl}/api/v1/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: await request.text(),
      cache: 'no-store',
    })
  } catch {
    return NextResponse.json({ detail: 'The backend could not be reached.' }, { status: 502 })
  }
  const payload = await response.json().catch(() => ({}))
  if (!response.ok) return NextResponse.json(payload, { status: response.status })
  const token = findToken(payload)
  if (!token) return NextResponse.json({ detail: 'Registration succeeded but no access token was returned by the backend.' }, { status: 502 })
  const workspaceId = findWorkspaceId(payload)
  const result = NextResponse.json({ user: payload.user ?? null, workspace: payload.workspace ?? null })
  result.cookies.set('contextflow_access_token', token, {
    httpOnly: true,
    secure: process.env.NODE_ENV === 'production',
    sameSite: 'lax',
    path: '/',
    maxAge: 60 * 60 * 8,
  })
  if (workspaceId) {
    result.cookies.set('contextflow_workspace_id', workspaceId, {
      httpOnly: true,
      secure: process.env.NODE_ENV === 'production',
      sameSite: 'lax',
      path: '/',
      maxAge: 60 * 60 * 8,
    })
  }
  return result
}
