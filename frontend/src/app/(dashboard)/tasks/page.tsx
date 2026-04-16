'use client'

import { useEffect, useState, FormEvent } from 'react'
import {
  Plus, Trash2, CheckCircle, Clock, AlertTriangle, Sparkles,
  ChevronDown, X, Loader2, Filter, Bot
} from 'lucide-react'
import { tasks as tasksApi } from '@/lib/api'
import { cn, formatDate, getPriorityColor, getStatusColor, isOverdue, truncate } from '@/lib/utils'

interface Task {
  id: number
  title: string
  description?: string
  priority: string
  status: string
  due_date?: string
  ai_summary?: string
  created_at: string
}

const PRIORITIES = ['all', 'urgent', 'high', 'medium', 'low']
const STATUSES = ['all', 'todo', 'in_progress', 'done', 'cancelled']

export default function TasksPage() {
  const [taskList, setTaskList] = useState<Task[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [statusFilter, setStatusFilter] = useState('all')
  const [priorityFilter, setPriorityFilter] = useState('all')
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [aiText, setAiText] = useState('')
  const [aiLoading, setAiLoading] = useState(false)
  const [error, setError] = useState('')

  // Stats
  const todo = taskList.filter((t) => t.status === 'todo').length
  const inProgress = taskList.filter((t) => t.status === 'in_progress').length
  const done = taskList.filter((t) => t.status === 'done').length
  const overdue = taskList.filter((t) => isOverdue(t.due_date) && t.status !== 'done').length

  function fetchTasks() {
    const params: any = {}
    if (statusFilter !== 'all') params.status = statusFilter
    if (priorityFilter !== 'all') params.priority = priorityFilter
    tasksApi.list(params)
      .then((res) => {
        setTaskList(res.data?.tasks || res.data || [])
        setIsLoading(false)
      })
      .catch(() => setIsLoading(false))
  }

  useEffect(() => { fetchTasks() }, [statusFilter, priorityFilter])

  async function handleAiCreate() {
    if (!aiText.trim()) return
    setAiLoading(true)
    setError('')
    try {
      await tasksApi.createFromText(aiText.trim())
      setAiText('')
      fetchTasks()
    } catch (e: any) {
      setError(e?.response?.data?.detail || 'Failed to create task from text')
    } finally {
      setAiLoading(false)
    }
  }

  async function markDone(id: number) {
    try {
      await tasksApi.update(id, { status: 'done' })
      fetchTasks()
    } catch { }
  }

  async function deleteTask(id: number) {
    if (!confirm('Delete this task?')) return
    try {
      await tasksApi.delete(id)
      fetchTasks()
    } catch { }
  }

  const filteredTasks = taskList

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Stats bar */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: 'To Do', value: todo, color: 'text-slate-400', bg: 'bg-slate-500/10 border-slate-500/20' },
          { label: 'In Progress', value: inProgress, color: 'text-blue-400', bg: 'bg-blue-500/10 border-blue-500/20' },
          { label: 'Done', value: done, color: 'text-green-400', bg: 'bg-green-500/10 border-green-500/20' },
          { label: 'Overdue', value: overdue, color: 'text-red-400', bg: 'bg-red-500/10 border-red-500/20' },
        ].map((s) => (
          <div key={s.label} className={cn('bg-dark-card border rounded-xl p-4', s.bg)}>
            <p className={cn('text-2xl font-bold', s.color)}>{s.value}</p>
            <p className="text-sm text-dark-text mt-1">{s.label}</p>
          </div>
        ))}
      </div>

      {/* AI text input */}
      <div className="bg-dark-card border border-dark-border rounded-2xl p-5">
        <div className="flex items-center gap-2 mb-3">
          <Bot className="w-5 h-5 text-primary-400" />
          <h3 className="font-semibold text-dark-heading">Create Task from Natural Language</h3>
        </div>
        {error && (
          <p className="text-red-400 text-sm mb-3 bg-red-500/10 border border-red-500/20 rounded-xl px-3 py-2">{error}</p>
        )}
        <div className="flex gap-3">
          <input
            type="text"
            value={aiText}
            onChange={(e) => setAiText(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleAiCreate()}
            placeholder='e.g. "Write a blog post about SEO tips by Friday, high priority"'
            className="flex-1 bg-dark-bg border border-dark-border rounded-xl px-4 py-3 text-dark-heading placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-primary-500/50 focus:border-primary-500 transition text-sm"
          />
          <button
            onClick={handleAiCreate}
            disabled={aiLoading || !aiText.trim()}
            className="flex items-center gap-2 bg-primary-500 hover:bg-primary-600 disabled:bg-primary-500/40 text-white px-5 py-3 rounded-xl font-medium transition"
          >
            {aiLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
            Create
          </button>
        </div>
      </div>

      {/* Filters + Add button */}
      <div className="flex flex-wrap items-center gap-3">
        {/* Status tabs */}
        <div className="flex bg-dark-card border border-dark-border rounded-xl p-1 gap-1 overflow-x-auto">
          {STATUSES.map((s) => (
            <button
              key={s}
              onClick={() => setStatusFilter(s)}
              className={cn(
                'px-3 py-1.5 rounded-lg text-sm font-medium transition capitalize whitespace-nowrap',
                statusFilter === s
                  ? 'bg-primary-500 text-white'
                  : 'text-dark-text hover:text-dark-heading'
              )}
            >
              {s === 'in_progress' ? 'In Progress' : s.charAt(0).toUpperCase() + s.slice(1)}
            </button>
          ))}
        </div>

        {/* Priority filter */}
        <div className="flex bg-dark-card border border-dark-border rounded-xl p-1 gap-1">
          {PRIORITIES.map((p) => (
            <button
              key={p}
              onClick={() => setPriorityFilter(p)}
              className={cn(
                'px-3 py-1.5 rounded-lg text-sm font-medium transition capitalize',
                priorityFilter === p
                  ? 'bg-primary-500 text-white'
                  : 'text-dark-text hover:text-dark-heading'
              )}
            >
              {p.charAt(0).toUpperCase() + p.slice(1)}
            </button>
          ))}
        </div>

        <div className="flex-1" />
        <button
          onClick={() => setShowCreateModal(true)}
          className="flex items-center gap-2 bg-primary-500 hover:bg-primary-600 text-white px-4 py-2 rounded-xl font-medium transition"
        >
          <Plus className="w-4 h-4" />
          New Task
        </button>
      </div>

      {/* Task list */}
      {isLoading ? (
        <div className="grid gap-3">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="h-24 bg-dark-card rounded-2xl animate-pulse" />
          ))}
        </div>
      ) : filteredTasks.length === 0 ? (
        <div className="bg-dark-card border border-dark-border rounded-2xl p-12 text-center">
          <CheckCircle className="w-12 h-12 mx-auto text-slate-600 mb-3" />
          <p className="text-dark-heading font-medium">No tasks found</p>
          <p className="text-dark-text text-sm mt-1">Create your first task or change the filters</p>
        </div>
      ) : (
        <div className="grid gap-3">
          {filteredTasks.map((task) => (
            <div
              key={task.id}
              className={cn(
                'bg-dark-card border rounded-2xl p-4 hover:border-dark-border/80 transition group',
                isOverdue(task.due_date) && task.status !== 'done'
                  ? 'border-red-500/30'
                  : 'border-dark-border'
              )}
            >
              <div className="flex items-start gap-4">
                <div className="flex-1 min-w-0">
                  <div className="flex flex-wrap items-center gap-2 mb-1.5">
                    <span className={cn('text-xs px-2 py-0.5 rounded-full font-medium', getPriorityColor(task.priority))}>
                      {task.priority}
                    </span>
                    <span className={cn('text-xs px-2 py-0.5 rounded-full font-medium', getStatusColor(task.status))}>
                      {task.status?.replace('_', ' ')}
                    </span>
                    {isOverdue(task.due_date) && task.status !== 'done' && (
                      <span className="flex items-center gap-1 text-xs text-red-400">
                        <AlertTriangle className="w-3 h-3" />
                        Overdue
                      </span>
                    )}
                  </div>
                  <p className="font-medium text-dark-heading">{task.title}</p>
                  {task.description && (
                    <p className="text-sm text-dark-text mt-1">{truncate(task.description, 120)}</p>
                  )}
                  {task.ai_summary && (
                    <p className="text-xs text-primary-400 mt-1 italic">AI: {task.ai_summary}</p>
                  )}
                  {task.due_date && (
                    <p className="text-xs text-dark-text mt-2 flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      Due {formatDate(task.due_date)}
                    </p>
                  )}
                </div>
                <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition">
                  {task.status !== 'done' && (
                    <button
                      onClick={() => markDone(task.id)}
                      title="Mark done"
                      className="p-1.5 rounded-lg text-green-400 hover:bg-green-500/10 transition"
                    >
                      <CheckCircle className="w-4 h-4" />
                    </button>
                  )}
                  <button
                    onClick={() => deleteTask(task.id)}
                    title="Delete"
                    className="p-1.5 rounded-lg text-red-400 hover:bg-red-500/10 transition"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Create Task Modal */}
      {showCreateModal && (
        <CreateTaskModal
          onClose={() => setShowCreateModal(false)}
          onCreated={() => { setShowCreateModal(false); fetchTasks() }}
        />
      )}
    </div>
  )
}

function CreateTaskModal({ onClose, onCreated }: { onClose: () => void; onCreated: () => void }) {
  const [form, setForm] = useState({
    title: '',
    description: '',
    priority: 'medium',
    due_date: '',
  })
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    if (!form.title.trim()) { setError('Title is required'); return }
    setIsLoading(true)
    try {
      await tasksApi.create({
        title: form.title.trim(),
        description: form.description || undefined,
        priority: form.priority,
        due_date: form.due_date || undefined,
      })
      onCreated()
    } catch (e: any) {
      setError(e?.response?.data?.detail || 'Failed to create task')
      setIsLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={onClose} />
      <div className="relative bg-dark-card border border-dark-border rounded-2xl p-6 w-full max-w-md shadow-2xl">
        <div className="flex items-center justify-between mb-5">
          <h3 className="font-semibold text-dark-heading text-lg">Create New Task</h3>
          <button onClick={onClose} className="text-dark-text hover:text-dark-heading transition">
            <X className="w-5 h-5" />
          </button>
        </div>
        {error && (
          <p className="text-red-400 text-sm mb-4 bg-red-500/10 border border-red-500/20 rounded-xl px-3 py-2">{error}</p>
        )}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-dark-text mb-1.5">Title *</label>
            <input
              type="text"
              value={form.title}
              onChange={(e) => setForm({ ...form, title: e.target.value })}
              placeholder="Task title"
              className="w-full bg-dark-bg border border-dark-border rounded-xl px-4 py-3 text-dark-heading placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-primary-500/50 focus:border-primary-500 transition text-sm"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-dark-text mb-1.5">Description</label>
            <textarea
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
              placeholder="Task description..."
              rows={3}
              className="w-full bg-dark-bg border border-dark-border rounded-xl px-4 py-3 text-dark-heading placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-primary-500/50 focus:border-primary-500 transition text-sm resize-none"
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-dark-text mb-1.5">Priority</label>
              <select
                value={form.priority}
                onChange={(e) => setForm({ ...form, priority: e.target.value })}
                className="w-full bg-dark-bg border border-dark-border rounded-xl px-4 py-3 text-dark-heading focus:outline-none focus:ring-2 focus:ring-primary-500/50 focus:border-primary-500 transition text-sm"
              >
                {['urgent', 'high', 'medium', 'low'].map((p) => (
                  <option key={p} value={p}>{p.charAt(0).toUpperCase() + p.slice(1)}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-dark-text mb-1.5">Due Date</label>
              <input
                type="date"
                value={form.due_date}
                onChange={(e) => setForm({ ...form, due_date: e.target.value })}
                className="w-full bg-dark-bg border border-dark-border rounded-xl px-4 py-3 text-dark-heading focus:outline-none focus:ring-2 focus:ring-primary-500/50 focus:border-primary-500 transition text-sm"
              />
            </div>
          </div>
          <div className="flex gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 border border-dark-border text-dark-text hover:text-dark-heading py-2.5 rounded-xl transition text-sm font-medium"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isLoading}
              className="flex-1 bg-primary-500 hover:bg-primary-600 disabled:bg-primary-500/50 text-white py-2.5 rounded-xl transition text-sm font-medium flex items-center justify-center gap-2"
            >
              {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Plus className="w-4 h-4" />}
              Create Task
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
