'use client'

import { FormEvent, useState } from 'react'
import { AppShell, PageHeading } from '@/components/contextflow-app'
import { apiRequest } from '@/lib/api'

type Citation = { title?: string; source_type?: string; score?: number; text_reference?: string }
type Answer = { answer?: string; response?: string; citations?: Citation[]; insufficient_evidence?: boolean }

export default function AskPage() {
  const [question, setQuestion] = useState('')
  const [answer, setAnswer] = useState<Answer | null>(null)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  async function ask(event: FormEvent) {
    event.preventDefault()
    if (!question.trim()) return
    setBusy(true); setError('')
    try { setAnswer(await apiRequest<Answer>('/api/v1/ai/workspace/ask', { method: 'POST', body: JSON.stringify({ question }) })) }
    catch (cause) { setError(cause instanceof Error ? cause.message : 'Workspace request failed.') }
    finally { setBusy(false) }
  }
  return <AppShell active="Ask workspace"><div className="dashboard-content max-w-5xl"><PageHeading eyebrow="Grounded workspace assistant" title="Ask your workspace." description="Answers use your active workspace and cite retrieved meetings, tasks, and documents."/><div className="panel mt-8"><div className="min-h-[280px]">{answer ? <div className="space-y-5"><div><p className="eyebrow">Answer</p><p className="mt-3 whitespace-pre-wrap text-sm leading-7 text-slate-300">{answer.answer ?? answer.response ?? 'No answer was returned.'}</p></div>{answer.insufficient_evidence && <p className="text-sm text-amber-300">There is not enough evidence in this workspace to answer confidently.</p>}<div><p className="eyebrow">Sources</p>{answer.citations?.length ? answer.citations.map((citation, index) => <div className="list-row" key={`${citation.title ?? 'source'}-${index}`}><div className="min-w-0 flex-1"><p>{citation.title ?? 'Workspace source'}</p><span>{citation.source_type ?? 'source'}{citation.score == null ? '' : ` · score ${citation.score.toFixed(2)}`}</span></div></div>) : <p className="mt-3 text-sm text-slate-500">No source citations were returned.</p>}</div></div> : <div className="flex min-h-[280px] flex-col items-center justify-center text-center"><div className="flex size-14 items-center justify-center rounded-2xl bg-violet/15 text-violet">✦</div><h2 className="mt-5 text-xl font-medium text-white">Start with a question</h2><p className="mt-2 max-w-md text-sm leading-6 text-slate-500">Ask about decisions, tasks, meetings, or knowledge documents.</p></div>}</div>{error && <p role="alert" className="mb-3 text-sm text-rose-300">{error}</p>}<form onSubmit={ask} className="flex gap-3 border-t border-white/5 pt-4"><input className="search-box flex-1 px-4" value={question} onChange={event => setQuestion(event.target.value)} placeholder="Ask about your workspace..." /><button disabled={busy} className="button-primary px-4 py-2 text-xs disabled:opacity-50">{busy ? 'Asking…' : 'Ask'}</button></form></div></div></AppShell>
}
