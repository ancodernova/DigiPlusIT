'use client'

import { useEffect, useState } from 'react'
import { AppShell, PageHeading, PendingCard } from '@/components/contextflow-app'
import { apiRequest } from '@/lib/api'

type User = { full_name: string }
type Meeting = { _id: string; title: string; meeting_date?: string; status?: string }
type Overview = {
  total_meetings: number
  open_tasks: number
  completed_tasks: number
  blocked_tasks: number
  recent_meetings: Meeting[]
}

export default function AppPage() {
  const [user, setUser] = useState<User | null>(null)
  const [overview, setOverview] = useState<Overview | null>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    Promise.all([
      apiRequest<User>('/api/v1/auth/me'),
      apiRequest<Overview>('/api/v1/dashboard/overview'),
    ]).then(([currentUser, currentOverview]) => {
      setUser(currentUser)
      setOverview(currentOverview)
    }).catch(cause => setError(cause instanceof Error ? cause.message : 'Unable to load your workspace.'))
  }, [])

  const firstName = user?.full_name?.trim().split(/\s+/)[0] || 'there'
  const metrics = overview ? [
    ['Meetings', overview.total_meetings, 'in this workspace'],
    ['Open tasks', overview.open_tasks, 'need a next move'],
    ['Completed tasks', overview.completed_tasks, 'completed'],
    ['Blocked tasks', overview.blocked_tasks, 'need attention'],
  ] : []

  return <AppShell><div className="dashboard-content"><PageHeading eyebrow="Workspace overview" title={`Good morning, ${firstName}.`} description="A connected view of meetings, decisions, and work continuity." action={<a href="/app/meetings/new" className="button-primary px-4 py-3 text-xs">＋ New meeting</a>}/>{error && <p role="alert" className="mt-6 text-sm text-rose-300">{error}</p>}<div className="mt-8 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">{metrics.map(([label, value, detail]) => <div className="metric-card" key={label as string}><p>{label}</p><strong>{value}</strong><span>{detail}</span></div>)}</div><div className="mt-6 grid gap-6 lg:grid-cols-[1.25fr_.75fr]"><div className="panel"><div className="panel-heading"><div><p className="eyebrow">Recent meetings</p><h2>Keep the thread moving.</h2></div><a href="/app/meetings" className="text-xs text-cyan">View all</a></div>{overview?.recent_meetings.map((meeting, index) => <a href={`/app/meetings/${meeting._id}`} className="list-row" key={meeting._id}><div className="list-icon bg-cyan/10 text-cyan">{index + 1}</div><div className="min-w-0 flex-1"><p>{meeting.title}</p><span>{meeting.meeting_date ? new Date(meeting.meeting_date).toLocaleString() : 'No date'}</span></div><span className="status-chip">{meeting.status || 'Recorded'}</span></a>)}</div><div className="panel"><div className="panel-heading"><div><p className="eyebrow">Risk overview</p><h2>Where context is thin.</h2></div></div><div className="risk-ring"><strong>{overview ? `${Math.max(0, 100 - overview.blocked_tasks * 5)}%` : '—'}</strong><span>context health</span></div><p className="mt-5 text-sm leading-6 text-slate-500">{overview?.blocked_tasks ?? 0} blocked tasks need a clear next owner.</p><a href="/app/tasks" className="button-ghost mt-5 w-full px-4 py-3 text-xs">Review attention items</a></div></div><div className="mt-6"><PendingCard/></div></div></AppShell>
}
