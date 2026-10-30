'use client'

import { FormEvent, useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'

export default function LoginPage() {
  const router = useRouter()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setBusy(true)
    setError('')
    try {
      const response = await fetch('/api/auth/login', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ email, password }) })
      const payload = await response.json().catch(() => ({}))
      if (!response.ok) throw new Error(payload.detail ?? 'Unable to sign in.')
      router.push('/app')
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Unable to sign in.')
      setBusy(false)
    }
  }

  return <main className="flex min-h-screen items-center justify-center bg-ink px-6 text-white"><div className="panel w-full max-w-md"><div className="logo-mark mb-6"><span/><span/><span/></div><h1 className="text-2xl font-semibold">Welcome back</h1><p className="mt-2 text-sm text-slate-500">Sign in to continue to your workspace.</p><form onSubmit={submit} className="mt-6 flex flex-col gap-4"><label className="field">Work email<input required type="email" value={email} onChange={(event) => setEmail(event.target.value)} placeholder="you@company.com" /></label><label className="field">Password<input required minLength={8} type="password" value={password} onChange={(event) => setPassword(event.target.value)} placeholder="••••••••" /></label>{error && <p role="alert" className="text-sm text-rose-300">{error}</p>}<button disabled={busy} className="button-primary mt-2 px-4 py-3 text-sm disabled:opacity-50">{busy ? 'Signing in…' : 'Sign in'}</button></form><p className="mt-6 text-center text-xs text-slate-500">No account? <Link className="text-cyan" href="/register">Create one</Link></p></div></main>
}
