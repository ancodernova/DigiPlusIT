'use client'

import { useEffect, useState } from 'react'
import { AppShell, PageHeading } from '@/components/contextflow-app'
import { apiRequest } from '@/lib/api'

export default function IntegrationSettingsPage() {
  const [status, setStatus] = useState<Record<string, unknown> | null>(null)
  const [error, setError] = useState('')
  useEffect(() => { apiRequest<Record<string, unknown>>('/api/v1/pinecone/status').then(setStatus).catch(cause => setError(cause instanceof Error ? cause.message : 'Provider status is unavailable.')) }, [])
  return <AppShell active="Settings"><div className="dashboard-content max-w-5xl"><PageHeading eyebrow="Settings / Integrations" title="Integrations" description="Review the configured intelligence services for this workspace." /><div className="mt-8 grid gap-4 md:grid-cols-2"><div className="panel"><p className="eyebrow">FastAPI proxy</p><h2 className="mt-3 text-white">Connected</h2><p className="mt-2 text-sm text-slate-500">Authenticated requests use the server-only NEXT_API_URL configuration.</p></div><div className="panel"><p className="eyebrow">Pinecone index</p><h2 className="mt-3 text-white">{status ? String(status.status ?? status.ready ?? 'Available') : error ? 'Unavailable' : 'Checking…'}</h2><p className="mt-2 text-sm text-slate-500">{error || (status ? 'Semantic workspace search is configured.' : 'Checking the protected provider diagnostic.')}</p></div></div></div></AppShell>
}
