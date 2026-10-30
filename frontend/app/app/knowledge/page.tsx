'use client'

import { useEffect, useState } from 'react'
import { AppShell, PageHeading } from '@/components/contextflow-app'
import { apiRequest } from '@/lib/api'

type Document = { _id: string; title: string; content: string; document_type?: string; updated_at?: string }
export default function KnowledgePage() {
  const [documents, setDocuments] = useState<Document[]>([])
  const [search, setSearch] = useState('')
  const [error, setError] = useState('')
  useEffect(() => { const query = search.trim() ? `?search=${encodeURIComponent(search.trim())}` : ''; apiRequest<Document[]>(`/api/v1/knowledge/${query}`).then(setDocuments).catch(cause => setError(cause instanceof Error ? cause.message : 'Unable to load knowledge.')) }, [search])
  return <AppShell active="Knowledge"><div className="dashboard-content"><PageHeading eyebrow="Workspace memory" title="Knowledge" description="Browse the durable source of truth for the documents and decisions your team relies on." />
    <div className="mt-8 flex gap-3"><input className="search-box h-11 min-w-[280px] px-3" value={search} onChange={event => setSearch(event.target.value)} placeholder="Search documents..." /></div>
    {error && <p role="alert" className="mt-6 text-sm text-rose-300">{error}</p>}
    <div className="mt-6 grid gap-4 md:grid-cols-3"><div className="panel"><p className="eyebrow">Documents</p><strong className="mt-4 block text-3xl text-white">{documents.length}</strong><p className="mt-2 text-sm text-slate-500">Available in this workspace</p></div><div className="panel"><p className="eyebrow">Recently updated</p><strong className="mt-4 block text-3xl text-white">{documents.filter(item => item.updated_at && Date.now() - new Date(item.updated_at).getTime() < 7 * 86400000).length}</strong><p className="mt-2 text-sm text-slate-500">In the last 7 days</p></div><div className="panel"><p className="eyebrow">Search coverage</p><strong className="mt-4 block text-3xl text-cyan">{documents.length ? 'Available' : '0'}</strong><p className="mt-2 text-sm text-slate-500">Live API results</p></div></div>
    <div className="panel mt-6">{documents.map(item => <div className="list-row" key={item._id}><div className="flex-1 min-w-0"><p>{item.title}</p><span>{item.document_type ?? 'note'} · {item.updated_at ? new Date(item.updated_at).toLocaleDateString() : 'Recently updated'}</span><p className="mt-2 truncate text-xs text-slate-500">{item.content}</p></div></div>)}{!documents.length && !error && <p className="p-6 text-sm text-slate-500">No knowledge documents found.</p>}</div>
  </div></AppShell>
}
