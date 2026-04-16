'use client'

import { useState, useEffect } from 'react'
import { Play, Loader2, Copy, CheckCircle, Scissors, TrendingUp, Video } from 'lucide-react'
import { youtube } from '@/lib/api'
import { cn, formatDate } from '@/lib/utils'

type Tab = 'script' | 'titles' | 'shorts' | 'library'

const STYLES = ['educational', 'entertaining', 'tutorial', 'vlog', 'review', 'documentary']
const NICHES = ['tech', 'finance', 'health', 'fitness', 'marketing', 'cooking', 'travel', 'gaming', 'beauty', 'business']

export default function YouTubePage() {
  const [activeTab, setActiveTab] = useState<Tab>('script')

  const tabs = [
    { id: 'script' as Tab, label: 'Script Generator', icon: Play },
    { id: 'titles' as Tab, label: 'Title Optimizer', icon: TrendingUp },
    { id: 'shorts' as Tab, label: 'Shorts Generator', icon: Scissors },
    { id: 'library' as Tab, label: 'Video Library', icon: Video },
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

      {activeTab === 'script' && <ScriptGenerator />}
      {activeTab === 'titles' && <TitleOptimizer />}
      {activeTab === 'shorts' && <ShortsGenerator />}
      {activeTab === 'library' && <VideoLibrary />}
    </div>
  )
}

