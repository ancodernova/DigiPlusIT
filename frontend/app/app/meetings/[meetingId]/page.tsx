'use client'

import Link from 'next/link'
import { useEffect, useState } from 'react'
import { AppShell, PageHeading } from '@/components/contextflow-app'
import { apiRequest } from '@/lib/api'

type Meeting = { _id: string; title: string; meeting_date?: string; status?: string; meeting_type?: string }
type Transcript = { _id: string; title?: string; status?: string; original_text?: string; analysis?: Record<string, unknown> }
type Decision = { _id: string; title: string; description?: string }

export default function MeetingDetailPage({ params }: { params: Promise<{ meetingId: string }> }) {
  const [meetingId, setMeetingId] = useState('')
  const [meeting, setMeeting] = useState<Meeting | null>(null)
  const [transcripts, setTranscripts] = useState<Transcript[]>([])
  const [decisions, setDecisions] = useState<Decision[]>([])
  const [analysis, setAnalysis] = useState<Record<string, unknown> | null>(null)
  const [error, setError] = useState('')
  const [analyzing, setAnalyzing] = useState(false)
  useEffect(() => {
    let active = true
    params.then(async ({ meetingId: id }) => {
      setMeetingId(id)
      try {
        const [item, transcriptItems, decisionItems] = await Promise.all([
          apiRequest<Meeting>(`/api/v1/meetings/${id}`),
          apiRequest<Transcript[]>(`/api/v1/meetings/${id}/transcripts`),
          apiRequest<Decision[]>(`/api/v1/meetings/${id}/decisions`),
        ])
        if (!active) return
        setMeeting(item)
        setTranscripts(transcriptItems)
        setDecisions(decisionItems)
        const analyzed = transcriptItems.find(transcript => transcript.analysis)
        if (analyzed?.analysis) {
          setAnalysis(analyzed.analysis)
          return
        }
        const transcript = transcriptItems.find(item => item.original_text?.trim())
        if (!transcript) return
        setAnalyzing(true)
        const generated = await apiRequest<Record<string, unknown>>(`/api/v1/meetings/${id}/transcripts/${transcript._id}/analyze`, { method: 'POST' })
        if (active) setAnalysis(generated)
      } catch (cause) {
        if (active) setError(cause instanceof Error ? cause.message : 'Unable to load or analyze meeting.')
      } finally {
        if (active) setAnalyzing(false)
      }
    })
    return () => { active = false }
  }, [params])
  const summary = analysis?.executive_summary ?? analysis?.detailed_summary
  return <AppShell active="Meetings"><div className="dashboard-content"><PageHeading eyebrow="Meeting detail" title={meeting?.title ?? 'Meeting'} description={meeting ? `${meeting.status ?? 'scheduled'} · ${meeting.meeting_date ? new Date(meeting.meeting_date).toLocaleString() : 'Date not set'}` : 'Loading meeting details.'} action={meetingId ? <Link href={`/app/meetings/${meetingId}/live`} className="button-primary px-4 py-3 text-xs">Open live room</Link> : undefined} />
    {error && <p role="alert" className="mt-6 text-sm text-rose-300">{error}</p>}
    <div className="mt-8 grid gap-6 lg:grid-cols-[1.1fr_.9fr]"><div className="panel"><p className="eyebrow">Executive summary</p><h2 className="mt-3 text-xl text-white">{analyzing ? 'Generating analysis…' : String(summary ?? 'Analysis is not available yet.')}</h2><p className="mt-3 text-sm leading-7 text-slate-500">{analysis ? 'Generated from the meeting transcript.' : analyzing ? 'The transcript is being analyzed by the configured AI provider.' : transcripts.length ? 'Analysis could not be generated. Check the AI provider configuration and try again.' : 'Submit a transcript from New meeting to generate analysis.'}</p></div><div className="panel"><p className="eyebrow">Source trail</p>{transcripts.map(item => <div className="list-row px-0" key={item._id}><div className="flex-1"><p>{item.title ?? 'Transcript'}</p><span>{item.status ?? 'received'}</span></div></div>)}{!transcripts.length && <p className="mt-4 text-sm text-slate-500">No transcripts attached.</p>}</div></div>
    <div className="panel mt-6"><p className="eyebrow">Decisions</p>{decisions.map(item => <div className="list-row px-0" key={item._id}><div><p>{item.title}</p><span>{item.description ?? 'No description'}</span></div></div>)}{!decisions.length && <p className="mt-4 text-sm text-slate-500">No decisions recorded.</p>}</div>
  </div></AppShell>
}
