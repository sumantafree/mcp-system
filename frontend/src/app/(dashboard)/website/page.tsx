'use client'

import { useEffect, useState } from 'react'
import { Globe, Loader2, AlertTriangle, CheckCircle, XCircle, Zap, FileCode, History, ExternalLink } from 'lucide-react'
import { website } from '@/lib/api'
import { cn, formatDate, truncate } from '@/lib/utils'

type Tab = 'scanner' | 'performance' | 'generator' | 'history'

export default function WebsitePage() {
  const [activeTab, setActiveTab] = useState<Tab>('scanner')

  const tabs = [
    { id: 'scanner' as Tab, label: 'Link Scanner', icon: Globe },
    { id: 'performance' as Tab, label: 'Performance', icon: Zap },
    { id: 'generator' as Tab, label: 'Page Generator', icon: FileCode },
    { id: 'history' as Tab, label: 'Scan History', icon: History },
  ]

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex overflow-x-auto gap-1 bg-dark-card border border-dark-border rounded-2xl p-1">
        {tabs.map((tab) => {
          const Icon = tab.icon
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={cn(
                'flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium transition whitespace-nowrap flex-shrink-0',
                activeTab === tab.id ? 'bg-primary-500 text-white' : 'text-dark-text hover:text-dark-heading'
              )}
            >
              <Icon className="w-4 h-4" />
              {tab.label}
            </button>
          )
        })}
      </div>

      {activeTab === 'scanner' && <LinkScanner />}
      {activeTab === 'performance' && <PerformanceAnalyzer />}
      {activeTab === 'generator' && <PageGenerator />}
      {activeTab === 'history' && <ScanHistory />}
    </div>
  )
}

