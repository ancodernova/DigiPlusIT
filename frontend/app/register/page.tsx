'use client'

import { FormEvent, useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'

export default function RegisterPage() {
  const router = useRouter()
  const [fullName, setFullName] = useState('')
  const [email, setEmail] = useState('')
  const [workspaceName, setWorkspaceName] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setBusy(true)
    setError('')
    try {
      const response = await fetch('/api/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          full_name: fullName,
          email,
          password,
          workspace_name: workspaceName,
        }),
      })
      const payload = await response.json().catch(() => ({}))
      if (!response.ok) {
        const detail = Array.isArray(payload.detail)
          ? payload.detail.map((item: { msg?: string }) => item.msg ?? 'Invalid value').join(', ')
          : payload.detail
        throw new Error(detail ?? 'Unable to create your account.')
      }
      router.push('/app')
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Unable to create your account.')
      setBusy(false)
    }
  }

  return <main className="flex min-h-screen items-center justify-center bg-ink px-6 text-white"><div className="panel w-full max-w-md"><div className="logo-mark mb-6"><span/><span/><span/></div><h1 className="text-2xl font-semibold">Create your account</h1><p className="mt-2 text-sm text-slate-500">Start preserving your team's context.</p><form onSubmit={submit} className="mt-6 flex flex-col gap-4"><label className="field">Full name<input required minLength={2} value={fullName} onChange={event => setFullName(event.target.value)} placeholder="Jordan Lee"/></label><label className="field">Work email<input required type="email" value={email} onChange={event => setEmail(event.target.value)} placeholder="you@company.com"/></label><label className="field">Workspace name<input required minLength={2} value={workspaceName} onChange={event => setWorkspaceName(event.target.value)} placeholder="Acme Product Team"/></label><label className="field">Password<input required minLength={8} type="password" value={password} onChange={event => setPassword(event.target.value)} placeholder="Create a password"/></label>{error && <p role="alert" className="text-sm text-rose-300">{error}</p>}<button disabled={busy} className="button-primary mt-2 px-4 py-3 text-sm disabled:opacity-50">{busy ? 'Creating workspace…' : 'Create workspace'}</button></form><p className="mt-6 text-center text-xs text-slate-500">Already have an account? <Link className="text-cyan" href="/login">Sign in</Link></p></div></main>
}
