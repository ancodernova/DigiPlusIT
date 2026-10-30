'use client'

import Link from 'next/link'
import { useEffect, useMemo, useState } from 'react'
import { AppShell, PageHeading } from '@/components/contextflow-app'
import { apiRequest } from '@/lib/api'

type Meeting = { _id: string; title: string; meeting_date?: string; status?: string; meeting_type?: string; participants?: string[] }

export default function MeetingsPage() {
  const [meetings, setMeetings] = useState<Meeting[]>([])
  const [search, setSearch] = useState('')
  const [status, setStatus] = useState('')
  const [error, setError] = useState('')

  useEffect(() => {
    const query = new URLSearchParams({ limit: '100' })
    if (search.trim()) query.set('search', search.trim())
    if (status) query.set('status', status)
    apiRequest<Meeting[]>(`/api/v1/meetings/?${query.toString()}`)
      .then(setMeetings)
      .catch(cause => setError(cause instanceof Error ? cause.message : 'Unable to load meetings.'))
  }, [search, status])

  const statuses = useMemo(() => Array.from(new Set(meetings.map(item => item.status).filter(Boolean))), [meetings])
  return <AppShell active="Meetings"><div className="dashboard-content"><PageHeading eyebrow="Meeting intelligence" title="Meetings" description="Capture conversation, preserve decisions, and keep every handover grounded." action={<Link href="/app/meetings/new" className="button-primary px-4 py-3 text-xs">＋ New meeting</Link>} />
    <div className="mt-8 flex flex-wrap gap-3"><input className="search-box h-11 min-w-[260px] px-3" value={search} onChange={event => setSearch(event.target.value)} placeholder="Search meetings..." /><select className="button-ghost px-4 py-2 text-xs" value={status} onChange={event => setStatus(event.target.value)}><option value="">All statuses</option>{statuses.map(item => <option key={item} value={item}>{item}</option>)}</select></div>
    {error && <p role="alert" className="mt-6 text-sm text-rose-300">{error}</p>}
    <div className="panel mt-6 overflow-hidden"><div className="grid grid-cols-[1.5fr_.8fr_.8fr_.7fr] gap-4 border-b border-white/5 px-5 py-3 text-[10px] uppercase tracking-[.14em] text-slate-600"><span>Meeting</span><span>Participants</span><span>Status</span><span>Source</span></div>
      {meetings.map(item => <Link href={`/app/meetings/${item._id}`} className="list-row grid-cols-[1.5fr_.8fr_.8fr_.7fr]" key={item._id}><div className="min-w-0"><p>{item.title}</p><span>{item.meeting_date ? new Date(item.meeting_date).toLocaleString() : 'Date not set'}</span></div><span className="text-xs text-slate-400">{item.participants?.length ?? 0} people</span><span className="status-chip">{item.status ?? 'scheduled'}</span><span className="text-xs text-slate-500">{item.meeting_type ?? 'Meeting'}</span></Link>)}
      {!meetings.length && !error && <p className="p-6 text-sm text-slate-500">No meetings found in this workspace.</p>}
    </div>
  </div></AppShell>
}