function LinkScanner() {
  const [url, setUrl] = useState('')
  const [result, setResult] = useState<any>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')

  async function handleScan() {
    if (!url.trim()) { setError('URL is required'); return }
    setIsLoading(true); setError('')
    try {
      const res = await website.scanWebsite(url.trim())
      setResult(res.data)
    } catch (e: any) {
      setError(e?.response?.data?.detail || 'Failed to scan website')
    } finally { setIsLoading(false) }
  }

  const links: any[] = result?.broken_links || result?.links || []
  const brokenCount = links.filter((l) => l.status >= 400 || l.status === 0 || l.is_broken).length

  return (
    <div className="bg-dark-card border border-dark-border rounded-2xl p-6">
      <h3 className="font-semibold text-dark-heading text-lg mb-5">Website Link Scanner</h3>
      {error && <p className="text-red-400 text-sm mb-4 bg-red-500/10 border border-red-500/20 rounded-xl px-3 py-2">{error}</p>}
      <div className="flex gap-3 mb-5">
        <input
          type="url"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleScan()}
          placeholder="https://example.com"
          className="flex-1 bg-dark-bg border border-dark-border rounded-xl px-4 py-3 text-dark-heading placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-primary-500/50 focus:border-primary-500 transition text-sm"
        />
        <button
          onClick={handleScan}
          disabled={isLoading}
          className="flex items-center gap-2 bg-primary-500 hover:bg-primary-600 disabled:bg-primary-500/50 text-white px-6 py-3 rounded-xl font-medium transition"
        >
          {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Globe className="w-4 h-4" />}
          {isLoading ? 'Scanning...' : 'Scan'}
        </button>
      </div>

      {result && (
        <div className="space-y-4">
          {/* Summary */}
          <div className="grid grid-cols-3 gap-4">
            <div className="bg-dark-bg border border-dark-border rounded-xl p-4 text-center">
              <p className="text-2xl font-bold text-dark-heading">{result.total_links || links.length}</p>
              <p className="text-xs text-dark-text mt-1">Total Links</p>
            </div>
            <div className={cn('border rounded-xl p-4 text-center', brokenCount > 0 ? 'bg-red-500/10 border-red-500/20' : 'bg-dark-bg border-dark-border')}>
              <p className={cn('text-2xl font-bold', brokenCount > 0 ? 'text-red-400' : 'text-dark-heading')}>{brokenCount}</p>
              <p className="text-xs text-dark-text mt-1">Broken Links</p>
            </div>
            <div className="bg-green-500/10 border border-green-500/20 rounded-xl p-4 text-center">
              <p className="text-2xl font-bold text-green-400">{(result.total_links || links.length) - brokenCount}</p>
              <p className="text-xs text-dark-text mt-1">Working Links</p>
            </div>
          </div>

          {/* Links table */}
          {links.length > 0 && (
            <div>
              <h4 className="font-semibold text-dark-heading mb-3">
                {brokenCount > 0 ? `Broken Links (${brokenCount})` : 'All Links'}
              </h4>
              <div className="space-y-2 max-h-80 overflow-y-auto">
                {links.map((link, i) => {
                  const isBroken = link.status >= 400 || link.status === 0 || link.is_broken
                  return (
                    <div
                      key={i}
                      className={cn(
                        'flex items-center gap-3 p-3 rounded-xl border text-sm',
                        isBroken ? 'bg-red-500/5 border-red-500/20' : 'bg-dark-bg border-dark-border'
                      )}
                    >
                      {isBroken ? (
                        <XCircle className="w-4 h-4 text-red-400 flex-shrink-0" />
                      ) : (
                        <CheckCircle className="w-4 h-4 text-green-400 flex-shrink-0" />
                      )}
                      <span className="flex-1 truncate text-dark-heading">{link.url || link.href || link}</span>
                      <span className={cn(
                        'text-xs font-mono px-2 py-0.5 rounded',
                        link.status >= 500 ? 'bg-red-500/20 text-red-400' :
                        link.status >= 400 ? 'bg-orange-500/20 text-orange-400' :
                        link.status >= 300 ? 'bg-yellow-500/20 text-yellow-400' :
                        'bg-green-500/20 text-green-400'
                      )}>
                        {link.status || 'N/A'}
                      </span>
                    </div>
                  )
                })}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

function PerformanceAnalyzer() {
  const [url, setUrl] = useState('')
  const [result, setResult] = useState<any>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')

  async function handleAnalyze() {
    if (!url.trim()) { setError('URL is required'); return }
    setIsLoading(true); setError('')
    try {
      const res = await website.analyzePerformance(url.trim())
      setResult(res.data)
    } catch (e: any) {
      setError(e?.response?.data?.detail || 'Failed to analyze performance')
    } finally { setIsLoading(false) }
  }

  function getScoreColor(score: number) {
    if (score >= 90) return 'text-green-400 border-green-500'
    if (score >= 50) return 'text-yellow-400 border-yellow-500'
    return 'text-red-400 border-red-500'
  }

  return (
    <div className="bg-dark-card border border-dark-border rounded-2xl p-6">
      <h3 className="font-semibold text-dark-heading text-lg mb-5">Performance Analyzer</h3>
      {error && <p className="text-red-400 text-sm mb-4 bg-red-500/10 border border-red-500/20 rounded-xl px-3 py-2">{error}</p>}
      <div className="flex gap-3 mb-5">
        <input
          type="url"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="https://example.com"
          className="flex-1 bg-dark-bg border border-dark-border rounded-xl px-4 py-3 text-dark-heading placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-primary-500/50 focus:border-primary-500 transition text-sm"
        />
        <button
          onClick={handleAnalyze}
          disabled={isLoading}
          className="flex items-center gap-2 bg-primary-500 hover:bg-primary-600 disabled:bg-primary-500/50 text-white px-6 py-3 rounded-xl font-medium transition"
        >
          {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Zap className="w-4 h-4" />}
          {isLoading ? 'Analyzing...' : 'Analyze'}
        </button>
      </div>

      {result && (
        <div className="space-y-4">
          {/* Score circles */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[
              { label: 'Performance', value: result.performance_score || result.performance || 0 },
              { label: 'Accessibility', value: result.accessibility_score || result.accessibility || 0 },
              { label: 'Best Practices', value: result.best_practices_score || result.best_practices || 0 },
              { label: 'SEO', value: result.seo_score || result.seo || 0 },
            ].map((metric) => (
              <div key={metric.label} className="bg-dark-bg border border-dark-border rounded-xl p-4 flex flex-col items-center">
                <div className={cn('w-16 h-16 rounded-full border-4 flex items-center justify-center text-xl font-bold mb-2', getScoreColor(metric.value))}>
                  {metric.value}
                </div>
                <p className="text-xs text-dark-text text-center">{metric.label}</p>
              </div>
            ))}
          </div>

          {/* Metrics */}
          {result.metrics && (
            <div>
              <h4 className="font-semibold text-dark-heading mb-3">Core Web Vitals</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {Object.entries(result.metrics).map(([key, value]) => (
                  <div key={key} className="flex items-center justify-between bg-dark-bg border border-dark-border rounded-xl p-3">
                    <span className="text-sm text-dark-text capitalize">{key.replace(/_/g, ' ')}</span>
                    <span className="text-sm font-medium text-dark-heading">{String(value)}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Opportunities */}
          {result.opportunities && result.opportunities.length > 0 && (
            <div>
              <h4 className="font-semibold text-dark-heading mb-3">Opportunities</h4>
              <div className="space-y-2">
                {result.opportunities.map((opp: any, i: number) => (
                  <div key={i} className="flex items-start gap-3 bg-dark-bg border border-dark-border rounded-xl p-3">
                    <AlertTriangle className="w-4 h-4 text-yellow-400 flex-shrink-0 mt-0.5" />
                    <div>
                      <p className="text-sm font-medium text-dark-heading">{opp.title || opp}</p>
                      {opp.description && <p className="text-xs text-dark-text mt-0.5">{opp.description}</p>}
                    </div>
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

function PageGenerator() {
  const [form, setForm] = useState({ keyword: '', page_type: 'landing' })
  const [result, setResult] = useState<any>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')

  const PAGE_TYPES = ['landing', 'about', 'service', 'blog', 'contact', 'faq', 'product']

  async function handleGenerate() {
    if (!form.keyword.trim()) { setError('Keyword is required'); return }
    setIsLoading(true); setError('')
    try {
      const res = await website.generatePage(form)
      setResult(res.data)
    } catch (e: any) {
      setError(e?.response?.data?.detail || 'Failed to generate page')
    } finally { setIsLoading(false) }
  }

  return (
    <div className="bg-dark-card border border-dark-border rounded-2xl p-6">
      <h3 className="font-semibold text-dark-heading text-lg mb-5">Page Content Generator</h3>
      {error && <p className="text-red-400 text-sm mb-4 bg-red-500/10 border border-red-500/20 rounded-xl px-3 py-2">{error}</p>}
      <div className="space-y-4 mb-5">
        <div>
          <label className="block text-sm font-medium text-dark-text mb-1.5">Focus Keyword *</label>
          <input
            type="text"
            value={form.keyword}
            onChange={(e) => setForm({ ...form, keyword: e.target.value })}
            placeholder="e.g. digital marketing agency"
            className="w-full bg-dark-bg border border-dark-border rounded-xl px-4 py-3 text-dark-heading placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-primary-500/50 focus:border-primary-500 transition text-sm"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-dark-text mb-2">Page Type</label>
          <div className="flex flex-wrap gap-2">
            {PAGE_TYPES.map((t) => (
              <button
                key={t}
                onClick={() => setForm({ ...form, page_type: t })}
                className={cn(
                  'px-4 py-2 rounded-xl text-sm font-medium transition capitalize border',
                  form.page_type === t
                    ? 'bg-primary-500 border-primary-500 text-white'
                    : 'bg-dark-bg border-dark-border text-dark-text hover:text-dark-heading'
                )}
              >
                {t}
              </button>
            ))}
          </div>
        </div>
      </div>
      <button
        onClick={handleGenerate}
        disabled={isLoading}
        className="flex items-center gap-2 bg-primary-500 hover:bg-primary-600 disabled:bg-primary-500/50 text-white px-6 py-2.5 rounded-xl font-medium transition"
      >
        {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <FileCode className="w-4 h-4" />}
        {isLoading ? 'Generating...' : 'Generate Page'}
      </button>

      {result && (
        <div className="mt-6">
          <h4 className="font-semibold text-dark-heading mb-4">Generated Page Content</h4>
          {result.title && (
            <h2 className="text-xl font-bold text-dark-heading mb-3">{result.title}</h2>
          )}
          {result.meta_description && (
            <p className="text-sm text-dark-text italic mb-4 bg-dark-bg border border-dark-border rounded-xl px-4 py-2">
              Meta: {result.meta_description}
            </p>
          )}
          <div className="bg-dark-bg border border-dark-border rounded-xl p-5 max-h-96 overflow-y-auto">
            <div className="prose-dark text-sm whitespace-pre-wrap">
              {result.content || result.html || result.text || JSON.stringify(result, null, 2)}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

function ScanHistory() {
  const [scans, setScans] = useState<any[]>([])
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    website.listScans()
      .then((res) => setScans(res.data?.scans || res.data || []))
      .catch(() => { })
      .finally(() => setIsLoading(false))
  }, [])

  return (
    <div className="bg-dark-card border border-dark-border rounded-2xl p-6">
      <h3 className="font-semibold text-dark-heading text-lg mb-4">Scan History</h3>
      {isLoading ? (
        <div className="space-y-3">
          {[...Array(4)].map((_, i) => <div key={i} className="h-20 bg-dark-bg rounded-xl animate-pulse" />)}
        </div>
      ) : scans.length === 0 ? (
        <div className="text-center py-12">
          <History className="w-12 h-12 mx-auto text-slate-600 mb-3" />
          <p className="text-dark-heading font-medium">No scans yet</p>
          <p className="text-dark-text text-sm mt-1">Scan your website to see the history here</p>
        </div>
      ) : (
        <div className="space-y-3">
          {scans.map((scan, i) => (
            <div key={scan.id || i} className="bg-dark-bg border border-dark-border rounded-xl p-4">
              <div className="flex items-center justify-between">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <a href={scan.url} target="_blank" rel="noopener noreferrer" className="text-sm font-medium text-primary-400 hover:underline flex items-center gap-1 truncate">
                      {scan.url}
                      <ExternalLink className="w-3 h-3 flex-shrink-0" />
                    </a>
                  </div>
                  <p className="text-xs text-dark-text mt-1">{formatDate(scan.created_at)}</p>
                </div>
                <div className="flex items-center gap-4 ml-4">
                  {scan.broken_count !== undefined && (
                    <div className="text-center">
                      <p className={cn('text-sm font-bold', scan.broken_count > 0 ? 'text-red-400' : 'text-green-400')}>
                        {scan.broken_count}
                      </p>
                      <p className="text-xs text-dark-text">broken</p>
                    </div>
                  )}
                  {scan.total_links !== undefined && (
                    <div className="text-center">
                      <p className="text-sm font-bold text-dark-heading">{scan.total_links}</p>
                      <p className="text-xs text-dark-text">total</p>
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
