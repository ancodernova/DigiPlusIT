'use client'

import { useEffect, useState } from 'react'
import { AppShell, PageHeading } from '@/components/contextflow-app'
import { apiRequest } from '@/lib/api'

type Overview = {
  total_meetings: number
  open_tasks: number
  completed_tasks: number
  blocked_tasks: number
  recent_meetings: { _id: string; title: string; meeting_date: string; status: string }[]
}

export default function AppPage() {
  const [overview, setOverview] = useState<Overview | null>(null)
  const [error, setError] = useState('')
  useEffect(() => {
    apiRequest<Overview>('/api/v1/dashboard/overview')
      .then(setOverview)
      .catch(cause => setError(cause instanceof Error ? cause.message : 'Unable to load dashboard.'))
  }, [])
  const metrics = overview ? [
    ['Meetings', overview.total_meetings, 'in this workspace'],
    ['Open tasks', overview.open_tasks, 'need a next move'],
    ['Completed tasks', overview.completed_tasks, 'completed'],
    ['Blocked tasks', overview.blocked_tasks, 'need attention'],
  ] : []
  return <AppShell><div className="dashboard-content"><PageHeading eyebrow="Workspace overview" title="Good morning." description="A live view of meetings, decisions, and work continuity." action={<a href="/app/meetings/new" className="button-primary px-4 py-3 text-xs">＋ New meeting</a>}/>{error && <p role="alert" className="mt-6 text-sm text-rose-300">{error}</p>}<div className="mt-8 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">{metrics.map(([label, value, detail]) => <div className="metric-card" key={label as string}><p>{label}</p><strong>{value}</strong><span>{detail}</span></div>)}</div><div className="panel mt-6"><div className="panel-heading"><div><p className="eyebrow">Recent meetings</p><h2>Keep the thread moving.</h2></div><a href="/app/meetings" className="text-xs text-cyan">View all</a></div>{overview?.recent_meetings.map(meeting => <a href={`/app/meetings/${meeting._id}`} className="list-row" key={meeting._id}><div className="list-icon bg-cyan/10 text-cyan">•</div><div className="min-w-0 flex-1"><p>{meeting.title}</p><span>{new Date(meeting.meeting_date).toLocaleString()}</span></div><span className="status-chip">{meeting.status}</span></a>)}</div></div></AppShell>
}
