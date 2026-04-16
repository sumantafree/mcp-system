'use client'

import { useState, useEffect } from 'react'
import { FileText, Loader2, Copy, CheckCircle, RefreshCw, BookOpen, Newspaper, MessageSquare, Library } from 'lucide-react'
import { content as contentApi } from '@/lib/api'
import { cn, getStatusColor, formatDate, truncate } from '@/lib/utils'

type Tab = 'blog' | 'rewrite' | 'captions' | 'library'

export default function ContentPage() {
  const [activeTab, setActiveTab] = useState<Tab>('blog')

  const tabs = [
    { id: 'blog' as Tab, label: 'Blog Generator', icon: BookOpen },
    { id: 'rewrite' as Tab, label: 'News Rewriter', icon: Newspaper },
    { id: 'captions' as Tab, label: 'Social Captions', icon: MessageSquare },
    { id: 'library' as Tab, label: 'Content Library', icon: Library },
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

      {activeTab === 'blog' && <BlogGenerator />}
      {activeTab === 'rewrite' && <NewsRewriter />}
      {activeTab === 'captions' && <SocialCaptions />}
      {activeTab === 'library' && <ContentLibrary />}
    </div>
  )
}

function BlogGenerator() {
  const [form, setForm] = useState({ topic: '', keyword: '', language: 'EN', word_count: 1000 })
  const [result, setResult] = useState<any>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')
  const [copied, setCopied] = useState(false)

  async function handleSubmit() {
    if (!form.topic || !form.keyword) { setError('Topic and keyword are required'); return }
    setIsLoading(true); setError('')
    try {
      const res = await contentApi.generateBlog({
        topic: form.topic,
        keyword: form.keyword,
        language: form.language,
        word_count: form.word_count,
      })
      setResult(res.data)
    } catch (e: any) {
      setError(e?.response?.data?.detail || 'Failed to generate blog')
    } finally { setIsLoading(false) }
  }

  function copyContent() {
    const text = result?.content || result?.blog || result?.text || ''
    navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="bg-dark-card border border-dark-border rounded-2xl p-6">
      <h3 className="font-semibold text-dark-heading text-lg mb-5">AI Blog Generator</h3>
      {error && <p className="text-red-400 text-sm mb-4 bg-red-500/10 border border-red-500/20 rounded-xl px-3 py-2">{error}</p>}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-5">
        <div className="md:col-span-2">
          <label className="block text-sm font-medium text-dark-text mb-1.5">Blog Topic *</label>
          <input
            type="text"
            value={form.topic}
            onChange={(e) => setForm({ ...form, topic: e.target.value })}
            placeholder="e.g. Top 10 SEO Strategies for Small Businesses in 2025"
            className="w-full bg-dark-bg border border-dark-border rounded-xl px-4 py-3 text-dark-heading placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-primary-500/50 focus:border-primary-500 transition text-sm"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-dark-text mb-1.5">Focus Keyword *</label>
          <input
            type="text"
            value={form.keyword}
            onChange={(e) => setForm({ ...form, keyword: e.target.value })}
            placeholder="e.g. seo strategies"
            className="w-full bg-dark-bg border border-dark-border rounded-xl px-4 py-3 text-dark-heading placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-primary-500/50 focus:border-primary-500 transition text-sm"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-dark-text mb-1.5">Language</label>
          <select
            value={form.language}
            onChange={(e) => setForm({ ...form, language: e.target.value })}
            className="w-full bg-dark-bg border border-dark-border rounded-xl px-4 py-3 text-dark-heading focus:outline-none focus:ring-2 focus:ring-primary-500/50 focus:border-primary-500 transition text-sm"
          >
            <option value="EN">English</option>
            <option value="HI">Hindi</option>
            <option value="ES">Spanish</option>
            <option value="FR">French</option>
            <option value="DE">German</option>
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium text-dark-text mb-1.5">Word Count</label>
          <select
            value={form.word_count}
            onChange={(e) => setForm({ ...form, word_count: Number(e.target.value) })}
            className="w-full bg-dark-bg border border-dark-border rounded-xl px-4 py-3 text-dark-heading focus:outline-none focus:ring-2 focus:ring-primary-500/50 focus:border-primary-500 transition text-sm"
          >
            {[500, 800, 1000, 1500, 2000, 2500, 3000].map((n) => (
              <option key={n} value={n}>{n} words</option>
            ))}
          </select>
        </div>
      </div>
      <button
        onClick={handleSubmit}
        disabled={isLoading}
        className="flex items-center gap-2 bg-primary-500 hover:bg-primary-600 disabled:bg-primary-500/50 text-white px-6 py-2.5 rounded-xl font-medium transition"
      >
        {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <BookOpen className="w-4 h-4" />}
        {isLoading ? 'Generating...' : 'Generate Blog'}
      </button>

      {result && (
        <div className="mt-6">
          <div className="flex items-center justify-between mb-3">
            <h4 className="font-semibold text-dark-heading">Generated Blog Post</h4>
            <div className="flex gap-2">
              <button
                onClick={handleSubmit}
                className="flex items-center gap-1 text-sm text-dark-text hover:text-dark-heading transition px-3 py-1.5 border border-dark-border rounded-lg"
              >
                <RefreshCw className="w-3 h-3" />
                Regenerate
              </button>
              <button
                onClick={copyContent}
                className="flex items-center gap-1 text-sm text-primary-400 hover:text-primary-300 transition px-3 py-1.5 bg-primary-500/10 border border-primary-500/20 rounded-lg"
              >
                {copied ? <CheckCircle className="w-3 h-3" /> : <Copy className="w-3 h-3" />}
                {copied ? 'Copied!' : 'Copy All'}
              </button>
            </div>
          </div>
          {result.title && (
            <h2 className="text-xl font-bold text-dark-heading mb-3">{result.title}</h2>
          )}
          <div className="bg-dark-bg border border-dark-border rounded-xl p-5 max-h-96 overflow-y-auto">
            <div className="prose-dark text-sm whitespace-pre-wrap">
              {result.content || result.blog || result.text || JSON.stringify(result, null, 2)}
            </div>
          </div>
          {result.word_count && (
            <p className="text-xs text-dark-text mt-2">{result.word_count} words generated</p>
          )}
        </div>
      )}
    </div>
  )
}

