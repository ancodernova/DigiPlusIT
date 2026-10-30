'use client'

import { useState } from 'react'
import { AppShell, PageHeading, PendingCard } from '@/components/contextflow-app'

const methods = ['Paste transcript', 'Upload file', 'Live meeting']

export default function NewMeetingPage() {
  const [method, setMethod] = useState(methods[0])
  const [consent, setConsent] = useState(false)

  return (
    <AppShell active="Meetings">
      <div className="dashboard-content max-w-6xl">
        <PageHeading
          eyebrow="Capture center"
          title="Bring the room into context."
          description="Choose a capture method. Processing only begins after the backend confirms receipt."
        />

        <div className="mt-8 flex flex-wrap gap-2 rounded-2xl border border-white/10 bg-white/[.025] p-2 shadow-[0_20px_60px_rgba(0,0,0,.16)]">
          {methods.map((item) => (
            <button
              key={item}
              type="button"
              onClick={() => setMethod(item)}
              className={`capture-tab ${method === item ? 'capture-tab-active' : ''}`}
              aria-pressed={method === item}
            >
              {item}
            </button>
          ))}
        </div>

        <section className="capture-card mt-5">
          <div className="capture-form-grid">
            <label className="capture-field">
              <span>Meeting title</span>
              <input className="capture-input" placeholder="e.g. Product direction sync" />
            </label>
            <label className="capture-field">
              <span>Meeting date</span>
              <input className="capture-input" type="date" />
            </label>
          </div>

          {method === 'Paste transcript' && (
            <label className="capture-field mt-6">
              <span>Transcript text</span>
              <textarea className="capture-textarea" placeholder="Paste the transcript here..." />
            </label>
          )}

          {method === 'Upload file' && (
            <label className="capture-dropzone mt-6">
              <input className="sr-only" type="file" accept=".txt,.md,.vtt,.srt,.docx,.pdf" />
              <span className="capture-drop-icon">↑</span>
              <span className="font-medium text-white">Drop a transcript file here</span>
              <span className="text-sm text-muted-foreground">TXT, MD, VTT, SRT, DOCX, or PDF</span>
            </label>
          )}

          {method === 'Live meeting' && (
            <div className="capture-live mt-6">
              <span className="live-dot" />
              <div>
                <p className="font-medium text-white">Live capture is ready</p>
                <p className="mt-1 text-sm text-muted-foreground">Start when everyone has consented. The room will remain in preview until the backend confirms receipt.</p>
              </div>
            </div>
          )}

          <div className="capture-footer mt-6">
            <label className="consent-row">
              <input type="checkbox" checked={consent} onChange={(event) => setConsent(event.target.checked)} />
              <span>I have consent to process this meeting</span>
            </label>
            <button type="button" className="primary-action" disabled={!consent}>
              {method === 'Live meeting' ? 'Start live capture' : 'Save and analyze'}
            </button>
          </div>
        </section>

        <PendingCard />
      </div>
    </AppShell>
  )
}
