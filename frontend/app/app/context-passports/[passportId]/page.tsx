'use client'

import { use, useEffect, useState } from 'react'
import { AppShell, PageHeading } from '@/components/contextflow-app'
import { apiRequest } from '@/lib/api'

type Passport = { _id: string; title: string; content: Record<string, unknown> }
export default function PassportDetailPage({ params }: { params: Promise<{ passportId: string }> }) {
  const { passportId } = use(params)
  const [passport, setPassport] = useState<Passport | null>(null)
  const [error, setError] = useState('')
  useEffect(() => { apiRequest<Passport>(`/api/v1/context-passports/${passportId}`).then(setPassport).catch(cause => setError(cause instanceof Error ? cause.message : 'Unable to load passport.')) }, [passportId])
  async function download() {
    try {
      const response = await fetch(`/api/backend?path=${encodeURIComponent(`/api/v1/context-passports/${passportId}/markdown`)}`)
      if (!response.ok) throw new Error('Markdown export failed.')
      const blob = await response.blob(); const url = URL.createObjectURL(blob); const link = document.createElement('a'); link.href = url; link.download = `${passport?.title ?? 'context-passport'}.md`; link.click(); URL.revokeObjectURL(url)
    } catch (cause) { setError(cause instanceof Error ? cause.message : 'Markdown export failed.') }
  }
  return <AppShell active="Passports"><div className="dashboard-content max-w-5xl">{error && <p role="alert" className="text-sm text-rose-300">{error}</p>}{passport && <><PageHeading eyebrow="Context Passport" title={passport.title} description="Source-linked handover brief for the active workspace." action={<button onClick={download} className="button-ghost px-4 py-3 text-xs">Download Markdown</button>}/><div className="panel mt-8"><pre className="whitespace-pre-wrap text-sm leading-7 text-slate-300">{JSON.stringify(passport.content, null, 2)}</pre></div></>}</div></AppShell>
}