function ScriptGenerator() {
  const [form, setForm] = useState({ topic: '', duration_minutes: 10, style: 'educational' })
  const [result, setResult] = useState<any>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')
  const [copied, setCopied] = useState(false)

  async function handleSubmit() {
    if (!form.topic.trim()) { setError('Topic is required'); return }
    setIsLoading(true); setError('')
    try {
      const res = await youtube.generateScript(form)
      setResult(res.data)
    } catch (e: any) {
      setError(e?.response?.data?.detail || 'Failed to generate script')
    } finally { setIsLoading(false) }
  }

  return (
    <div className="bg-dark-card border border-dark-border rounded-2xl p-6">
      <h3 className="font-semibold text-dark-heading text-lg mb-5">YouTube Script Generator</h3>
      {error && <p className="text-red-400 text-sm mb-4 bg-red-500/10 border border-red-500/20 rounded-xl px-3 py-2">{error}</p>}
      <div className="space-y-4 mb-5">
        <div>
          <label className="block text-sm font-medium text-dark-text mb-1.5">Video Topic *</label>
          <input
            type="text"
            value={form.topic}
            onChange={(e) => setForm({ ...form, topic: e.target.value })}
            placeholder="e.g. How to grow a YouTube channel from 0 to 10k subscribers"
            className="w-full bg-dark-bg border border-dark-border rounded-xl px-4 py-3 text-dark-heading placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-primary-500/50 focus:border-primary-500 transition text-sm"
          />
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-dark-text mb-1.5">Duration (minutes)</label>
            <select
              value={form.duration_minutes}
              onChange={(e) => setForm({ ...form, duration_minutes: Number(e.target.value) })}
              className="w-full bg-dark-bg border border-dark-border rounded-xl px-4 py-3 text-dark-heading focus:outline-none focus:ring-2 focus:ring-primary-500/50 focus:border-primary-500 transition text-sm"
            >
              {[5, 8, 10, 12, 15, 20, 30].map((d) => (
                <option key={d} value={d}>{d} min</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-dark-text mb-1.5">Style</label>
            <select
              value={form.style}
              onChange={(e) => setForm({ ...form, style: e.target.value })}
              className="w-full bg-dark-bg border border-dark-border rounded-xl px-4 py-3 text-dark-heading focus:outline-none focus:ring-2 focus:ring-primary-500/50 focus:border-primary-500 transition text-sm"
            >
              {STYLES.map((s) => (
                <option key={s} value={s}>{s.charAt(0).toUpperCase() + s.slice(1)}</option>
              ))}
            </select>
          </div>
        </div>
      </div>
      <button
        onClick={handleSubmit}
        disabled={isLoading}
        className="flex items-center gap-2 bg-primary-500 hover:bg-primary-600 disabled:bg-primary-500/50 text-white px-6 py-2.5 rounded-xl font-medium transition"
      >
        {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
        {isLoading ? 'Generating Script...' : 'Generate Script'}
      </button>

      {result && (
        <div className="mt-6">
          <div className="flex items-center justify-between mb-3">
            <h4 className="font-semibold text-dark-heading">Generated Script</h4>
            <button
              onClick={() => {
                navigator.clipboard.writeText(result.script || result.content || '')
                setCopied(true)
                setTimeout(() => setCopied(false), 2000)
              }}
              className="flex items-center gap-1 text-sm text-primary-400 hover:text-primary-300 transition"
            >
              {copied ? <CheckCircle className="w-4 h-4 text-green-400" /> : <Copy className="w-4 h-4" />}
              {copied ? 'Copied!' : 'Copy Script'}
            </button>
          </div>
          {result.title && (
            <p className="text-base font-bold text-dark-heading mb-3">{result.title}</p>
          )}
          {result.outline && (
            <div className="bg-dark-bg border border-dark-border rounded-xl p-4 mb-4">
              <p className="text-xs font-semibold text-dark-text uppercase tracking-wider mb-2">Outline</p>
              <div className="space-y-1">
                {(Array.isArray(result.outline) ? result.outline : result.outline.split('\n')).map((item: string, i: number) => (
                  <p key={i} className="text-sm text-dark-heading">{item}</p>
                ))}
              </div>
            </div>
          )}
          <div className="bg-dark-bg border border-dark-border rounded-xl p-5 max-h-96 overflow-y-auto">
            <div className="prose-dark text-sm whitespace-pre-wrap">
              {result.script || result.content || result.text || JSON.stringify(result, null, 2)}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

function TitleOptimizer() {
  const [topic, setTopic] = useState('')
  const [niche, setNiche] = useState('tech')
  const [result, setResult] = useState<any>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')

  async function handleSubmit() {
    if (!topic.trim()) { setError('Topic is required'); return }
    setIsLoading(true); setError('')
    try {
      const res = await youtube.optimizeTitle({ topic, niche })
      setResult(res.data)
    } catch (e: any) {
      setError(e?.response?.data?.detail || 'Failed to optimize titles')
    } finally { setIsLoading(false) }
  }

  const titles: any[] = result?.titles || result?.suggestions || []

  return (
    <div className="bg-dark-card border border-dark-border rounded-2xl p-6">
      <h3 className="font-semibold text-dark-heading text-lg mb-5">YouTube Title Optimizer</h3>
      {error && <p className="text-red-400 text-sm mb-4 bg-red-500/10 border border-red-500/20 rounded-xl px-3 py-2">{error}</p>}
      <div className="space-y-4 mb-5">
        <div>
          <label className="block text-sm font-medium text-dark-text mb-1.5">Video Topic *</label>
          <input
            type="text"
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            placeholder="e.g. passive income strategies"
            className="w-full bg-dark-bg border border-dark-border rounded-xl px-4 py-3 text-dark-heading placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-primary-500/50 focus:border-primary-500 transition text-sm"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-dark-text mb-2">Niche</label>
          <div className="flex flex-wrap gap-2">
            {NICHES.map((n) => (
              <button
                key={n}
                onClick={() => setNiche(n)}
                className={cn(
                  'px-3 py-1.5 rounded-xl text-sm font-medium transition capitalize border',
                  niche === n
                    ? 'bg-primary-500 border-primary-500 text-white'
                    : 'bg-dark-bg border-dark-border text-dark-text hover:text-dark-heading'
                )}
              >
                {n}
              </button>
            ))}
          </div>
        </div>
      </div>
      <button
        onClick={handleSubmit}
        disabled={isLoading}
        className="flex items-center gap-2 bg-primary-500 hover:bg-primary-600 disabled:bg-primary-500/50 text-white px-6 py-2.5 rounded-xl font-medium transition"
      >
        {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <TrendingUp className="w-4 h-4" />}
        Generate Titles
      </button>

      {titles.length > 0 && (
        <div className="mt-6">
          <h4 className="font-semibold text-dark-heading mb-4">{titles.length} Title Options</h4>
          <div className="space-y-3">
            {titles.map((item: any, i: number) => {
              const titleText = typeof item === 'string' ? item : item.title || item.text || ''
              const score = item.score || item.ctr_score || null
              return (
                <div key={i} className="flex items-center gap-3 bg-dark-bg border border-dark-border rounded-xl p-4 group hover:border-primary-500/30 transition">
                  <span className="text-sm font-bold text-dark-text w-6 flex-shrink-0">{i + 1}</span>
                  <p className="flex-1 text-sm font-medium text-dark-heading">{titleText}</p>
                  <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition">
                    {score !== null && (
                      <span className={cn(
                        'text-xs px-2 py-0.5 rounded-full font-medium',
                        score >= 80 ? 'bg-green-500/20 text-green-400' :
                        score >= 60 ? 'bg-yellow-500/20 text-yellow-400' :
                        'bg-red-500/20 text-red-400'
                      )}>
                        {score}/100
                      </span>
                    )}
                    <button
                      onClick={() => navigator.clipboard.writeText(titleText)}
                      className="text-dark-text hover:text-dark-heading transition"
                    >
                      <Copy className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}

function ShortsGenerator() {
  const [script, setScript] = useState('')
  const [result, setResult] = useState<any>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')

  async function handleSubmit() {
    if (!script.trim()) { setError('Paste a script to extract shorts'); return }
    setIsLoading(true); setError('')
    try {
      const res = await youtube.generateShorts(script)
      setResult(res.data)
    } catch (e: any) {
      setError(e?.response?.data?.detail || 'Failed to generate shorts')
    } finally { setIsLoading(false) }
  }

  const shorts: any[] = result?.shorts || result?.clips || []

  return (
    <div className="bg-dark-card border border-dark-border rounded-2xl p-6">
      <h3 className="font-semibold text-dark-heading text-lg mb-5">YouTube Shorts Generator</h3>
      <p className="text-dark-text text-sm mb-5">Paste your full video script and AI will extract 3 engaging Shorts clips.</p>
      {error && <p className="text-red-400 text-sm mb-4 bg-red-500/10 border border-red-500/20 rounded-xl px-3 py-2">{error}</p>}
      <textarea
        value={script}
        onChange={(e) => setScript(e.target.value)}
        placeholder="Paste your full video script here..."
        rows={8}
        className="w-full bg-dark-bg border border-dark-border rounded-xl px-4 py-3 text-dark-heading placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-primary-500/50 focus:border-primary-500 transition text-sm resize-none mb-4"
      />
      <button
        onClick={handleSubmit}
        disabled={isLoading}
        className="flex items-center gap-2 bg-primary-500 hover:bg-primary-600 disabled:bg-primary-500/50 text-white px-6 py-2.5 rounded-xl font-medium transition"
      >
        {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Scissors className="w-4 h-4" />}
        Extract Shorts
      </button>

      {shorts.length > 0 && (
        <div className="mt-6">
          <h4 className="font-semibold text-dark-heading mb-4">{shorts.length} Shorts Ideas</h4>
          <div className="grid gap-4">
            {shorts.map((short: any, i: number) => (
              <div key={i} className="bg-dark-bg border border-dark-border rounded-xl p-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-bold text-primary-400">Short #{i + 1}</span>
                  {short.duration && <span className="text-xs text-dark-text">{short.duration}</span>}
                  <button
                    onClick={() => navigator.clipboard.writeText(short.content || short.script || '')}
                    className="text-dark-text hover:text-dark-heading transition"
                  >
                    <Copy className="w-4 h-4" />
                  </button>
                </div>
                {short.title && <p className="font-semibold text-dark-heading text-sm mb-2">{short.title}</p>}
                <p className="text-sm text-dark-text whitespace-pre-wrap">{short.content || short.script || ''}</p>
                {short.hook && (
                  <div className="mt-2 text-xs bg-yellow-500/10 border border-yellow-500/20 text-yellow-400 px-3 py-1.5 rounded-lg">
                    Hook: {short.hook}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

function VideoLibrary() {
  const [videos, setVideos] = useState<any[]>([])
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    youtube.listVideos()
      .then((res) => setVideos(res.data?.videos || res.data || []))
      .catch(() => { })
      .finally(() => setIsLoading(false))
  }, [])

  return (
    <div className="bg-dark-card border border-dark-border rounded-2xl p-6">
      <h3 className="font-semibold text-dark-heading text-lg mb-4">Video Library</h3>
      {isLoading ? (
        <div className="grid gap-3">
          {[...Array(4)].map((_, i) => <div key={i} className="h-20 bg-dark-bg rounded-xl animate-pulse" />)}
        </div>
      ) : videos.length === 0 ? (
        <div className="text-center py-12">
          <Video className="w-12 h-12 mx-auto text-slate-600 mb-3" />
          <p className="text-dark-heading font-medium">No videos yet</p>
          <p className="text-dark-text text-sm mt-1">Generate scripts or optimize titles to see them here</p>
        </div>
      ) : (
        <div className="grid gap-3">
          {videos.map((video, i) => (
            <div key={video.id || i} className="bg-dark-bg border border-dark-border rounded-xl p-4">
              <p className="font-medium text-dark-heading">{video.title || video.topic || 'Untitled'}</p>
              <div className="flex items-center gap-3 mt-1.5">
                {video.duration && <span className="text-xs text-dark-text">{video.duration} min</span>}
                {video.style && <span className="text-xs text-dark-text capitalize">{video.style}</span>}
                <span className="text-xs text-dark-text">{formatDate(video.created_at)}</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
