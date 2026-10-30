'use client'

import { FormEvent, useRef, useState } from 'react'
import { useRouter } from 'next/navigation'
import { AppShell, PageHeading } from '@/components/contextflow-app'
import { apiRequest } from '@/lib/api'

const methods = ['Paste transcript', 'Upload file', 'Live meeting'] as const
type Meeting = { _id: string }
type Transcript = { _id?: string; job_id?: string; status?: string }
type LiveSession = { _id: string; status: string }

export default function NewMeetingPage() {
  const router = useRouter()
  const fileRef = useRef<HTMLInputElement>(null)
  const [method, setMethod] = useState<(typeof methods)[number]>('Paste transcript')
  const [title, setTitle] = useState('')
  const [meetingDate, setMeetingDate] = useState(new Date().toISOString().slice(0, 10))
  const [transcript, setTranscript] = useState('')
  const [file, setFile] = useState<File | null>(null)
  const [consent, setConsent] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [meetingUrl, setMeetingUrl] = useState('https://localhost/mock-meeting')
  const [liveSession, setLiveSession] = useState<LiveSession | null>(null)
  const [liveMeetingId, setLiveMeetingId] = useState('')

  async function submit(event: FormEvent) {
    event.preventDefault()
    if (!consent) return setError('Confirm consent before processing this meeting.')
    if (!title.trim()) return setError('Enter a meeting title.')
    if (method === 'Paste transcript' && !transcript.trim()) return setError('Paste a transcript before saving.')
    if (method === 'Upload file' && !file) return setError('Choose a transcript file before uploading.')
    if (method === 'Live meeting' && !meetingUrl.trim()) return setError('Enter a meeting URL for the mock live session.')
    setBusy(true); setError(''); setSuccess('')
    try {
      const meeting = await apiRequest<Meeting>('/api/v1/meetings/', { method: 'POST', body: JSON.stringify({ title, meeting_date: new Date(meetingDate).toISOString(), meeting_type: 'other', participants: [] }) })
      let result: Transcript | LiveSession
      if (method === 'Paste transcript') {
        result = await apiRequest<Transcript>('/api/v1/transcripts/paste', { method: 'POST', body: JSON.stringify({ meeting_id: meeting._id, title, transcript_text: transcript, meeting_date: new Date(meetingDate).toISOString(), source: 'manual_paste' }) })
      } else if (method === 'Upload file') {
        const form = new FormData()
        form.append('file', file as File)
        form.append('meeting_id', meeting._id)
        const response = await fetch(`/api/backend?path=${encodeURIComponent('/api/v1/transcripts/upload')}`, { method: 'POST', body: form })
        const payload = await response.json().catch(() => ({}))
        if (!response.ok) throw new Error(payload.detail ?? `Transcript upload failed (${response.status})`)
        result = payload
      } else {
        const liveResult = await apiRequest<LiveSession>(`/api/v1/meetings/${meeting._id}/live-sessions`, { method: 'POST', body: JSON.stringify({ meeting_url: meetingUrl, provider: 'mock', consent_confirmed: true }) })
        result = liveResult
        setLiveSession(liveResult)
        setLiveMeetingId(meeting._id)
      }
      setSuccess(method === 'Live meeting' ? 'Mock live session started. Stop it when the meeting ends.' : `Meeting saved. Transcript processing ${result.status ?? 'started'}.`)
      if (method !== 'Live meeting') setTimeout(() => router.push(`/app/meetings/${meeting._id}`), 700)
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Meeting processing failed.')
    } finally { setBusy(false) }
  }

  return <AppShell active="Meetings"><div className="dashboard-content max-w-6xl"><PageHeading eyebrow="Capture center" title="Bring the room into context." description="Create a meeting and send its transcript to the backend for processing."/><div className="mt-8 flex flex-wrap gap-2 rounded-2xl border border-white/10 bg-white/[.025] p-2">{methods.map(item => <button key={item} type="button" onClick={() => setMethod(item)} className={`capture-tab ${method === item ? 'capture-tab-active' : ''}`} aria-pressed={method === item}>{item}</button>)}</div><form onSubmit={submit} className="capture-card mt-5"><div className="capture-form-grid"><label className="capture-field"><span>Meeting title</span><input required className="capture-input" value={title} onChange={event => setTitle(event.target.value)} placeholder="e.g. Product direction sync" /></label><label className="capture-field"><span>Meeting date</span><input required className="capture-input" type="date" value={meetingDate} onChange={event => setMeetingDate(event.target.value)} /></label></div>{method === 'Paste transcript' && <label className="capture-field mt-6"><span>Transcript text</span><textarea required className="capture-textarea" value={transcript} onChange={event => setTranscript(event.target.value)} placeholder="Paste the transcript here..." /></label>}{method === 'Upload file' && <label className="capture-dropzone mt-6"><input ref={fileRef} className="sr-only" type="file" accept=".txt,.md,.vtt,.srt,.docx,.pdf,.mp3,.wav,.m4a" onChange={event => setFile(event.target.files?.[0] ?? null)} /><span className="capture-drop-icon">↑</span><span className="font-medium text-white">{file?.name ?? 'Choose a transcript file'}</span><span className="text-sm text-muted-foreground">TXT, MD, VTT, SRT, DOCX, PDF, MP3, WAV, or M4A</span></label>}{method === 'Live meeting' && <label className="capture-field mt-6"><span>Meeting URL</span><input required className="capture-input" value={meetingUrl} onChange={event => setMeetingUrl(event.target.value)} placeholder="https://localhost/mock-meeting" /><span className="text-sm text-muted-foreground">Starts the configured mock live-session lifecycle. External providers require separate credentials.</span></label>}{liveSession && <div className="capture-live mt-6"><span className="live-dot" /><div><p className="font-medium text-white">Live session {liveSession.status}</p><p className="mt-1 text-sm text-muted-foreground">Session ID: {liveSession._id}</p></div><button type="button" className="button-ghost px-3 py-2 text-xs" onClick={async () => { try { const stopped = await apiRequest<LiveSession>(`/api/v1/meetings/${liveMeetingId}/live-sessions/${liveSession._id}/stop`, { method: 'POST' }); setLiveSession(stopped); setSuccess('Live session stopped.') } catch (cause) { setError(cause instanceof Error ? cause.message : 'Unable to stop live session.') } }}>Stop session</button></div>}<div className="capture-footer mt-6"><label className="consent-row"><input type="checkbox" checked={consent} onChange={event => setConsent(event.target.checked)} /><span>I have consent to process this meeting</span></label><button type="submit" className="primary-action" disabled={busy || !consent}>{busy ? 'Processing…' : method === 'Live meeting' ? 'Start live session' : 'Save and process'}</button></div>{error && <p role="alert" className="mt-4 text-sm text-rose-300">{error}</p>}{success && <p role="status" className="mt-4 text-sm text-emerald-300">{success}</p>}</form></div></AppShell>
}
