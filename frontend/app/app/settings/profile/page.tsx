'use client'

import { useEffect, useState } from 'react'
import { AppShell, PageHeading } from '@/components/contextflow-app'
import { apiRequest } from '@/lib/api'

export default function ProfileSettingsPage() {
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')
  useEffect(() => { apiRequest<{ full_name: string; email: string }>('/api/v1/auth/me').then(user => { setName(user.full_name); setEmail(user.email) }).catch(cause => setError(cause instanceof Error ? cause.message : 'Unable to load profile.')) }, [])
  async function save(event: React.FormEvent) { event.preventDefault(); try { await apiRequest('/api/v1/auth/me', { method: 'PATCH', body: JSON.stringify({ full_name: name }) }); setMessage('Profile updated.') } catch (cause) { setError(cause instanceof Error ? cause.message : 'Unable to update profile.') } }
  return <AppShell active="Settings"><div className="dashboard-content max-w-5xl"><PageHeading eyebrow="Settings / Profile" title="Profile" description="Manage the identity shown across your workspace." /><form onSubmit={save} className="panel mt-8 max-w-xl"><label className="capture-field"><span>Full name</span><input className="capture-input" required value={name} onChange={event => setName(event.target.value)} /></label><label className="capture-field mt-5"><span>Email</span><input className="capture-input" disabled value={email} /></label><button className="button-primary mt-6 px-4 py-3 text-xs">Save profile</button>{error && <p role="alert" className="mt-4 text-sm text-rose-300">{error}</p>}{message && <p role="status" className="mt-4 text-sm text-emerald-300">{message}</p>}</form></div></AppShell>
}
