'use client'

import { useState } from 'react'
import { AppShell, PageHeading } from '@/components/contextflow-app'
import { apiRequest } from '@/lib/api'

export default function SecuritySettingsPage() {
  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')
  async function changePassword(event: React.FormEvent) { event.preventDefault(); setError(''); setMessage(''); try { await apiRequest('/api/v1/auth/change-password', { method: 'POST', body: JSON.stringify({ current_password: currentPassword, new_password: newPassword }) }); setCurrentPassword(''); setNewPassword(''); setMessage('Password changed successfully.') } catch (cause) { setError(cause instanceof Error ? cause.message : 'Unable to change password.') } }
  return <AppShell active="Settings"><div className="dashboard-content max-w-5xl"><PageHeading eyebrow="Settings / Security" title="Sign-in & security" description="Change the password used to access this account." /><form onSubmit={changePassword} className="panel mt-8 max-w-xl"><label className="capture-field"><span>Current password</span><input className="capture-input" required type="password" value={currentPassword} onChange={event => setCurrentPassword(event.target.value)} /></label><label className="capture-field mt-5"><span>New password</span><input className="capture-input" required minLength={8} type="password" value={newPassword} onChange={event => setNewPassword(event.target.value)} /></label><button className="button-primary mt-6 px-4 py-3 text-xs">Change password</button>{error && <p role="alert" className="mt-4 text-sm text-rose-300">{error}</p>}{message && <p role="status" className="mt-4 text-sm text-emerald-300">{message}</p>}</form></div></AppShell>
}
