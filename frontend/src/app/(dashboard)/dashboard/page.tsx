'use client'

import { useEffect, useState } from 'react'
import {
  CheckSquare, Users, FileText, Search, TrendingUp, AlertTriangle,
  Plus, Zap, ArrowRight, Clock, CheckCircle, XCircle, Activity
} from 'lucide-react'
import { useRouter } from 'next/navigation'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend
} from 'recharts'
import { analytics, tasks as tasksApi, assistant } from '@/lib/api'
import { formatRelative, formatDate, getPriorityColor, getStatusColor, cn } from '@/lib/utils'

interface StatCard {
  label: string
  value: string | number
  icon: React.ElementType
  color: string
  change?: string
  changeType?: 'up' | 'down' | 'neutral'
}

interface Task {
  id: number
  title: string
  priority: string
  status: string
  due_date?: string
}

interface Activity {
  id: number
  type: string
  message: string
  created_at: string
}

const TASK_COLORS = ['#94A3B8', '#3B82F6', '#22C55E', '#EF4444']
const PIE_COLORS = ['#3B82F6', '#22C55E', '#EAB308', '#EF4444', '#8B5CF6']

export default function DashboardPage() {
  const router = useRouter()
  const [dashData, setDashData] = useState<any>(null)
  const [recentTasks, setRecentTasks] = useState<Task[]>([])
  const [briefing, setBriefing] = useState<string>('')
  const [activity, setActivity] = useState<Activity[]>([])
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    Promise.allSettled([
      analytics.getDashboard(7),
      tasksApi.list({ }),
      assistant.getDailyBriefing(),
      analytics.getActivity(7),
    ]).then(([dashRes, tasksRes, briefRes, actRes]) => {
      if (dashRes.status === 'fulfilled') setDashData(dashRes.value.data)
      if (tasksRes.status === 'fulfilled') {
        const all = tasksRes.value.data?.tasks || tasksRes.value.data || []
        setRecentTasks(all.slice(0, 6))
      }
      if (briefRes.status === 'fulfilled') {
        setBriefing(briefRes.value.data?.briefing || briefRes.value.data?.message || '')
      }
      if (actRes.status === 'fulfilled') {
        setActivity(actRes.value.data?.activities || actRes.value.data || [])
      }
      setIsLoading(false)
    })
  }, [])

  const stats = dashData ? [
    {
      label: 'Total Tasks',
      value: dashData.total_tasks || 0,
      icon: CheckSquare,
      color: 'text-blue-400',
      bg: 'bg-blue-500/10 border-blue-500/20',
    },
    {
      label: 'Active Leads',
      value: dashData.active_leads || 0,
      icon: Users,
      color: 'text-purple-400',
      bg: 'bg-purple-500/10 border-purple-500/20',
    },
    {
      label: 'Content Posts',
      value: dashData.content_posts || 0,
      icon: FileText,
      color: 'text-green-400',
      bg: 'bg-green-500/10 border-green-500/20',
    },
    {
      label: 'Keywords Tracked',
      value: dashData.keywords_tracked || 0,
      icon: Search,
      color: 'text-yellow-400',
      bg: 'bg-yellow-500/10 border-yellow-500/20',
    },
  ] : []

  const taskChartData = dashData?.tasks_by_status
    ? Object.entries(dashData.tasks_by_status).map(([name, value]) => ({ name, value }))
    : [
        { name: 'Todo', value: 0 },
        { name: 'In Progress', value: 0 },
        { name: 'Done', value: 0 },
        { name: 'Cancelled', value: 0 },
      ]

  const leadsChartData = dashData?.leads_by_stage
    ? Object.entries(dashData.leads_by_stage).map(([name, value]) => ({ name, value }))
    : []

  if (isLoading) {
    return (
      <div className="space-y-6 animate-pulse">
        <div className="h-28 bg-dark-card rounded-2xl" />
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => <div key={i} className="h-24 bg-dark-card rounded-2xl" />)}
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {[...Array(2)].map((_, i) => <div key={i} className="h-64 bg-dark-card rounded-2xl" />)}
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Briefing banner */}
      {briefing && (
        <div className="bg-gradient-to-r from-primary-500/10 to-purple-500/10 border border-primary-500/20 rounded-2xl p-5">
          <div className="flex items-start gap-3">
            <div className="w-8 h-8 bg-primary-500/20 rounded-xl flex items-center justify-center flex-shrink-0">
              <Zap className="w-4 h-4 text-primary-400" />
            </div>
            <div>
              <p className="text-sm font-semibold text-primary-400 mb-1">ARIA Daily Briefing</p>
              <p className="text-dark-text text-sm leading-relaxed">{briefing}</p>
            </div>
          </div>
        </div>
      )}

      {/* Stats */}
      {stats.length > 0 && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {stats.map((stat, i) => {
            const Icon = stat.icon
            return (
              <div key={i} className={cn('bg-dark-card border rounded-2xl p-5', stat.bg)}>
                <div className="flex items-center justify-between mb-3">
                  <div className={cn('w-10 h-10 rounded-xl flex items-center justify-center', stat.bg)}>
                    <Icon className={cn('w-5 h-5', stat.color)} />
                  </div>
                  <TrendingUp className="w-4 h-4 text-slate-600" />
                </div>
                <p className="text-2xl font-bold text-dark-heading">{stat.value}</p>
                <p className="text-sm text-dark-text mt-1">{stat.label}</p>
              </div>
            )
          })}
        </div>
      )}

      {/* Charts row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Tasks by status bar chart */}
        <div className="bg-dark-card border border-dark-border rounded-2xl p-5">
          <h3 className="font-semibold text-dark-heading mb-4">Tasks by Status</h3>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={taskChartData} barSize={32}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="name" tick={{ fill: '#94A3B8', fontSize: 12 }} />
              <YAxis tick={{ fill: '#94A3B8', fontSize: 12 }} />
              <Tooltip
                contentStyle={{ background: '#1E293B', border: '1px solid #334155', borderRadius: '12px' }}
                labelStyle={{ color: '#F1F5F9' }}
              />
              <Bar dataKey="value" fill="#3B82F6" radius={[4, 4, 0, 0]}>
                {taskChartData.map((_, index) => (
                  <Cell key={index} fill={TASK_COLORS[index % TASK_COLORS.length]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Leads by stage pie chart */}
        <div className="bg-dark-card border border-dark-border rounded-2xl p-5">
          <h3 className="font-semibold text-dark-heading mb-4">Leads by Stage</h3>
          {leadsChartData.length > 0 ? (
            <ResponsiveContainer width="100%" height={200}>
              <PieChart>
                <Pie
                  data={leadsChartData}
                  cx="50%"
                  cy="50%"
                  innerRadius={50}
                  outerRadius={80}
                  dataKey="value"
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  labelLine={false}
                >
                  {leadsChartData.map((_, index) => (
                    <Cell key={index} fill={PIE_COLORS[index % PIE_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{ background: '#1E293B', border: '1px solid #334155', borderRadius: '12px' }}
                />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-48 flex items-center justify-center text-dark-text text-sm">
              No lead data available
            </div>
          )}
        </div>
      </div>

      {/* Recent tasks + Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Tasks */}
        <div className="bg-dark-card border border-dark-border rounded-2xl p-5">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold text-dark-heading">Recent Tasks</h3>
            <button
              onClick={() => router.push('/tasks')}
              className="text-primary-400 hover:text-primary-300 text-sm flex items-center gap-1 transition"
            >
              View all <ArrowRight className="w-3 h-3" />
            </button>
          </div>
          {recentTasks.length === 0 ? (
            <div className="text-center py-8 text-dark-text text-sm">
              <CheckSquare className="w-8 h-8 mx-auto mb-2 text-slate-600" />
              No tasks yet
            </div>
          ) : (
            <div className="space-y-2">
              {recentTasks.map((task) => (
                <div
                  key={task.id}
                  className="flex items-center gap-3 p-3 rounded-xl hover:bg-dark-bg/50 transition"
                >
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-dark-heading truncate">{task.title}</p>
                    {task.due_date && (
                      <p className="text-xs text-dark-text mt-0.5 flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        {formatDate(task.due_date)}
                      </p>
                    )}
                  </div>
                  <span className={cn('text-xs px-2 py-0.5 rounded-full font-medium', getPriorityColor(task.priority))}>
                    {task.priority}
                  </span>
                  <span className={cn('text-xs px-2 py-0.5 rounded-full font-medium', getStatusColor(task.status))}>
                    {task.status?.replace('_', ' ')}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Activity Timeline */}
        <div className="bg-dark-card border border-dark-border rounded-2xl p-5">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold text-dark-heading">Recent Activity</h3>
            <Activity className="w-4 h-4 text-slate-500" />
          </div>
          {activity.length === 0 ? (
            <div className="text-center py-8 text-dark-text text-sm">
              <Activity className="w-8 h-8 mx-auto mb-2 text-slate-600" />
              No recent activity
            </div>
          ) : (
            <div className="space-y-3">
              {activity.slice(0, 6).map((item, i) => (
                <div key={item.id || i} className="flex items-start gap-3">
                  <div className="w-2 h-2 rounded-full bg-primary-500 mt-2 flex-shrink-0" />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-dark-heading">{item.message}</p>
                    <p className="text-xs text-dark-text mt-0.5">{formatRelative(item.created_at)}</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Quick actions */}
      <div className="bg-dark-card border border-dark-border rounded-2xl p-5">
        <h3 className="font-semibold text-dark-heading mb-4">Quick Actions</h3>
        <div className="flex flex-wrap gap-3">
          <button
            onClick={() => router.push('/tasks')}
            className="flex items-center gap-2 bg-primary-500/20 hover:bg-primary-500/30 border border-primary-500/30 text-primary-400 px-4 py-2 rounded-xl text-sm font-medium transition"
          >
            <Plus className="w-4 h-4" />
            Create Task
          </button>
          <button
            onClick={() => router.push('/content')}
            className="flex items-center gap-2 bg-green-500/10 hover:bg-green-500/20 border border-green-500/20 text-green-400 px-4 py-2 rounded-xl text-sm font-medium transition"
          >
            <FileText className="w-4 h-4" />
            Generate Blog
          </button>
          <button
            onClick={() => router.push('/crm')}
            className="flex items-center gap-2 bg-purple-500/10 hover:bg-purple-500/20 border border-purple-500/20 text-purple-400 px-4 py-2 rounded-xl text-sm font-medium transition"
          >
            <Users className="w-4 h-4" />
            Add Lead
          </button>
          <button
            onClick={() => router.push('/assistant')}
            className="flex items-center gap-2 bg-yellow-500/10 hover:bg-yellow-500/20 border border-yellow-500/20 text-yellow-400 px-4 py-2 rounded-xl text-sm font-medium transition"
          >
            <Zap className="w-4 h-4" />
            Ask ARIA
          </button>
        </div>
      </div>
    </div>
  )
}
