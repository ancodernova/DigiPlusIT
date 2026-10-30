'use client'

import { use, useEffect, useState } from 'react'
import { AppShell, PageHeading } from '@/components/contextflow-app'
import { apiRequest } from '@/lib/api'

type Session = { _id: string; status: string; provider: string; meeting_url?: string; created_at?: string; ended_at?: string }
type Meeting = { title: string }

export default function LiveMeetingPage({ params }: { params: Promise<{ meetingId: string }> }) {
  const { meetingId } = use(params)
  const [meeting, setMeeting] = useState<Meeting | null>(null)
  const [session, setSession] = useState<Session | null>(null)
  const [analysis, setAnalysis] = useState<Record<string, unknown> | null>(null)
  const [error, setError] = useState('')
  useEffect(() => {
    let active = true
    async function load() {
      try {
        const [currentMeeting, sessions] = await Promise.all([
          apiRequest<Meeting>(`/api/v1/meetings/${meetingId}`),
          apiRequest<Session[]>(`/api/v1/meetings/${meetingId}/live-sessions`),
        ])
        if (!active) return
        setMeeting(currentMeeting); setSession(sessions[0] ?? null)
        try { setAnalysis(await apiRequest<Record<string, unknown>>(`/api/v1/meetings/${meetingId}/analysis`)) } catch { setAnalysis(null) }
      } catch (cause) { if (active) setError(cause instanceof Error ? cause.message : 'Unable to load live session.') }
    }
    void load()
    const timer = window.setInterval(load, 3000)
    return () => { active = false; window.clearInterval(timer) }
  }, [meetingId])
  async function stop() {
    if (!session) return
    try { setSession(await apiRequest<Session>(`/api/v1/meetings/${meetingId}/live-sessions/${session._id}/stop`, { method: 'POST' })) }
    catch (cause) { setError(cause instanceof Error ? cause.message : 'Unable to stop session.') }
  }
  return <AppShell active="Meetings"><div className="dashboard-content"><PageHeading eyebrow="Live meeting room" title={meeting?.title ?? 'Loading meeting…'} description={session ? `Session ${session._id} · ${session.provider} provider · ${session.status}.` : 'No live session has been started for this meeting.'} action={session && session.status !== 'stopped' ? <button onClick={stop} className="button-ghost px-4 py-3 text-xs">Stop capture</button> : undefined}/>{error && <p role="alert" className="mt-4 text-sm text-rose-300">{error}</p>}<div className="mt-8 grid gap-6 lg:grid-cols-[1.2fr_.8fr]"><div className="panel min-h-[430px]"><div className="panel-heading"><div><p className="eyebrow">Transcript</p><h2>{session?.status === 'stopped' ? 'Session stopped' : 'Waiting for transcript'}</h2></div><span className="status-chip">{session?.status ?? 'Not started'}</span></div><div className="flex min-h-[300px] items-center justify-center text-center text-sm text-slate-500">{session ? 'The mock provider records lifecycle state only. Paste or upload a transcript to generate searchable content and embeddings.' : 'Start a live session from the meeting capture page.'}</div></div><div className="panel"><p className="eyebrow">AI insights</p>{analysis ? <div className="mt-6 space-y-4">{['executive_summary', 'decisions', 'action_items', 'risks'].map(key => <div key={key}><p className="text-sm font-medium capitalize text-white">{key.replace('_', ' ')}</p><p className="mt-1 whitespace-pre-wrap text-sm text-slate-500">{typeof analysis[key] === 'string' ? analysis[key] as string : JSON.stringify(analysis[key] ?? 'No data')}</p></div>)}</div> : <p className="mt-6 text-sm leading-6 text-slate-500">Insights appear after a processed transcript is analyzed.</p>}</div></div></div></AppShell>
}