function NewsRewriter() {
  const [article, setArticle] = useState('')
  const [style, setStyle] = useState('professional')
  const [result, setResult] = useState<any>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')
  const [copied, setCopied] = useState(false)

  async function handleSubmit() {
    if (!article.trim()) { setError('Paste an article to rewrite'); return }
    setIsLoading(true); setError('')
    try {
      const res = await contentApi.rewriteNews({ article, style })
      setResult(res.data)
    } catch (e: any) {
      setError(e?.response?.data?.detail || 'Failed to rewrite article')
    } finally { setIsLoading(false) }
  }

  return (
    <div className="bg-dark-card border border-dark-border rounded-2xl p-6">
      <h3 className="font-semibold text-dark-heading text-lg mb-5">News Rewriter</h3>
      {error && <p className="text-red-400 text-sm mb-4 bg-red-500/10 border border-red-500/20 rounded-xl px-3 py-2">{error}</p>}
      <div className="space-y-4 mb-5">
        <div>
          <label className="block text-sm font-medium text-dark-text mb-1.5">Writing Style</label>
          <select
            value={style}
            onChange={(e) => setStyle(e.target.value)}
            className="w-full bg-dark-bg border border-dark-border rounded-xl px-4 py-3 text-dark-heading focus:outline-none focus:ring-2 focus:ring-primary-500/50 focus:border-primary-500 transition text-sm"
          >
            {['professional', 'casual', 'engaging', 'seo-optimized', 'concise'].map((s) => (
              <option key={s} value={s}>{s.charAt(0).toUpperCase() + s.slice(1)}</option>
            ))}
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium text-dark-text mb-1.5">Original Article *</label>
          <textarea
            value={article}
            onChange={(e) => setArticle(e.target.value)}
            placeholder="Paste the original news article here..."
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
        {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Newspaper className="w-4 h-4" />}
        {isLoading ? 'Rewriting...' : 'Rewrite Article'}
      </button>

      {result && (
        <div className="mt-6">
          <div className="flex items-center justify-between mb-3">
            <h4 className="font-semibold text-dark-heading">Rewritten Article</h4>
            <button
              onClick={() => {
                navigator.clipboard.writeText(result.content || result.rewritten || '')
                setCopied(true)
                setTimeout(() => setCopied(false), 2000)
              }}
              className="flex items-center gap-1 text-sm text-primary-400 hover:text-primary-300 transition"
            >
              {copied ? <CheckCircle className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
              {copied ? 'Copied!' : 'Copy'}
            </button>
          </div>
          <div className="bg-dark-bg border border-dark-border rounded-xl p-5 max-h-96 overflow-y-auto">
            <div className="prose-dark text-sm whitespace-pre-wrap">
              {result.content || result.rewritten || result.text || JSON.stringify(result, null, 2)}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

function SocialCaptions() {
  const [topic, setTopic] = useState('')
  const [platform, setPlatform] = useState('instagram')
  const [result, setResult] = useState<any>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')

  async function handleSubmit() {
    if (!topic.trim()) { setError('Topic is required'); return }
    setIsLoading(true); setError('')
    try {
      const res = await contentApi.generateCaptions({ topic, platform })
      setResult(res.data)
    } catch (e: any) {
      setError(e?.response?.data?.detail || 'Failed to generate captions')
    } finally { setIsLoading(false) }
  }

  const PLATFORMS = ['instagram', 'twitter', 'linkedin', 'facebook', 'tiktok']

  return (
    <div className="bg-dark-card border border-dark-border rounded-2xl p-6">
      <h3 className="font-semibold text-dark-heading text-lg mb-5">Social Media Captions</h3>
      {error && <p className="text-red-400 text-sm mb-4 bg-red-500/10 border border-red-500/20 rounded-xl px-3 py-2">{error}</p>}
      <div className="space-y-4 mb-5">
        <div>
          <label className="block text-sm font-medium text-dark-text mb-1.5">Platform</label>
          <div className="flex flex-wrap gap-2">
            {PLATFORMS.map((p) => (
              <button
                key={p}
                onClick={() => setPlatform(p)}
                className={cn(
                  'px-4 py-2 rounded-xl text-sm font-medium transition capitalize border',
                  platform === p
                    ? 'bg-primary-500 border-primary-500 text-white'
                    : 'bg-dark-bg border-dark-border text-dark-text hover:text-dark-heading'
                )}
              >
                {p}
              </button>
            ))}
          </div>
        </div>
        <div>
          <label className="block text-sm font-medium text-dark-text mb-1.5">Topic *</label>
          <input
            type="text"
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            placeholder="e.g. New product launch, fitness tips, travel destination"
            className="w-full bg-dark-bg border border-dark-border rounded-xl px-4 py-3 text-dark-heading placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-primary-500/50 focus:border-primary-500 transition text-sm"
          />
        </div>
      </div>
      <button
        onClick={handleSubmit}
        disabled={isLoading}
        className="flex items-center gap-2 bg-primary-500 hover:bg-primary-600 disabled:bg-primary-500/50 text-white px-6 py-2.5 rounded-xl font-medium transition"
      >
        {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <MessageSquare className="w-4 h-4" />}
        Generate Captions
      </button>

      {result && (
        <div className="mt-6 space-y-4">
          {(result.captions || [result]).map((cap: any, i: number) => (
            <div key={i} className="bg-dark-bg border border-dark-border rounded-xl p-4">
              <div className="flex items-start justify-between gap-3">
                <p className="text-sm text-dark-heading whitespace-pre-wrap flex-1">
                  {typeof cap === 'string' ? cap : cap.caption || cap.text || cap.content || ''}
                </p>
                <button
                  onClick={() => navigator.clipboard.writeText(typeof cap === 'string' ? cap : cap.caption || '')}
                  className="text-dark-text hover:text-dark-heading flex-shrink-0 transition"
                >
                  <Copy className="w-4 h-4" />
                </button>
              </div>
              {cap.hashtags && (
                <p className="text-xs text-primary-400 mt-2">{Array.isArray(cap.hashtags) ? cap.hashtags.join(' ') : cap.hashtags}</p>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

function ContentLibrary() {
  const [posts, setPosts] = useState<any[]>([])
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    contentApi.listPosts()
      .then((res) => setPosts(res.data?.posts || res.data || []))
      .catch(() => { })
      .finally(() => setIsLoading(false))
  }, [])

  return (
    <div className="bg-dark-card border border-dark-border rounded-2xl p-6">
      <h3 className="font-semibold text-dark-heading text-lg mb-4">Content Library</h3>
      {isLoading ? (
        <div className="space-y-3">
          {[...Array(4)].map((_, i) => <div key={i} className="h-20 bg-dark-bg rounded-xl animate-pulse" />)}
        </div>
      ) : posts.length === 0 ? (
        <div className="text-center py-12">
          <Library className="w-12 h-12 mx-auto text-slate-600 mb-3" />
          <p className="text-dark-heading font-medium">No content yet</p>
          <p className="text-dark-text text-sm mt-1">Generate blogs, captions, or articles to see them here</p>
        </div>
      ) : (
        <div className="space-y-3">
          {posts.map((post, i) => (
            <div key={post.id || i} className="bg-dark-bg border border-dark-border rounded-xl p-4 hover:border-dark-border/80 transition">
              <div className="flex items-start justify-between gap-3">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span className={cn('text-xs px-2 py-0.5 rounded-full font-medium', getStatusColor(post.status || 'draft'))}>
                      {post.status || 'draft'}
                    </span>
                    <span className="text-xs text-dark-text capitalize">{post.type || post.content_type || 'post'}</span>
                  </div>
                  <p className="font-medium text-dark-heading">{post.title || truncate(post.content, 60)}</p>
                  <p className="text-xs text-dark-text mt-1">{formatDate(post.created_at)}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
