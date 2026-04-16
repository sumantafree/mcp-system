'use client'

import { useEffect, useState, FormEvent } from 'react'
import {
  Users, Plus, X, Loader2, Bot, Send, Phone, Mail,
  DollarSign, TrendingUp, Star, ChevronRight, MessageSquare
} from 'lucide-react'
import { crm } from '@/lib/api'
import { cn, formatCurrency, getStatusColor, formatDate, truncate } from '@/lib/utils'

const STAGES = ['new', 'contacted', 'qualified', 'proposal', 'won', 'lost']

interface Lead {
  id: number
  name: string
  email?: string
  company?: string
  phone?: string
  deal_value?: number
  stage: string
  notes?: string
  ai_score?: number
  created_at: string
}

export default function CrmPage() {
  const [leads, setLeads] = useState<Lead[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [showAddModal, setShowAddModal] = useState(false)
  const [selectedLead, setSelectedLead] = useState<Lead | null>(null)

  function fetchLeads() {
    crm.listLeads()
      .then((res) => setLeads(res.data?.leads || res.data || []))
      .catch(() => { })
      .finally(() => setIsLoading(false))
  }

  useEffect(() => { fetchLeads() }, [])

  function getLeadsByStage(stage: string) {
    return leads.filter((l) => l.stage === stage)
  }

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-dark-heading">CRM Pipeline</h2>
          <p className="text-dark-text text-sm mt-0.5">{leads.length} total leads</p>
        </div>
        <button
          onClick={() => setShowAddModal(true)}
          className="flex items-center gap-2 bg-primary-500 hover:bg-primary-600 text-white px-4 py-2 rounded-xl font-medium transition"
        >
          <Plus className="w-4 h-4" />
          Add Lead
        </button>
      </div>

      {/* Pipeline board */}
      {isLoading ? (
        <div className="flex gap-4 overflow-x-auto pb-4">
          {STAGES.map((s) => (
            <div key={s} className="w-64 flex-shrink-0 bg-dark-card border border-dark-border rounded-2xl p-4 animate-pulse">
              <div className="h-5 bg-dark-bg rounded mb-4" />
              {[...Array(2)].map((_, i) => <div key={i} className="h-24 bg-dark-bg rounded-xl mb-3" />)}
            </div>
          ))}
        </div>
      ) : (
        <div className="flex gap-4 overflow-x-auto pb-4">
          {STAGES.map((stage) => {
            const stageLeads = getLeadsByStage(stage)
            const stageValue = stageLeads.reduce((sum, l) => sum + (l.deal_value || 0), 0)
            return (
              <div key={stage} className="w-72 flex-shrink-0">
                <div className="bg-dark-card border border-dark-border rounded-2xl overflow-hidden">
                  {/* Stage header */}
                  <div className="px-4 py-3 border-b border-dark-border flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className={cn('text-sm font-semibold capitalize', getStatusTextColor(stage))}>
                        {stage}
                      </span>
                      <span className="text-xs bg-dark-bg text-dark-text rounded-full w-5 h-5 flex items-center justify-center font-bold">
                        {stageLeads.length}
                      </span>
                    </div>
                    {stageValue > 0 && (
                      <span className="text-xs text-green-400 font-medium">{formatCurrency(stageValue)}</span>
                    )}
                  </div>
                  {/* Leads */}
                  <div className="p-3 space-y-2 max-h-[calc(100vh-280px)] overflow-y-auto">
                    {stageLeads.length === 0 ? (
                      <div className="text-center py-6 text-dark-text text-sm">
                        <Users className="w-8 h-8 mx-auto text-slate-700 mb-2" />
                        No leads
                      </div>
                    ) : (
                      stageLeads.map((lead) => (
                        <LeadCard
                          key={lead.id}
                          lead={lead}
                          onClick={() => setSelectedLead(lead)}
                          onScored={fetchLeads}
                        />
                      ))
                    )}
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      )}

      {/* Add lead modal */}
      {showAddModal && (
        <AddLeadModal
          onClose={() => setShowAddModal(false)}
          onCreated={() => { setShowAddModal(false); fetchLeads() }}
        />
      )}

      {/* Lead detail sidebar */}
      {selectedLead && (
        <LeadDetailSidebar
          lead={selectedLead}
          onClose={() => setSelectedLead(null)}
          onUpdated={fetchLeads}
        />
      )}
    </div>
  )
}

function getStatusTextColor(stage: string) {
  switch (stage) {
    case 'new': return 'text-slate-400'
    case 'contacted': return 'text-blue-400'
    case 'qualified': return 'text-purple-400'
    case 'proposal': return 'text-yellow-400'
    case 'won': return 'text-green-400'
    case 'lost': return 'text-red-400'
    default: return 'text-dark-text'
  }
}

function LeadCard({ lead, onClick, onScored }: { lead: Lead; onClick: () => void; onScored: () => void }) {
  const [scoring, setScoring] = useState(false)

  async function handleScore(e: React.MouseEvent) {
    e.stopPropagation()
    setScoring(true)
    try {
      await crm.scoreLead(lead.id)
      onScored()
    } catch { }
    finally { setScoring(false) }
  }

  return (
    <div
      onClick={onClick}
      className="bg-dark-bg border border-dark-border rounded-xl p-3 cursor-pointer hover:border-primary-500/30 transition group"
    >
      <div className="flex items-start justify-between gap-2 mb-2">
        <div className="flex-1 min-w-0">
          <p className="font-medium text-dark-heading text-sm truncate">{lead.name}</p>
          {lead.company && (
            <p className="text-xs text-dark-text truncate">{lead.company}</p>
          )}
        </div>
        {lead.ai_score !== undefined && lead.ai_score !== null && (
          <div className={cn(
            'flex items-center gap-1 text-xs font-bold px-1.5 py-0.5 rounded-lg',
            lead.ai_score >= 70 ? 'bg-green-500/20 text-green-400' :
            lead.ai_score >= 40 ? 'bg-yellow-500/20 text-yellow-400' :
            'bg-red-500/20 text-red-400'
          )}>
            <Star className="w-3 h-3" />
            {lead.ai_score}
          </div>
        )}
      </div>
      {lead.deal_value && (
        <div className="flex items-center gap-1 text-xs text-green-400 mb-2">
          <DollarSign className="w-3 h-3" />
          {formatCurrency(lead.deal_value)}
        </div>
      )}
      <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition">
        <button
          onClick={handleScore}
          className="flex items-center gap-1 text-xs text-primary-400 hover:text-primary-300 transition"
        >
          {scoring ? <Loader2 className="w-3 h-3 animate-spin" /> : <Bot className="w-3 h-3" />}
          AI Score
        </button>
        <span className="text-dark-border">·</span>
        <button className="flex items-center gap-1 text-xs text-dark-text hover:text-dark-heading transition">
          Details <ChevronRight className="w-3 h-3" />
        </button>
      </div>
    </div>
  )
}

function AddLeadModal({ onClose, onCreated }: { onClose: () => void; onCreated: () => void }) {
  const [form, setForm] = useState({
    name: '', email: '', company: '', phone: '', deal_value: '', stage: 'new', notes: ''
  })
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    if (!form.name.trim()) { setError('Name is required'); return }
    setIsLoading(true)
    try {
      await crm.createLead({
        name: form.name.trim(),
        email: form.email || undefined,
        company: form.company || undefined,
        phone: form.phone || undefined,
        deal_value: form.deal_value ? Number(form.deal_value) : undefined,
        stage: form.stage,
        notes: form.notes || undefined,
      })
      onCreated()
    } catch (e: any) {
      setError(e?.response?.data?.detail || 'Failed to create lead')
      setIsLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={onClose} />
      <div className="relative bg-dark-card border border-dark-border rounded-2xl p-6 w-full max-w-lg shadow-2xl max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between mb-5">
          <h3 className="font-semibold text-dark-heading text-lg">Add New Lead</h3>
          <button onClick={onClose} className="text-dark-text hover:text-dark-heading transition">
            <X className="w-5 h-5" />
          </button>
        </div>
        {error && <p className="text-red-400 text-sm mb-4 bg-red-500/10 border border-red-500/20 rounded-xl px-3 py-2">{error}</p>}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="col-span-2">
              <label className="block text-sm font-medium text-dark-text mb-1.5">Full Name *</label>
              <input
                type="text"
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                placeholder="John Smith"
                className="w-full bg-dark-bg border border-dark-border rounded-xl px-4 py-3 text-dark-heading placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-primary-500/50 focus:border-primary-500 transition text-sm"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-dark-text mb-1.5">Email</label>
              <input
                type="email"
                value={form.email}
                onChange={(e) => setForm({ ...form, email: e.target.value })}
                placeholder="john@company.com"
                className="w-full bg-dark-bg border border-dark-border rounded-xl px-4 py-3 text-dark-heading placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-primary-500/50 focus:border-primary-500 transition text-sm"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-dark-text mb-1.5">Phone</label>
              <input
                type="tel"
                value={form.phone}
                onChange={(e) => setForm({ ...form, phone: e.target.value })}
                placeholder="+1 (555) 000-0000"
                className="w-full bg-dark-bg border border-dark-border rounded-xl px-4 py-3 text-dark-heading placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-primary-500/50 focus:border-primary-500 transition text-sm"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-dark-text mb-1.5">Company</label>
              <input
                type="text"
                value={form.company}
                onChange={(e) => setForm({ ...form, company: e.target.value })}
                placeholder="Acme Corp"
                className="w-full bg-dark-bg border border-dark-border rounded-xl px-4 py-3 text-dark-heading placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-primary-500/50 focus:border-primary-500 transition text-sm"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-dark-text mb-1.5">Deal Value ($)</label>
              <input
                type="number"
                value={form.deal_value}
                onChange={(e) => setForm({ ...form, deal_value: e.target.value })}
                placeholder="5000"
                className="w-full bg-dark-bg border border-dark-border rounded-xl px-4 py-3 text-dark-heading placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-primary-500/50 focus:border-primary-500 transition text-sm"
              />
            </div>
            <div className="col-span-2">
              <label className="block text-sm font-medium text-dark-text mb-1.5">Stage</label>
              <select
                value={form.stage}
                onChange={(e) => setForm({ ...form, stage: e.target.value })}
                className="w-full bg-dark-bg border border-dark-border rounded-xl px-4 py-3 text-dark-heading focus:outline-none focus:ring-2 focus:ring-primary-500/50 focus:border-primary-500 transition text-sm"
              >
                {STAGES.map((s) => (
                  <option key={s} value={s}>{s.charAt(0).toUpperCase() + s.slice(1)}</option>
                ))}
              </select>
            </div>
            <div className="col-span-2">
              <label className="block text-sm font-medium text-dark-text mb-1.5">Notes</label>
              <textarea
                value={form.notes}
                onChange={(e) => setForm({ ...form, notes: e.target.value })}
                placeholder="Any notes about this lead..."
                rows={3}
                className="w-full bg-dark-bg border border-dark-border rounded-xl px-4 py-3 text-dark-heading placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-primary-500/50 focus:border-primary-500 transition text-sm resize-none"
              />
            </div>
          </div>
          <div className="flex gap-3 pt-2">
            <button type="button" onClick={onClose} className="flex-1 border border-dark-border text-dark-text hover:text-dark-heading py-2.5 rounded-xl transition text-sm font-medium">
              Cancel
            </button>
            <button
              type="submit"
              disabled={isLoading}
              className="flex-1 bg-primary-500 hover:bg-primary-600 disabled:bg-primary-500/50 text-white py-2.5 rounded-xl transition text-sm font-medium flex items-center justify-center gap-2"
            >
              {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Plus className="w-4 h-4" />}
              Add Lead
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

function LeadDetailSidebar({ lead, onClose, onUpdated }: { lead: Lead; onClose: () => void; onUpdated: () => void }) {
  const [followup, setFollowup] = useState('')
  const [loadingFollowup, setLoadingFollowup] = useState(false)
  const [sendingFollowup, setSendingFollowup] = useState(false)
  const [channel, setChannel] = useState<'email' | 'whatsapp'>('email')
  const [sent, setSent] = useState(false)

  async function generateFollowup() {
    setLoadingFollowup(true)
    try {
      const res = await crm.generateFollowup(lead.id)
      setFollowup(res.data?.message || res.data?.followup || '')
    } catch { }
    finally { setLoadingFollowup(false) }
  }

  async function sendFollowup() {
    if (!followup.trim()) return
    setSendingFollowup(true)
    try {
      await crm.sendFollowup(lead.id, { channel, message: followup })
      setSent(true)
      setTimeout(() => setSent(false), 3000)
    } catch { }
    finally { setSendingFollowup(false) }
  }

  return (
    <div className="fixed inset-0 z-50 flex justify-end">
      <div className="absolute inset-0 bg-black/40 backdrop-blur-sm" onClick={onClose} />
      <div className="relative bg-dark-card border-l border-dark-border w-full max-w-md h-full overflow-y-auto shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-dark-border sticky top-0 bg-dark-card z-10">
          <h3 className="font-semibold text-dark-heading">Lead Details</h3>
          <button onClick={onClose} className="text-dark-text hover:text-dark-heading transition">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-6 space-y-6">
          {/* Lead info */}
          <div>
            <div className="flex items-start justify-between gap-3 mb-4">
              <div>
                <h4 className="text-xl font-bold text-dark-heading">{lead.name}</h4>
                {lead.company && <p className="text-dark-text">{lead.company}</p>}
              </div>
              <span className={cn('text-xs px-3 py-1 rounded-full font-semibold capitalize', getStatusColor(lead.stage))}>
                {lead.stage}
              </span>
            </div>

            <div className="space-y-2">
              {lead.email && (
                <div className="flex items-center gap-3 text-sm">
                  <Mail className="w-4 h-4 text-dark-text flex-shrink-0" />
                  <a href={`mailto:${lead.email}`} className="text-primary-400 hover:underline">{lead.email}</a>
                </div>
              )}
              {lead.phone && (
                <div className="flex items-center gap-3 text-sm">
                  <Phone className="w-4 h-4 text-dark-text flex-shrink-0" />
                  <a href={`tel:${lead.phone}`} className="text-dark-heading">{lead.phone}</a>
                </div>
              )}
              {lead.deal_value && (
                <div className="flex items-center gap-3 text-sm">
                  <DollarSign className="w-4 h-4 text-dark-text flex-shrink-0" />
                  <span className="text-green-400 font-semibold">{formatCurrency(lead.deal_value)}</span>
                </div>
              )}
              {lead.ai_score !== undefined && lead.ai_score !== null && (
                <div className="flex items-center gap-3 text-sm">
                  <Star className="w-4 h-4 text-dark-text flex-shrink-0" />
                  <span className={cn(
                    'font-semibold',
                    lead.ai_score >= 70 ? 'text-green-400' : lead.ai_score >= 40 ? 'text-yellow-400' : 'text-red-400'
                  )}>
                    AI Score: {lead.ai_score}/100
                  </span>
                </div>
              )}
            </div>

            {lead.notes && (
              <div className="mt-4 bg-dark-bg border border-dark-border rounded-xl p-3">
                <p className="text-xs font-semibold text-dark-text uppercase tracking-wider mb-1.5">Notes</p>
                <p className="text-sm text-dark-heading">{lead.notes}</p>
              </div>
            )}
          </div>

          {/* Follow-up section */}
          <div>
            <h4 className="font-semibold text-dark-heading mb-3 flex items-center gap-2">
              <MessageSquare className="w-4 h-4 text-primary-400" />
              AI Follow-up Message
            </h4>

            <div className="flex gap-2 mb-3">
              {(['email', 'whatsapp'] as const).map((c) => (
                <button
                  key={c}
                  onClick={() => setChannel(c)}
                  className={cn(
                    'flex-1 py-2 rounded-xl text-sm font-medium transition capitalize border',
                    channel === c
                      ? 'bg-primary-500 border-primary-500 text-white'
                      : 'bg-dark-bg border-dark-border text-dark-text hover:text-dark-heading'
                  )}
                >
                  {c}
                </button>
              ))}
            </div>

            <button
              onClick={generateFollowup}
              disabled={loadingFollowup}
              className="w-full flex items-center justify-center gap-2 bg-dark-bg border border-dark-border hover:border-primary-500/50 text-dark-text hover:text-dark-heading py-2.5 rounded-xl text-sm font-medium transition mb-3"
            >
              {loadingFollowup ? <Loader2 className="w-4 h-4 animate-spin" /> : <Bot className="w-4 h-4" />}
              Generate AI Follow-up
            </button>

            {followup && (
              <>
                <textarea
                  value={followup}
                  onChange={(e) => setFollowup(e.target.value)}
                  rows={5}
                  className="w-full bg-dark-bg border border-dark-border rounded-xl px-4 py-3 text-dark-heading focus:outline-none focus:ring-2 focus:ring-primary-500/50 focus:border-primary-500 transition text-sm resize-none mb-3"
                />
                <button
                  onClick={sendFollowup}
                  disabled={sendingFollowup || sent}
                  className="w-full flex items-center justify-center gap-2 bg-green-500/20 hover:bg-green-500/30 border border-green-500/30 text-green-400 py-2.5 rounded-xl text-sm font-medium transition disabled:opacity-50"
                >
                  {sendingFollowup ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
                  {sent ? 'Sent!' : `Send via ${channel.charAt(0).toUpperCase() + channel.slice(1)}`}
                </button>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
