'use client'

import { useEffect, useState } from 'react'
import { AppShell, PageHeading } from '@/components/contextflow-app'
import { apiRequest } from '@/lib/api'

type Activity = { _id: string; action?: string; action_type?: string; entity_type?: string; created_at?: string; metadata?: Record<string, unknown> }
export default function ActivityPage() {
  const [items, setItems] = useState<Activity[]>([])
  const [error, setError] = useState('')
  useEffect(() => { apiRequest<Activity[]>('/api/v1/activity/').then(setItems).catch(cause => setError(cause instanceof Error ? cause.message : 'Unable to load activity.')) }, [])
  return <AppShell active="Activity"><div className="dashboard-content"><PageHeading eyebrow="Audit trail" title="Activity" description="A live history of actions and changes across the active workspace." />{error && <p role="alert" className="mt-6 text-sm text-rose-300">{error}</p>}<div className="panel mt-8">{items.map((item, index) => <div className="list-row" key={item._id}><div className="list-icon bg-violet/10 text-violet">{index + 1}</div><div className="flex-1"><p>{(item.action ?? item.action_type ?? 'Workspace action').replaceAll('_', ' ')}</p><span>{item.created_at ? new Date(item.created_at).toLocaleString() : 'Recently'} · {item.entity_type ?? 'workspace'}</span></div></div>)}{!items.length && !error && <p className="p-6 text-sm text-slate-500">No activity has been recorded yet.</p>}</div></div></AppShell>
}
