'use client'

import Link from 'next/link'
import { useEffect, useState } from 'react'
import { AppShell, PageHeading } from '@/components/contextflow-app'
import { apiRequest } from '@/lib/api'

type User = { full_name: string; email: string }
type Workspace = { name: string }
export default function SettingsPage() {
  const [user, setUser] = useState<User | null>(null)
  const [workspace, setWorkspace] = useState<Workspace | null>(null)
  const [error, setError] = useState('')
  useEffect(() => { Promise.all([apiRequest<User>('/api/v1/auth/me'), apiRequest<Workspace>('/api/v1/workspaces/current')]).then(([currentUser, currentWorkspace]) => { setUser(currentUser); setWorkspace(currentWorkspace) }).catch(cause => setError(cause instanceof Error ? cause.message : 'Unable to load settings.')) }, [])
  return <AppShell active="Settings"><div className="dashboard-content max-w-5xl"><PageHeading eyebrow="Workspace controls" title="Settings" description="Manage your profile, workspace, team access, connected providers, and security." />{error && <p role="alert" className="mt-6 text-sm text-rose-300">{error}</p>}<div className="mt-8 grid gap-3 md:grid-cols-3"><Link href="/app/settings/profile" className="panel text-left transition-transform hover:-translate-y-1"><p className="eyebrow">Profile</p><h2 className="mt-3">{user?.full_name ?? 'Loading…'}</h2><p className="mt-2 text-sm text-slate-500">{user?.email ?? 'Account information'}</p></Link><Link href="/app/settings/team" className="panel text-left transition-transform hover:-translate-y-1"><p className="eyebrow">Team</p><h2 className="mt-3">{workspace?.name ?? 'Loading…'}</h2><p className="mt-2 text-sm text-slate-500">Members and roles</p></Link><Link href="/app/settings/integrations" className="panel text-left transition-transform hover:-translate-y-1"><p className="eyebrow">Integrations</p><h2 className="mt-3">API services</h2><p className="mt-2 text-sm text-slate-500">Backend, Groq, and Pinecone</p></Link><Link href="/app/settings/security" className="panel text-left transition-transform hover:-translate-y-1"><p className="eyebrow">Security</p><h2 className="mt-3">Sign-in & security</h2><p className="mt-2 text-sm text-slate-500">Password and access</p></Link></div></div></AppShell>
}
