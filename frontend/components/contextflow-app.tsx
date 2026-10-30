'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { Activity, Bell, BookOpen, BrainCircuit, ChevronRight, CircleHelp, FileText, LayoutDashboard, ListChecks, Menu, MessageSquareText, Search, Settings2, Sparkles, X } from 'lucide-react'
import { apiRequest, apiState } from '@/lib/api'

const links = [
  ['/app', 'Overview', LayoutDashboard], ['/app/meetings', 'Meetings', MessageSquareText], ['/app/tasks', 'Tasks', ListChecks], ['/app/knowledge', 'Knowledge', BookOpen], ['/app/context-passports', 'Passports', FileText], ['/app/ask', 'Ask workspace', BrainCircuit], ['/app/activity', 'Activity', Activity], ['/app/settings', 'Settings', Settings2],
] as const

type User = { full_name: string; email: string }
type Workspace = { name: string }

function initials(name: string) {
  return name.split(/\s+/).filter(Boolean).slice(0, 2).map(part => part[0]).join('').toUpperCase() || '?'
}

export function AppShell({ children, active = 'Overview' }: { children: React.ReactNode; active?: string }) {
  const pathname = usePathname()
  const [collapsed, setCollapsed] = useState(false)
  const [mobileOpen, setMobileOpen] = useState(false)
  const [notice, setNotice] = useState(false)
  const [user, setUser] = useState<User | null>(null)
  const [workspace, setWorkspace] = useState<Workspace | null>(null)
  const [identityError, setIdentityError] = useState('')

  useEffect(() => {
    Promise.all([
      apiRequest<User>('/api/v1/auth/me'),
      apiRequest<Workspace>('/api/v1/workspaces/current'),
    ]).then(([currentUser, currentWorkspace]) => {
      setUser(currentUser)
      setWorkspace(currentWorkspace)
    }).catch(cause => setIdentityError(cause instanceof Error ? cause.message : 'Unable to load account.'))
  }, [])

  const displayName = user?.full_name || 'Loading account'
  const role = 'Workspace member'
  return <div className="app-shell"><aside className={`sidebar ${collapsed ? 'sidebar-collapsed' : ''} ${mobileOpen ? 'sidebar-mobile-open' : ''}`}><div className="flex h-full flex-col"><div className="flex items-center justify-between px-5 py-6"><Link href="/" className="flex items-center gap-3"><div className="logo-mark"><span/><span/><span/></div>{!collapsed && <span className="text-[15px] font-semibold text-white">ContextFlow <em className="not-italic text-cyan">AI</em></span>}</Link><button onClick={() => setCollapsed(!collapsed)} className="sidebar-toggle" aria-label="Toggle sidebar"><ChevronRight className={collapsed ? '' : 'rotate-180'} /></button></div><div className="mx-4 mb-6 flex items-center gap-3 rounded-xl border border-white/8 bg-white/[0.03] p-3"><div className="flex size-8 items-center justify-center rounded-lg bg-violet/20 text-xs font-semibold text-violet">D+</div>{!collapsed && <div className="min-w-0"><p className="truncate text-xs font-medium text-slate-200">{workspace?.name || 'Loading workspace'}</p><p className="text-[10px] text-slate-500">Active workspace</p></div>}</div><div className="px-4 text-[10px] font-semibold uppercase tracking-[0.16em] text-slate-600">Workspace</div><nav className="mt-3 flex-1 px-3">{links.map(([href, label, Icon]) => <Link key={href} href={href} title={collapsed ? label : undefined} className={pathname === href || (href !== '/app' && pathname.startsWith(href + '/')) || (!pathname && active === label) ? 'nav-item nav-active' : 'nav-item'}><Icon />{!collapsed && <span>{label}</span>}</Link>)}</nav><div className="mx-3 border-t border-white/5 pt-3"><button className="nav-item"><CircleHelp />{!collapsed && <span>Help center</span>}</button></div><div className="mt-3 border-t border-white/5 p-4"><div className="flex items-center gap-3"><div className="avatar bg-cyan/20 text-cyan">{initials(displayName)}</div>{!collapsed && <div className="min-w-0"><p className="truncate text-xs font-medium text-slate-200">{displayName}</p><p className="text-[10px] text-slate-500">{role}</p></div>}</div></div></div></aside><main className="dashboard-main"><header className="topbar"><button className="mobile-menu" onClick={() => setMobileOpen(!mobileOpen)} aria-label="Open navigation"><Menu /></button><div className="hidden items-center gap-2 text-xs text-slate-500 md:flex"><span>Workspace</span><ChevronRight/><span className="text-slate-300">{active}</span></div><div className="flex items-center gap-3"><label className="search-box hidden md:flex"><Search/><input placeholder="Search workspace..."/><kbd>⌘ K</kbd></label><button onClick={() => setNotice(!notice)} className="icon-button" aria-label="Notifications"><Bell/><span className="notification-dot"/></button><div className="avatar bg-cyan/20 text-cyan">{initials(displayName)}</div></div>{notice && <div className="notification-pop"><div className="flex items-center justify-between"><p className="text-sm font-medium">Notifications</p><button onClick={() => setNotice(false)} aria-label="Close notifications"><X/></button></div><p className="mt-3 text-xs leading-5 text-slate-500">No new notifications.</p></div>}</header>{identityError && <p role="alert" className="mx-6 mt-4 text-sm text-rose-300">{identityError}</p>}{children}</main></div>
}

export function PendingCard({ title = 'FastAPI backend connected' }: { title?: string }) { const connected = apiState === 'connected'; return <div className={`rounded-2xl border p-5 ${connected ? 'border-emerald-400/20 bg-emerald-400/[0.05]' : 'border-cyan/20 bg-cyan/[0.05]'}`}><div className="flex items-start gap-3"><Sparkles className={`mt-0.5 ${connected ? 'text-emerald-300' : 'text-cyan'}`} /><div><p className="text-sm font-medium text-white">{connected ? title : 'Integration pending'}</p><p className="mt-1 max-w-xl text-sm leading-6 text-slate-400">{connected ? 'Live data and protected actions use the FastAPI proxy with HttpOnly JWT session handling.' : <>Connect the FastAPI backend with <code className="text-cyan">NEXT_API_URL</code> to load live data.</>}</p></div></div></div> }

export function PageHeading({ eyebrow, title, description, action }: { eyebrow: string; title: string; description: string; action?: React.ReactNode }) { return <div className="flex flex-col justify-between gap-5 md:flex-row md:items-end"><div><div className="eyebrow"><span className="pulse-dot"/>{eyebrow}</div><h1 className="mt-3 text-3xl font-semibold tracking-[-0.045em] text-white md:text-4xl">{title}</h1><p className="mt-2 max-w-2xl text-sm leading-6 text-slate-500">{description}</p></div>{action}</div> }
