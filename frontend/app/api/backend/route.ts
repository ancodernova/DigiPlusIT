import { NextResponse } from 'next/server'
import { cookies } from 'next/headers'
import { getBackendUrl } from '@/lib/backend-url'

export async function GET(request: Request) {
  return forward(request, 'GET')
}
export async function POST(request: Request) {
  return forward(request, 'POST')
}
export async function PUT(request: Request) {
  return forward(request, 'PUT')
}
export async function PATCH(request: Request) {
  return forward(request, 'PATCH')
}
export async function DELETE(request: Request) {
  return forward(request, 'DELETE')
}

async function forward(request: Request, method: string) {
  const apiUrl = getBackendUrl()
  const path = new URL(request.url).searchParams.get('path')
  if (!path || !path.startsWith('/api/v1/')) return NextResponse.json({ detail: 'A valid /api/v1/ path is required.' }, { status: 400 })
  const token = (await cookies()).get('contextflow_access_token')?.value
  const headers = new Headers(request.headers)
  headers.delete('host')
  if (token) headers.set('Authorization', `Bearer ${token}`)
  const body = method === 'GET' || method === 'DELETE' ? undefined : await request.text()
  const response = await fetch(`${apiUrl}${path}`, { method, headers, body, cache: 'no-store' })
  return new NextResponse(response.body, { status: response.status, headers: { 'Content-Type': response.headers.get('content-type') ?? 'application/json' } })
}
