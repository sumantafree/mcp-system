'use client'

import { useState } from 'react'
import { Search, Copy, CheckCircle, Loader2, Tag, Link2, FileSearch, Database } from 'lucide-react'
import { seo } from '@/lib/api'
import { cn } from '@/lib/utils'

type Tab = 'cluster' | 'meta' | 'links' | 'audit' | 'keywords'

export default function SeoPage() {
  const [activeTab, setActiveTab] = useState<Tab>('cluster')

  const tabs = [
    { id: 'cluster' as Tab, label: 'Keyword Clustering', icon: Tag },
    { id: 'meta' as Tab, label: 'Meta Generator', icon: Search },
    { id: 'links' as Tab, label: 'Internal Links', icon: Link2 },
    { id: 'audit' as Tab, label: 'Content Audit', icon: FileSearch },
    { id: 'keywords' as Tab, label: 'Saved Keywords', icon: Database },
  ]

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Tabs */}
      <div className="flex overflow-x-auto gap-1 bg-dark-card border border-dark-border rounded-2xl p-1">
        {tabs.map((tab) => {
          const Icon = tab.icon
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={cn(
                'flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium transition whitespace-nowrap flex-shrink-0',
                activeTab === tab.id
                  ? 'bg-primary-500 text-white'
                  : 'text-dark-text hover:text-dark-heading'
              )}
            >
              <Icon className="w-4 h-4" />
              {tab.label}
            </button>
          )
        })}
      </div>

      {/* Tab content */}
      {activeTab === 'cluster' && <KeywordCluster />}
      {activeTab === 'meta' && <MetaGenerator />}
      {activeTab === 'links' && <InternalLinks />}
      {activeTab === 'audit' && <ContentAudit />}
      {activeTab === 'keywords' && <SavedKeywords />}
    </div>
  )
}

function KeywordCluster() {
  const [input, setInput] = useState('')
  const [result, setResult] = useState<any>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')

  async function handleSubmit() {
    const keywords = input.split('\n').map((k) => k.trim()).filter(Boolean)
    if (keywords.length < 2) { setError('Enter at least 2 keywords'); return }
    setIsLoading(true); setError('')
    try {
      const res = await seo.clusterKeywords(keywords)
      setResult(res.data)
    } catch (e: any) {
      setError(e?.response?.data?.detail || 'Failed to cluster keywords')
    } finally { setIsLoading(false) }
  }

  return (
    <div className="bg-dark-card border border-dark-border rounded-2xl p-6">
      <h3 className="font-semibold text-dark-heading text-lg mb-4">Keyword Clustering</h3>
      <p className="text-dark-text text-sm mb-5">Enter keywords (one per line) to automatically cluster them by topic.</p>
      {error && <p className="text-red-400 text-sm mb-4 bg-red-500/10 border border-red-500/20 rounded-xl px-3 py-2">{error}</p>}
      <textarea
        value={input}
        onChange={(e) => setInput(e.target.value)}
        placeholder="best seo tools&#10;keyword research&#10;on page optimization&#10;link building strategies&#10;..."
        rows={8}
        className="w-full bg-dark-bg border border-dark-border rounded-xl px-4 py-3 text-dark-heading placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-primary-500/50 focus:border-primary-500 transition text-sm resize-none mb-4"
      />
      <button
        onClick={handleSubmit}
        disabled={isLoading}
        className="flex items-center gap-2 bg-primary-500 hover:bg-primary-600 disabled:bg-primary-500/50 text-white px-6 py-2.5 rounded-xl font-medium transition"
      >
        {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Tag className="w-4 h-4" />}
        Cluster Keywords
      </button>

      {result && (
        <div className="mt-6">
          <h4 className="font-semibold text-dark-heading mb-4">Clusters</h4>
          <div className="grid gap-4">
            {Array.isArray(result.clusters)
              ? result.clusters.map((cluster: any, i: number) => (
                <div key={i} className="bg-dark-bg border border-dark-border rounded-xl p-4">
                  <p className="font-medium text-primary-400 mb-2">{cluster.topic || cluster.name || `Cluster ${i + 1}`}</p>
                  <div className="flex flex-wrap gap-2">
                    {(cluster.keywords || cluster.items || []).map((kw: string, j: number) => (
                      <span key={j} className="text-xs bg-dark-card border border-dark-border text-dark-text px-2 py-1 rounded-lg">
                        {kw}
                      </span>
                    ))}
                  </div>
                </div>
              ))
              : (
                <div className="bg-dark-bg border border-dark-border rounded-xl p-4">
                  <pre className="text-sm text-dark-text whitespace-pre-wrap">{JSON.stringify(result, null, 2)}</pre>
                </div>
              )
            }
          </div>
        </div>
      )}
    </div>
  )
}

