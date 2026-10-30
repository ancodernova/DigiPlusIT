'use client'

import { useEffect, useState } from 'react'
import { AppShell, PageHeading } from '@/components/contextflow-app'
import { apiRequest } from '@/lib/api'

type Task = { _id: string; title: string; description?: string; status?: string; priority?: string; due_date?: string }
export default function TasksPage() {
  const [tasks, setTasks] = useState<Task[]>([])
  const [error, setError] = useState('')
  async function load() { try { setTasks(await apiRequest<Task[]>('/api/v1/tasks/')) } catch (cause) { setError(cause instanceof Error ? cause.message : 'Unable to load tasks.') } }
  useEffect(() => { load() }, [])
  async function update(task: Task, status: string) { try { const saved = await apiRequest<Task>(`/api/v1/tasks/${task._id}`, { method: 'PATCH', body: JSON.stringify({ status }) }); setTasks(items => items.map(item => item._id === saved._id ? saved : item)) } catch (cause) { setError(cause instanceof Error ? cause.message : 'Unable to update task.') } }
  const open = tasks.filter(item => item.status !== 'completed').length
  const blocked = tasks.filter(item => item.status === 'blocked').length
  return <AppShell active="Tasks"><div className="dashboard-content"><PageHeading eyebrow="Smart carry-forward" title="Tasks" description="Keep commitments attached to their original context instead of creating duplicates." /><div className="mt-8 grid gap-4 sm:grid-cols-3"><div className="metric-card"><p>Open</p><strong>{open}</strong><span>Across this workspace</span></div><div className="metric-card"><p>Blocked</p><strong>{blocked}</strong><span>Needs attention</span></div><div className="metric-card"><p>Completed</p><strong>{tasks.length - open}</strong><span>Finished commitments</span></div></div>{error && <p role="alert" className="mt-6 text-sm text-rose-300">{error}</p>}<div className="panel mt-6"><div className="panel-heading"><div><p className="eyebrow">Workspace commitments</p><h2>Work that needs a next move.</h2></div></div>{tasks.map(task => <div className="list-row" key={task._id}><div className={`priority-dot ${task.priority === 'critical' || task.priority === 'high' ? 'p2' : 'p0'}`} /><div className="min-w-0 flex-1"><p>{task.title}</p><span>{task.priority ?? 'medium'} · {task.due_date ? new Date(task.due_date).toLocaleDateString() : 'No due date'}</span></div><select className="button-ghost px-3 py-2 text-xs" value={task.status ?? 'open'} onChange={event => update(task, event.target.value)}><option value="open">Open</option><option value="in_progress">In progress</option><option value="blocked">Blocked</option><option value="completed">Completed</option></select></div>)}{!tasks.length && !error && <p className="p-6 text-sm text-slate-500">No tasks found in this workspace.</p>}</div></div></AppShell>
}
