'use client'

import { useEffect, useState } from 'react'
import {
  BarChart, Bar, LineChart, Line, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend
} from 'recharts'
import { TrendingUp, CheckSquare, Users, FileText, Search, Loader2, FileBarChart, Activity } from 'lucide-react'
import { analytics } from '@/lib/api'
import { cn, formatRelative } from '@/lib/utils'

const COLORS = ['#3B82F6', '#22C55E', '#EAB308', '#EF4444', '#8B5CF6', '#F97316']

export default function AnalyticsPage() {
  const [days, setDays] = useState(7)
  const [dashData, setDashData] = useState<any>(null)
  const [activityData, setActivityData] = useState<any[]>([])
  const [weeklyReport, setWeeklyReport] = useState<string>('')
  const [isLoading, setIsLoading] = useState(true)
  const [reportLoading, setReportLoading] = useState(false)

  function fetchData() {
    setIsLoading(true)
    Promise.allSettled([
      analytics.getDashboard(days),
      analytics.getActivity(days),
    ]).then(([dashRes, actRes]) => {
      if (dashRes.status === 'fulfilled') setDashData(dashRes.value.data)
      if (actRes.status === 'fulfilled') {
        const data = actRes.value.data
        setActivityData(data?.activities || data?.timeline || data || [])
      }
    }).finally(() => setIsLoading(false))
  }

  useEffect(() => { fetchData() }, [days])

  async function generateReport() {
    setReportLoading(true)
    try {
      const res = await analytics.generateWeeklyReport()
      setWeeklyReport(res.data?.report || res.data?.insights || res.data?.summary || '')
    } catch { }
    finally { setReportLoading(false) }
  }

  const kpis = dashData ? [
    {
      label: 'Task Completion',
      value: `${dashData.task_completion_rate || 0}%`,
      icon: CheckSquare,
      color: 'text-blue-400',
      bg: 'bg-blue-500/10 border-blue-500/20',
      subtext: `${dashData.completed_tasks || 0} completed`,
    },
    {
      label: 'Lead Conversion',
      value: `${dashData.lead_conversion_rate || 0}%`,
      icon: Users,
      color: 'text-purple-400',
      bg: 'bg-purple-500/10 border-purple-500/20',
      subtext: `${dashData.won_leads || 0} won`,
    },
    {
      label: 'Content Published',
      value: dashData.content_published || 0,
      icon: FileText,
      color: 'text-green-400',
      bg: 'bg-green-500/10 border-green-500/20',
      subtext: `${dashData.draft_posts || 0} drafts`,
    },
    {
      label: 'Keywords Tracked',
      value: dashData.keywords_tracked || 0,
      icon: Search,
      color: 'text-yellow-400',
      bg: 'bg-yellow-500/10 border-yellow-500/20',
      subtext: `${dashData.top_keywords || 0} top rank`,
    },
  ] : []

  // Prepare chart data
  const tasksByStatus = dashData?.tasks_by_status
    ? Object.entries(dashData.tasks_by_status).map(([name, value]) => ({ name, value }))
    : []

  const leadsByStage = dashData?.leads_by_stage
    ? Object.entries(dashData.leads_by_stage).map(([name, value]) => ({ name, value }))
    : []

  const contentByType = dashData?.content_by_type
    ? Object.entries(dashData.content_by_type).map(([name, value]) => ({ name, value }))
    : []

  const activityTimeline = Array.isArray(activityData)
    ? activityData.map((item: any, i: number) => ({
        day: item.date || item.day || `Day ${i + 1}`,
        tasks: item.tasks || item.task_count || 0,
        leads: item.leads || item.lead_count || 0,
        content: item.content || item.content_count || 0,
      }))
    : []

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Date range selector */}
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-dark-heading">Analytics Overview</h2>
        <div className="flex items-center gap-1 bg-dark-card border border-dark-border rounded-xl p-1">
          {[7, 30, 90].map((d) => (
            <button
              key={d}
              onClick={() => setDays(d)}
              className={cn(
                'px-4 py-2 rounded-lg text-sm font-medium transition',
                days === d ? 'bg-primary-500 text-white' : 'text-dark-text hover:text-dark-heading'
              )}
            >
              {d}d
            </button>
          ))}
        </div>
      </div>

      {/* KPI Cards */}
      {isLoading ? (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => <div key={i} className="h-28 bg-dark-card rounded-2xl animate-pulse" />)}
        </div>
      ) : (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {kpis.map((kpi, i) => {
            const Icon = kpi.icon
            return (
              <div key={i} className={cn('bg-dark-card border rounded-2xl p-5', kpi.bg)}>
                <div className="flex items-center justify-between mb-3">
                  <div className={cn('w-10 h-10 rounded-xl flex items-center justify-center', kpi.bg)}>
                    <Icon className={cn('w-5 h-5', kpi.color)} />
                  </div>
                  <TrendingUp className="w-4 h-4 text-slate-600" />
                </div>
                <p className="text-2xl font-bold text-dark-heading">{kpi.value}</p>
                <p className="text-sm text-dark-text mt-0.5">{kpi.label}</p>
                <p className="text-xs text-slate-500 mt-0.5">{kpi.subtext}</p>
              </div>
            )
          })}
        </div>
      )}

      {/* Charts row 1 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Tasks by status */}
        <div className="bg-dark-card border border-dark-border rounded-2xl p-5">
          <h3 className="font-semibold text-dark-heading mb-4">Tasks by Status</h3>
          {tasksByStatus.length > 0 ? (
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={tasksByStatus} barSize={40}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis dataKey="name" tick={{ fill: '#94A3B8', fontSize: 12 }} />
                <YAxis tick={{ fill: '#94A3B8', fontSize: 12 }} />
                <Tooltip contentStyle={{ background: '#1E293B', border: '1px solid #334155', borderRadius: '12px' }} labelStyle={{ color: '#F1F5F9' }} />
                <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                  {tasksByStatus.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-48 flex items-center justify-center text-dark-text text-sm">No data available</div>
          )}
        </div>

        {/* Leads by stage */}
        <div className="bg-dark-card border border-dark-border rounded-2xl p-5">
          <h3 className="font-semibold text-dark-heading mb-4">Lead Pipeline</h3>
          {leadsByStage.length > 0 ? (
            <ResponsiveContainer width="100%" height={220}>
              <PieChart>
                <Pie
                  data={leadsByStage}
                  cx="50%"
                  cy="50%"
                  outerRadius={80}
                  dataKey="value"
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  labelLine={false}
                >
                  {leadsByStage.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                </Pie>
                <Tooltip contentStyle={{ background: '#1E293B', border: '1px solid #334155', borderRadius: '12px' }} />
                <Legend wrapperStyle={{ color: '#94A3B8', fontSize: '12px' }} />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-48 flex items-center justify-center text-dark-text text-sm">No lead data</div>
          )}
        </div>
      </div>

      {/* Charts row 2 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Activity timeline */}
        <div className="bg-dark-card border border-dark-border rounded-2xl p-5">
          <h3 className="font-semibold text-dark-heading mb-4">Activity Timeline</h3>
          {activityTimeline.length > 0 ? (
            <ResponsiveContainer width="100%" height={220}>
              <LineChart data={activityTimeline}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis dataKey="day" tick={{ fill: '#94A3B8', fontSize: 11 }} />
                <YAxis tick={{ fill: '#94A3B8', fontSize: 12 }} />
                <Tooltip contentStyle={{ background: '#1E293B', border: '1px solid #334155', borderRadius: '12px' }} />
                <Legend wrapperStyle={{ color: '#94A3B8', fontSize: '12px' }} />
                <Line type="monotone" dataKey="tasks" stroke="#3B82F6" strokeWidth={2} dot={false} name="Tasks" />
                <Line type="monotone" dataKey="leads" stroke="#8B5CF6" strokeWidth={2} dot={false} name="Leads" />
                <Line type="monotone" dataKey="content" stroke="#22C55E" strokeWidth={2} dot={false} name="Content" />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-48 flex items-center justify-center text-dark-text text-sm">No activity data</div>
          )}
        </div>

        {/* Content by type */}
        <div className="bg-dark-card border border-dark-border rounded-2xl p-5">
          <h3 className="font-semibold text-dark-heading mb-4">Content by Type</h3>
          {contentByType.length > 0 ? (
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={contentByType} layout="vertical" barSize={20}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis type="number" tick={{ fill: '#94A3B8', fontSize: 12 }} />
                <YAxis dataKey="name" type="category" tick={{ fill: '#94A3B8', fontSize: 12 }} width={80} />
                <Tooltip contentStyle={{ background: '#1E293B', border: '1px solid #334155', borderRadius: '12px' }} />
                <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                  {contentByType.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-48 flex items-center justify-center text-dark-text text-sm">No content data</div>
          )}
        </div>
      </div>

      {/* Recent Activity + Weekly Report */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent activity */}
        <div className="bg-dark-card border border-dark-border rounded-2xl p-5">
          <h3 className="font-semibold text-dark-heading mb-4 flex items-center gap-2">
            <Activity className="w-4 h-4 text-primary-400" />
            Recent Activity
          </h3>
          {activityData.length === 0 ? (
            <div className="text-center py-8 text-dark-text text-sm">No recent activity</div>
          ) : (
            <div className="space-y-3">
              {(Array.isArray(activityData) ? activityData : []).slice(0, 8).map((item: any, i: number) => (
                <div key={i} className="flex items-start gap-3">
                  <div className="w-2 h-2 rounded-full bg-primary-500 mt-2 flex-shrink-0" />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-dark-heading">{item.message || item.description || item.event || ''}</p>
                    <p className="text-xs text-dark-text mt-0.5">{formatRelative(item.created_at || item.timestamp)}</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Weekly report */}
        <div className="bg-dark-card border border-dark-border rounded-2xl p-5">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold text-dark-heading flex items-center gap-2">
              <FileBarChart className="w-4 h-4 text-primary-400" />
              AI Weekly Report
            </h3>
            <button
              onClick={generateReport}
              disabled={reportLoading}
              className="flex items-center gap-2 bg-primary-500/20 hover:bg-primary-500/30 border border-primary-500/30 text-primary-400 px-3 py-1.5 rounded-xl text-sm font-medium transition"
            >
              {reportLoading ? <Loader2 className="w-3 h-3 animate-spin" /> : <FileBarChart className="w-3 h-3" />}
              Generate
            </button>
          </div>
          {weeklyReport ? (
            <div className="bg-dark-bg border border-dark-border rounded-xl p-4 max-h-64 overflow-y-auto">
              <p className="text-sm text-dark-heading whitespace-pre-wrap leading-relaxed">{weeklyReport}</p>
            </div>
          ) : (
            <div className="text-center py-8">
              <FileBarChart className="w-12 h-12 mx-auto text-slate-600 mb-3" />
              <p className="text-dark-text text-sm">Click "Generate" to get AI insights about your week's performance</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