function MetaGenerator() {
  const [form, setForm] = useState({ title: '', description: '', keyword: '' })
  const [result, setResult] = useState<any>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')
  const [copied, setCopied] = useState<string | null>(null)

  async function handleSubmit() {
    if (!form.title || !form.keyword) { setError('Title and keyword are required'); return }
    setIsLoading(true); setError('')
    try {
      const res = await seo.generateMeta(form)
      setResult(res.data)
    } catch (e: any) {
      setError(e?.response?.data?.detail || 'Failed to generate meta tags')
    } finally { setIsLoading(false) }
  }

  function copyToClipboard(text: string, key: string) {
    navigator.clipboard.writeText(text)
    setCopied(key)
    setTimeout(() => setCopied(null), 2000)
  }

  return (
    <div className="bg-dark-card border border-dark-border rounded-2xl p-6">
      <h3 className="font-semibold text-dark-heading text-lg mb-4">Meta Tag Generator</h3>
      {error && <p className="text-red-400 text-sm mb-4 bg-red-500/10 border border-red-500/20 rounded-xl px-3 py-2">{error}</p>}
      <div className="space-y-4 mb-5">
        <div>
          <label className="block text-sm font-medium text-dark-text mb-1.5">Page Title *</label>
          <input
            type="text"
            value={form.title}
            onChange={(e) => setForm({ ...form, title: e.target.value })}
            placeholder="e.g. Best SEO Tools for 2025"
            className="w-full bg-dark-bg border border-dark-border rounded-xl px-4 py-3 text-dark-heading placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-primary-500/50 focus:border-primary-500 transition text-sm"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-dark-text mb-1.5">Page Description</label>
          <textarea
            value={form.description}
            onChange={(e) => setForm({ ...form, description: e.target.value })}
            placeholder="Brief description of the page..."
            rows={3}
            className="w-full bg-dark-bg border border-dark-border rounded-xl px-4 py-3 text-dark-heading placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-primary-500/50 focus:border-primary-500 transition text-sm resize-none"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-dark-text mb-1.5">Target Keyword *</label>
          <input
            type="text"
            value={form.keyword}
            onChange={(e) => setForm({ ...form, keyword: e.target.value })}
            placeholder="e.g. seo tools"
            className="w-full bg-dark-bg border border-dark-border rounded-xl px-4 py-3 text-dark-heading placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-primary-500/50 focus:border-primary-500 transition text-sm"
          />
        </div>
      </div>
      <button
        onClick={handleSubmit}
        disabled={isLoading}
        className="flex items-center gap-2 bg-primary-500 hover:bg-primary-600 disabled:bg-primary-500/50 text-white px-6 py-2.5 rounded-xl font-medium transition"
      >
        {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
        Generate Meta Tags
      </button>

      {result && (
        <div className="mt-6 space-y-4">
          {Object.entries(result).map(([key, value]) => typeof value === 'string' && (
            <div key={key} className="bg-dark-bg border border-dark-border rounded-xl p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-semibold text-primary-400 uppercase tracking-wider">{key.replace(/_/g, ' ')}</span>
                <button
                  onClick={() => copyToClipboard(value, key)}
                  className="flex items-center gap-1 text-xs text-dark-text hover:text-dark-heading transition"
                >
                  {copied === key ? <CheckCircle className="w-4 h-4 text-green-400" /> : <Copy className="w-4 h-4" />}
                  {copied === key ? 'Copied!' : 'Copy'}
                </button>
              </div>
              <p className="text-sm text-dark-heading">{value}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

function InternalLinks() {
  const [pageTitle, setPageTitle] = useState('')
  const [existingPages, setExistingPages] = useState('')
  const [result, setResult] = useState<any>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')

  async function handleSubmit() {
    if (!pageTitle) { setError('Page title is required'); return }
    setIsLoading(true); setError('')
    try {
      const pages = existingPages.split('\n').map((p) => p.trim()).filter(Boolean)
      const res = await seo.suggestLinks({ page_title: pageTitle, existing_pages: pages })
      setResult(res.data)
    } catch (e: any) {
      setError(e?.response?.data?.detail || 'Failed to get link suggestions')
    } finally { setIsLoading(false) }
  }

  return (
    <div className="bg-dark-card border border-dark-border rounded-2xl p-6">
      <h3 className="font-semibold text-dark-heading text-lg mb-4">Internal Link Suggestions</h3>
      {error && <p className="text-red-400 text-sm mb-4 bg-red-500/10 border border-red-500/20 rounded-xl px-3 py-2">{error}</p>}
      <div className="space-y-4 mb-5">
        <div>
          <label className="block text-sm font-medium text-dark-text mb-1.5">Current Page Title *</label>
          <input
            type="text"
            value={pageTitle}
            onChange={(e) => setPageTitle(e.target.value)}
            placeholder="e.g. Complete Guide to SEO in 2025"
            className="w-full bg-dark-bg border border-dark-border rounded-xl px-4 py-3 text-dark-heading placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-primary-500/50 focus:border-primary-500 transition text-sm"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-dark-text mb-1.5">Existing Pages (one per line)</label>
          <textarea
            value={existingPages}
            onChange={(e) => setExistingPages(e.target.value)}
            placeholder="Keyword Research Tips&#10;On-Page SEO Guide&#10;Link Building Strategies"
            rows={5}
            className="w-full bg-dark-bg border border-dark-border rounded-xl px-4 py-3 text-dark-heading placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-primary-500/50 focus:border-primary-500 transition text-sm resize-none"
          />
        </div>
      </div>
      <button
        onClick={handleSubmit}
        disabled={isLoading}
        className="flex items-center gap-2 bg-primary-500 hover:bg-primary-600 disabled:bg-primary-500/50 text-white px-6 py-2.5 rounded-xl font-medium transition"
      >
        {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Link2 className="w-4 h-4" />}
        Get Suggestions
      </button>

      {result && (
        <div className="mt-6">
          <h4 className="font-semibold text-dark-heading mb-3">Suggested Links</h4>
          <div className="space-y-2">
            {(result.suggestions || result.links || [result]).map((s: any, i: number) => (
              <div key={i} className="bg-dark-bg border border-dark-border rounded-xl p-3">
                <p className="text-sm text-primary-400 font-medium">{s.anchor_text || s.page || s}</p>
                {s.reason && <p className="text-xs text-dark-text mt-1">{s.reason}</p>}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

function ContentAudit() {
  const [content, setContent] = useState('')
  const [keyword, setKeyword] = useState('')
  const [result, setResult] = useState<any>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')

  async function handleSubmit() {
    if (!content || !keyword) { setError('Content and keyword are required'); return }
    setIsLoading(true); setError('')
    try {
      const res = await seo.auditContent({ content, keyword })
      setResult(res.data)
    } catch (e: any) {
      setError(e?.response?.data?.detail || 'Failed to audit content')
    } finally { setIsLoading(false) }
  }

  const score = result?.score || result?.seo_score || 0

  return (
    <div className="bg-dark-card border border-dark-border rounded-2xl p-6">
      <h3 className="font-semibold text-dark-heading text-lg mb-4">Content SEO Audit</h3>
      {error && <p className="text-red-400 text-sm mb-4 bg-red-500/10 border border-red-500/20 rounded-xl px-3 py-2">{error}</p>}
      <div className="space-y-4 mb-5">
        <div>
          <label className="block text-sm font-medium text-dark-text mb-1.5">Target Keyword *</label>
          <input
            type="text"
            value={keyword}
            onChange={(e) => setKeyword(e.target.value)}
            placeholder="e.g. seo optimization"
            className="w-full bg-dark-bg border border-dark-border rounded-xl px-4 py-3 text-dark-heading placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-primary-500/50 focus:border-primary-500 transition text-sm"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-dark-text mb-1.5">Content to Audit *</label>
          <textarea
            value={content}
            onChange={(e) => setContent(e.target.value)}
            placeholder="Paste your article content here..."
            rows={8}
            className="w-full bg-dark-bg border border-dark-border rounded-xl px-4 py-3 text-dark-heading placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-primary-500/50 focus:border-primary-500 transition text-sm resize-none"
          />
        </div>
      </div>
      <button
        onClick={handleSubmit}
        disabled={isLoading}
        className="flex items-center gap-2 bg-primary-500 hover:bg-primary-600 disabled:bg-primary-500/50 text-white px-6 py-2.5 rounded-xl font-medium transition"
      >
        {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <FileSearch className="w-4 h-4" />}
        Audit Content
      </button>

      {result && (
        <div className="mt-6 space-y-4">
          {/* Score */}
          <div className="flex items-center gap-4 bg-dark-bg border border-dark-border rounded-xl p-4">
            <div className={cn(
              'w-16 h-16 rounded-full border-4 flex items-center justify-center text-xl font-bold',
              score >= 80 ? 'border-green-500 text-green-400' :
              score >= 60 ? 'border-yellow-500 text-yellow-400' :
              'border-red-500 text-red-400'
            )}>
              {score}
            </div>
            <div>
              <p className="font-semibold text-dark-heading">SEO Score</p>
              <p className="text-sm text-dark-text">
                {score >= 80 ? 'Great!' : score >= 60 ? 'Needs improvement' : 'Needs significant work'}
              </p>
            </div>
          </div>

          {/* Issues */}
          {(result.issues || result.recommendations || []).length > 0 && (
            <div>
              <h4 className="font-semibold text-dark-heading mb-3">Issues & Recommendations</h4>
              <div className="space-y-2">
                {(result.issues || result.recommendations || []).map((issue: any, i: number) => (
                  <div key={i} className="flex items-start gap-3 bg-dark-bg border border-dark-border rounded-xl p-3">
                    <div className={cn(
                      'w-2 h-2 rounded-full mt-1.5 flex-shrink-0',
                      issue.type === 'error' ? 'bg-red-500' :
                      issue.type === 'warning' ? 'bg-yellow-500' : 'bg-blue-500'
                    )} />
                    <p className="text-sm text-dark-heading">{issue.message || issue}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

function SavedKeywords() {
  const [keywords, setKeywords] = useState<any[]>([])
  const [isLoading, setIsLoading] = useState(true)

  useState(() => {
    seo.listKeywords()
      .then((res) => { setKeywords(res.data?.keywords || res.data || []) })
      .catch(() => { })
      .finally(() => setIsLoading(false))
  })

  return (
    <div className="bg-dark-card border border-dark-border rounded-2xl p-6">
      <h3 className="font-semibold text-dark-heading text-lg mb-4">Saved Keywords</h3>
      {isLoading ? (
        <div className="space-y-2">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="h-12 bg-dark-bg rounded-xl animate-pulse" />
          ))}
        </div>
      ) : keywords.length === 0 ? (
        <div className="text-center py-12">
          <Database className="w-12 h-12 mx-auto text-slate-600 mb-3" />
          <p className="text-dark-heading font-medium">No saved keywords</p>
          <p className="text-dark-text text-sm mt-1">Keywords you cluster or audit will appear here</p>
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-dark-border">
                <th className="text-left py-3 px-4 text-xs font-semibold text-dark-text uppercase tracking-wider">Keyword</th>
                <th className="text-left py-3 px-4 text-xs font-semibold text-dark-text uppercase tracking-wider">Cluster</th>
                <th className="text-left py-3 px-4 text-xs font-semibold text-dark-text uppercase tracking-wider">Volume</th>
                <th className="text-left py-3 px-4 text-xs font-semibold text-dark-text uppercase tracking-wider">Difficulty</th>
              </tr>
            </thead>
            <tbody>
              {keywords.map((kw, i) => (
                <tr key={i} className="border-b border-dark-border/50 hover:bg-dark-bg/50 transition">
                  <td className="py-3 px-4 text-sm text-dark-heading">{kw.keyword || kw.term || kw}</td>
                  <td className="py-3 px-4 text-sm text-dark-text">{kw.cluster || kw.topic || '—'}</td>
                  <td className="py-3 px-4 text-sm text-dark-text">{kw.volume || '—'}</td>
                  <td className="py-3 px-4">
                    <span className={cn(
                      'text-xs px-2 py-0.5 rounded-full font-medium',
                      (kw.difficulty || 0) >= 70 ? 'bg-red-500/20 text-red-400' :
                      (kw.difficulty || 0) >= 40 ? 'bg-yellow-500/20 text-yellow-400' :
                      'bg-green-500/20 text-green-400'
                    )}>
                      {kw.difficulty || '—'}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
