'use client'

import { useEffect, useState } from 'react'
import { AppShell, PageHeading } from '@/components/contextflow-app'
import { apiRequest } from '@/lib/api'

type Member = { user: { _id: string; full_name?: string; email?: string }; membership: { role?: string } }
export default function TeamSettingsPage() {
  const [members, setMembers] = useState<Member[]>([])
  const [email, setEmail] = useState('')
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')
  function load() { apiRequest<Member[]>('/api/v1/workspaces/members').then(setMembers).catch(cause => setError(cause instanceof Error ? cause.message : 'Unable to load members.')) }
  useEffect(load, [])
  async function invite(event: React.FormEvent) { event.preventDefault(); setError(''); setMessage(''); try { await apiRequest('/api/v1/workspaces/members', { method: 'POST', body: JSON.stringify({ email, role: 'member' }) }); setEmail(''); setMessage('Member added.'); load() } catch (cause) { setError(cause instanceof Error ? cause.message : 'Unable to add member.') } }
  return <AppShell active="Settings"><div className="dashboard-content max-w-5xl"><PageHeading eyebrow="Workspace access" title="Team members" description="View active members and add existing ContextFlow accounts to this workspace." />
    <form onSubmit={invite} className="mt-8 flex flex-wrap gap-3"><input required type="email" className="search-box h-11 min-w-[280px] px-3" value={email} onChange={event => setEmail(event.target.value)} placeholder="teammate@example.com" /><button className="button-primary px-4 py-3 text-xs">＋ Add member</button></form>
    {error && <p role="alert" className="mt-4 text-sm text-rose-300">{error}</p>}{message && <p role="status" className="mt-4 text-sm text-emerald-300">{message}</p>}
    <div className="panel mt-8">{members.map(item => <div className="list-row" key={item.user._id}><div className="avatar bg-cyan/20 text-cyan">{(item.user.full_name ?? item.user.email ?? '?').slice(0, 2).toUpperCase()}</div><div className="flex-1"><p>{item.user.full_name ?? item.user.email}</p><span>{item.user.email} · {item.membership.role ?? 'member'} · active</span></div></div>)}{!members.length && !error && <p className="p-6 text-sm text-slate-500">No active members found.</p>}</div>
  </div></AppShell>
}
