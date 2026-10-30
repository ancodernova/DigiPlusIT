'use client'

import Link from 'next/link'
import { FormEvent, useEffect, useState } from 'react'
import { AppShell, PageHeading } from '@/components/contextflow-app'
import { apiRequest } from '@/lib/api'

type Passport = { _id: string; title: string; created_at?: string; content?: { important_decisions?: unknown[]; open_tasks?: unknown[]; source_meetings?: unknown[] } }

export default function PassportsPage() {
  const [passports, setPassports] = useState<Passport[]>([])
  const [title, setTitle] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  async function load() { try { setPassports(await apiRequest<Passport[]>('/api/v1/context-passports/')) } catch (cause) { setError(cause instanceof Error ? cause.message : 'Unable to load passports.') } }
  useEffect(() => { void load() }, [])
  async function generate(event: FormEvent) {
    event.preventDefault(); if (!title.trim()) return
    setBusy(true); setError('')
    try { const passport = await apiRequest<Passport>('/api/v1/context-passports/generate', { method: 'POST', body: JSON.stringify({ title, meeting_ids: [] }) }); setPassports(items => [passport, ...items]); setTitle('') }
    catch (cause) { setError(cause instanceof Error ? cause.message : 'Unable to generate passport.') }
    finally { setBusy(false) }
  }
  return <AppShell active="Passports"><div className="dashboard-content"><PageHeading eyebrow="Handover intelligence" title="Context Passports" description="Source-linked handovers built from your active workspace."/><form onSubmit={generate} className="panel mt-8 flex gap-3"><input required minLength={1} value={title} onChange={event => setTitle(event.target.value)} className="search-box flex-1 px-4" placeholder="Passport title" /><button disabled={busy} className="button-primary px-4 py-2 text-xs">{busy ? 'Generating…' : 'Generate passport'}</button></form>{error && <p role="alert" className="mt-4 text-sm text-rose-300">{error}</p>}<div className="mt-6 grid gap-4 md:grid-cols-2">{passports.map(passport => <div className="panel" key={passport._id}><p className="eyebrow">Context Passport</p><h2 className="mt-3">{passport.title}</h2><p className="mt-2 text-sm text-slate-500">{passport.content?.important_decisions?.length ?? 0} decisions · {passport.content?.open_tasks?.length ?? 0} open tasks · {passport.content?.source_meetings?.length ?? 0} source meetings</p><div className="mt-6 flex items-center justify-between text-xs text-slate-500"><span>{passport.created_at ? new Date(passport.created_at).toLocaleDateString() : ''}</span><Link href={`/app/context-passports/${passport._id}`} className="text-cyan">Open passport</Link></div></div>)}</div>{!passports.length && !error && <div className="panel mt-6 text-sm text-slate-500">No passports have been generated in this workspace.</div>}</div></AppShell>
}
