import { clsx, type ClassValue } from 'clsx'

export function cn(...inputs: ClassValue[]) {
  return clsx(inputs)
}

export function formatDate(date: string | Date | null | undefined): string {
  if (!date) return '—'
  const d = typeof date === 'string' ? new Date(date) : date
  if (isNaN(d.getTime())) return '—'
  return d.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })
}

export function formatDateTime(date: string | Date | null | undefined): string {
  if (!date) return '—'
  const d = typeof date === 'string' ? new Date(date) : date
  if (isNaN(d.getTime())) return '—'
  return d.toLocaleString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

export function formatRelative(date: string | Date | null | undefined): string {
  if (!date) return '—'
  const d = typeof date === 'string' ? new Date(date) : date
  if (isNaN(d.getTime())) return '—'
  const now = new Date()
  const diffMs = now.getTime() - d.getTime()
  const diffSecs = Math.floor(diffMs / 1000)
  const diffMins = Math.floor(diffSecs / 60)
  const diffHours = Math.floor(diffMins / 60)
  const diffDays = Math.floor(diffHours / 24)

  if (diffSecs < 60) return 'just now'
  if (diffMins < 60) return `${diffMins}m ago`
  if (diffHours < 24) return `${diffHours}h ago`
  if (diffDays === 1) return 'yesterday'
  if (diffDays < 7) return `${diffDays}d ago`
  return formatDate(d)
}

export type Priority = 'urgent' | 'high' | 'medium' | 'low'
export type Status = 'todo' | 'in_progress' | 'done' | 'cancelled'

export function getPriorityColor(priority: string): string {
  switch (priority?.toLowerCase()) {
    case 'urgent':
      return 'bg-red-500/20 text-red-400 border border-red-500/30'
    case 'high':
      return 'bg-orange-500/20 text-orange-400 border border-orange-500/30'
    case 'medium':
      return 'bg-blue-500/20 text-blue-400 border border-blue-500/30'
    case 'low':
      return 'bg-slate-500/20 text-slate-400 border border-slate-500/30'
    default:
      return 'bg-slate-500/20 text-slate-400 border border-slate-500/30'
  }
}

export function getPriorityDotColor(priority: string): string {
  switch (priority?.toLowerCase()) {
    case 'urgent':
      return 'bg-red-500'
    case 'high':
      return 'bg-orange-500'
    case 'medium':
      return 'bg-blue-500'
    case 'low':
      return 'bg-slate-500'
    default:
      return 'bg-slate-500'
  }
}

export function getStatusColor(status: string): string {
  switch (status?.toLowerCase()) {
    case 'todo':
      return 'bg-slate-500/20 text-slate-400 border border-slate-500/30'
    case 'in_progress':
      return 'bg-blue-500/20 text-blue-400 border border-blue-500/30'
    case 'done':
      return 'bg-green-500/20 text-green-400 border border-green-500/30'
    case 'cancelled':
      return 'bg-red-500/20 text-red-400 border border-red-500/30'
    // CRM stages
    case 'new':
      return 'bg-slate-500/20 text-slate-400 border border-slate-500/30'
    case 'contacted':
      return 'bg-blue-500/20 text-blue-400 border border-blue-500/30'
    case 'qualified':
      return 'bg-purple-500/20 text-purple-400 border border-purple-500/30'
    case 'proposal':
      return 'bg-yellow-500/20 text-yellow-400 border border-yellow-500/30'
    case 'won':
      return 'bg-green-500/20 text-green-400 border border-green-500/30'
    case 'lost':
      return 'bg-red-500/20 text-red-400 border border-red-500/30'
    // Published/Draft
    case 'published':
      return 'bg-green-500/20 text-green-400 border border-green-500/30'
    case 'draft':
      return 'bg-slate-500/20 text-slate-400 border border-slate-500/30'
    case 'scheduled':
      return 'bg-yellow-500/20 text-yellow-400 border border-yellow-500/30'
    default:
      return 'bg-slate-500/20 text-slate-400 border border-slate-500/30'
  }
}

export function truncate(str: string, length: number = 100): string {
  if (!str) return ''
  if (str.length <= length) return str
  return str.slice(0, length) + '...'
}

export function formatCurrency(amount: number, currency: string = 'USD'): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency,
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(amount)
}

export function getInitials(name: string): string {
  if (!name) return '?'
  return name
    .split(' ')
    .map((n) => n[0])
    .join('')
    .toUpperCase()
    .slice(0, 2)
}

export function isOverdue(dueDate: string | null | undefined): boolean {
  if (!dueDate) return false
  return new Date(dueDate) < new Date()
}
