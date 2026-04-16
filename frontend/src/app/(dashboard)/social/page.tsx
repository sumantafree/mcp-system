'use client'

import { useState, useEffect } from 'react'
import { Share2, Loader2, Hash, Calendar, Clock, Copy, CheckCircle, Plus } from 'lucide-react'
import { social } from '@/lib/api'
import { cn, formatDateTime, getStatusColor } from '@/lib/utils'

type Tab = 'generate' | 'scheduled' | 'calendar' | 'hashtags'

const PLATFORMS = ['instagram', 'twitter', 'linkedin', 'facebook']
const TONES = ['professional', 'casual', 'funny', 'inspirational', 'promotional']

export default function SocialPage() {
  const [activeTab, setActiveTab] = useState<Tab>('generate')
  const [activePlatform, setActivePlatform] = useState('instagram')

  const tabs = [
    { id: 'generate' as Tab, label: 'Post Generator', icon: Share2 },
    { id: 'scheduled' as Tab, label: 'Scheduled Posts', icon: Clock },
    { id: 'calendar' as Tab, label: 'Content Calendar', icon: Calendar },
    { id: 'hashtags' as Tab, label: 'Hashtag Generator', icon: Hash },
  ]

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Platform tabs */}
      <div className="flex gap-2 bg-dark-card border border-dark-border rounded-2xl p-2">
        {PLATFORMS.map((p) => (
          <button
            key={p}
            onClick={() => setActivePlatform(p)}
            className={cn(
              'flex-1 py-2 rounded-xl text-sm font-medium transition capitalize',
              activePlatform === p
                ? 'bg-primary-500 text-white'
                : 'text-dark-text hover:text-dark-heading'
            )}
          >
            {p}
          </button>
        ))}
      </div>

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
                activeTab === tab.id ? 'bg-primary-500 text-white' : 'text-dark-text hover:text-dark-heading'
              )}
            >
              <Icon className="w-4 h-4" />
              {tab.label}
            </button>
          )
        })}
      </div>

      {activeTab === 'generate' && <PostGenerator platform={activePlatform} />}
      {activeTab === 'scheduled' && <ScheduledPosts />}
      {activeTab === 'calendar' && <ContentCalendar />}
      {activeTab === 'hashtags' && <HashtagGenerator />}
    </div>
  )
}

function PostGenerator({ platform }: { platform: string }) {
  const [topic, setTopic] = useState('')
  const [tone, setTone] = useState('professional')
  const [includeHashtags, setIncludeHashtags] = useState(true)
  const [result, setResult] = useState<any>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')
  const [copied, setCopied] = useState(false)
  const [scheduleDate, setScheduleDate] = useState('')
  const [scheduling, setScheduling] = useState(false)
  const [scheduled, setScheduled] = useState(false)

  async function handleGenerate() {
    if (!topic.trim()) { setError('Topic is required'); return }
    setIsLoading(true); setError('')
    try {
      const res = await social.generatePost({ platform, topic, tone, include_hashtags: includeHashtags })
      setResult(res.data)
    } catch (e: any) {
      setError(e?.response?.data?.detail || 'Failed to generate post')
    } finally { setIsLoading(false) }
  }

  async function handleSchedule() {
    if (!scheduleDate || !result) return
    setScheduling(true)
    try {
      const content = result.content || result.post || result.text || ''
      await social.schedulePost({ platform, content, scheduled_at: new Date(scheduleDate).toISOString() })
      setScheduled(true)
      setTimeout(() => setScheduled(false), 3000)
    } catch { }
    finally { setScheduling(false) }
  }

  return (
    <div className="bg-dark-card border border-dark-border rounded-2xl p-6">
      <h3 className="font-semibold text-dark-heading text-lg mb-5 capitalize">{platform} Post Generator</h3>
      {error && <p className="text-red-400 text-sm mb-4 bg-red-500/10 border border-red-500/20 rounded-xl px-3 py-2">{error}</p>}
      <div className="space-y-4 mb-5">
        <div>
          <label className="block text-sm font-medium text-dark-text mb-1.5">Topic *</label>
          <input
            type="text"
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            placeholder="e.g. New product launch, tips for productivity"
            className="w-full bg-dark-bg border border-dark-border rounded-xl px-4 py-3 text-dark-heading placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-primary-500/50 focus:border-primary-500 transition text-sm"
          />
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-dark-text mb-1.5">Tone</label>
            <select
              value={tone}
              onChange={(e) => setTone(e.target.value)}
              className="w-full bg-dark-bg border border-dark-border rounded-xl px-4 py-3 text-dark-heading focus:outline-none focus:ring-2 focus:ring-primary-500/50 focus:border-primary-500 transition text-sm"
            >
              {TONES.map((t) => (
                <option key={t} value={t}>{t.charAt(0).toUpperCase() + t.slice(1)}</option>
              ))}
            </select>
          </div>
          <div className="flex items-end pb-1">
            <label className="flex items-center gap-2 cursor-pointer">
              <div
                onClick={() => setIncludeHashtags(!includeHashtags)}
                className={cn(
                  'w-10 h-5 rounded-full transition relative cursor-pointer',
                  includeHashtags ? 'bg-primary-500' : 'bg-slate-600'
                )}
              >
                <div className={cn(
                  'w-4 h-4 bg-white rounded-full absolute top-0.5 transition-all',
                  includeHashtags ? 'left-5' : 'left-0.5'
                )} />
              </div>
              <span className="text-sm text-dark-text">Include Hashtags</span>
            </label>
          </div>
        </div>
      </div>
      <button
        onClick={handleGenerate}
        disabled={isLoading}
        className="flex items-center gap-2 bg-primary-500 hover:bg-primary-600 disabled:bg-primary-500/50 text-white px-6 py-2.5 rounded-xl font-medium transition"
      >
        {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Share2 className="w-4 h-4" />}
        Generate Post
      </button>

      {result && (
        <div className="mt-6 space-y-4">
          <div className="bg-dark-bg border border-dark-border rounded-xl p-4">
            <div className="flex items-start justify-between gap-3 mb-3">
              <span className="text-xs font-semibold text-primary-400 uppercase tracking-wider capitalize">{platform} Post</span>
              <button
                onClick={() => {
                  navigator.clipboard.writeText(result.content || result.post || '')
                  setCopied(true)
                  setTimeout(() => setCopied(false), 2000)
                }}
                className="flex items-center gap-1 text-xs text-dark-text hover:text-dark-heading transition"
              >
                {copied ? <CheckCircle className="w-3 h-3 text-green-400" /> : <Copy className="w-3 h-3" />}
                {copied ? 'Copied!' : 'Copy'}
              </button>
            </div>
            <p className="text-sm text-dark-heading whitespace-pre-wrap">{result.content || result.post || result.text || ''}</p>
            {result.hashtags && (
              <p className="text-sm text-primary-400 mt-3">
                {Array.isArray(result.hashtags) ? result.hashtags.join(' ') : result.hashtags}
              </p>
            )}
          </div>

          {/* Schedule option */}
          <div className="bg-dark-bg border border-dark-border rounded-xl p-4">
            <p className="text-sm font-medium text-dark-heading mb-3">Schedule this post</p>
            <div className="flex gap-3">
              <input
                type="datetime-local"
                value={scheduleDate}
                onChange={(e) => setScheduleDate(e.target.value)}
                className="flex-1 bg-dark-card border border-dark-border rounded-xl px-4 py-2 text-dark-heading focus:outline-none focus:ring-2 focus:ring-primary-500/50 focus:border-primary-500 transition text-sm"
              />
              <button
                onClick={handleSchedule}
                disabled={!scheduleDate || scheduling || scheduled}
                className="flex items-center gap-2 bg-green-500/20 hover:bg-green-500/30 border border-green-500/30 text-green-400 px-4 py-2 rounded-xl text-sm font-medium transition disabled:opacity-50"
              >
                {scheduling ? <Loader2 className="w-4 h-4 animate-spin" /> : scheduled ? <CheckCircle className="w-4 h-4" /> : <Calendar className="w-4 h-4" />}
                {scheduled ? 'Scheduled!' : 'Schedule'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

function ScheduledPosts() {
  const [posts, setPosts] = useState<any[]>([])
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    social.listPosts({ status: 'scheduled' })
      .then((res) => setPosts(res.data?.posts || res.data || []))
      .catch(() => { })
      .finally(() => setIsLoading(false))
  }, [])

  return (
    <div className="bg-dark-card border border-dark-border rounded-2xl p-6">
      <h3 className="font-semibold text-dark-heading text-lg mb-4">Scheduled Posts</h3>
      {isLoading ? (
        <div className="space-y-3">
          {[...Array(3)].map((_, i) => <div key={i} className="h-20 bg-dark-bg rounded-xl animate-pulse" />)}
        </div>
      ) : posts.length === 0 ? (
        <div className="text-center py-12">
          <Clock className="w-12 h-12 mx-auto text-slate-600 mb-3" />
          <p className="text-dark-heading font-medium">No scheduled posts</p>
          <p className="text-dark-text text-sm mt-1">Generate posts and schedule them for later</p>
        </div>
      ) : (
        <div className="space-y-3">
          {posts.map((post, i) => (
            <div key={post.id || i} className="bg-dark-bg border border-dark-border rounded-xl p-4">
              <div className="flex items-start justify-between gap-3">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-xs bg-primary-500/20 text-primary-400 border border-primary-500/30 px-2 py-0.5 rounded-full font-medium capitalize">{post.platform || 'social'}</span>
                    <span className={cn('text-xs px-2 py-0.5 rounded-full font-medium', getStatusColor(post.status || 'scheduled'))}>
                      {post.status || 'scheduled'}
                    </span>
                  </div>
                  <p className="text-sm text-dark-heading">{post.content?.slice(0, 100)}...</p>
                  <p className="text-xs text-dark-text mt-1 flex items-center gap-1">
                    <Clock className="w-3 h-3" />
                    {formatDateTime(post.scheduled_at)}
                  </p>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

function ContentCalendar() {
  const [topics, setTopics] = useState('')
  const [platforms, setPlatforms] = useState<string[]>(['instagram', 'twitter'])
  const [days, setDays] = useState(7)
  const [result, setResult] = useState<any>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')

  function togglePlatform(p: string) {
    setPlatforms((prev) =>
      prev.includes(p) ? prev.filter((x) => x !== p) : [...prev, p]
    )
  }

  async function handleGenerate() {
    const topicList = topics.split('\n').map((t) => t.trim()).filter(Boolean)
    if (topicList.length === 0) { setError('Enter at least one topic'); return }
    if (platforms.length === 0) { setError('Select at least one platform'); return }
    setIsLoading(true); setError('')
    try {
      const res = await social.generateCalendar({ topics: topicList, platforms, days })
      setResult(res.data)
    } catch (e: any) {
      setError(e?.response?.data?.detail || 'Failed to generate calendar')
    } finally { setIsLoading(false) }
  }

  return (
    <div className="bg-dark-card border border-dark-border rounded-2xl p-6">
      <h3 className="font-semibold text-dark-heading text-lg mb-5">Content Calendar Generator</h3>
      {error && <p className="text-red-400 text-sm mb-4 bg-red-500/10 border border-red-500/20 rounded-xl px-3 py-2">{error}</p>}
      <div className="space-y-4 mb-5">
        <div>
          <label className="block text-sm font-medium text-dark-text mb-1.5">Topics (one per line)</label>
          <textarea
            value={topics}
            onChange={(e) => setTopics(e.target.value)}
            placeholder="Product tips&#10;Customer success story&#10;Industry news&#10;Behind the scenes"
            rows={5}
            className="w-full bg-dark-bg border border-dark-border rounded-xl px-4 py-3 text-dark-heading placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-primary-500/50 focus:border-primary-500 transition text-sm resize-none"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-dark-text mb-2">Platforms</label>
          <div className="flex flex-wrap gap-2">
            {PLATFORMS.map((p) => (
              <button
                key={p}
                onClick={() => togglePlatform(p)}
                className={cn(
                  'px-4 py-2 rounded-xl text-sm font-medium transition capitalize border',
                  platforms.includes(p)
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
          <label className="block text-sm font-medium text-dark-text mb-1.5">Duration</label>
          <select
            value={days}
            onChange={(e) => setDays(Number(e.target.value))}
            className="w-full bg-dark-bg border border-dark-border rounded-xl px-4 py-3 text-dark-heading focus:outline-none focus:ring-2 focus:ring-primary-500/50 focus:border-primary-500 transition text-sm"
          >
            {[7, 14, 30].map((d) => (
              <option key={d} value={d}>{d} days</option>
            ))}
          </select>
        </div>
      </div>
      <button
        onClick={handleGenerate}
        disabled={isLoading}
        className="flex items-center gap-2 bg-primary-500 hover:bg-primary-600 disabled:bg-primary-500/50 text-white px-6 py-2.5 rounded-xl font-medium transition"
      >
        {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Calendar className="w-4 h-4" />}
        Generate Calendar
      </button>

      {result && (
        <div className="mt-6">
          <h4 className="font-semibold text-dark-heading mb-4">{days}-Day Content Calendar</h4>
          <div className="space-y-3">
            {(result.calendar || result.schedule || []).map((item: any, i: number) => (
              <div key={i} className="bg-dark-bg border border-dark-border rounded-xl p-4">
                <div className="flex items-center gap-3 mb-2">
                  <span className="text-sm font-semibold text-primary-400">Day {item.day || i + 1}</span>
                  {item.date && <span className="text-xs text-dark-text">{item.date}</span>}
                  {item.platform && (
                    <span className="text-xs bg-dark-card border border-dark-border text-dark-text px-2 py-0.5 rounded-full capitalize">{item.platform}</span>
                  )}
                </div>
                <p className="text-sm text-dark-heading">{item.topic || item.content || item.title || ''}</p>
                {item.caption && <p className="text-sm text-dark-text mt-1">{item.caption}</p>}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

function HashtagGenerator() {
  const [topic, setTopic] = useState('')
  const [platform, setPlatform] = useState('instagram')
  const [result, setResult] = useState<any>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')

  async function handleSubmit() {
    if (!topic.trim()) { setError('Topic is required'); return }
    setIsLoading(true); setError('')
    try {
      const res = await social.getHashtags(topic, platform)
      setResult(res.data)
    } catch (e: any) {
      setError(e?.response?.data?.detail || 'Failed to generate hashtags')
    } finally { setIsLoading(false) }
  }

  const hashtags: string[] = result?.hashtags || result?.tags || []

  return (
    <div className="bg-dark-card border border-dark-border rounded-2xl p-6">
      <h3 className="font-semibold text-dark-heading text-lg mb-5">Hashtag Generator</h3>
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
            placeholder="e.g. digital marketing, fitness motivation"
            className="w-full bg-dark-bg border border-dark-border rounded-xl px-4 py-3 text-dark-heading placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-primary-500/50 focus:border-primary-500 transition text-sm"
          />
        </div>
      </div>
      <button
        onClick={handleSubmit}
        disabled={isLoading}
        className="flex items-center gap-2 bg-primary-500 hover:bg-primary-600 disabled:bg-primary-500/50 text-white px-6 py-2.5 rounded-xl font-medium transition"
      >
        {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Hash className="w-4 h-4" />}
        Generate Hashtags
      </button>

      {hashtags.length > 0 && (
        <div className="mt-6">
          <div className="flex items-center justify-between mb-3">
            <h4 className="font-semibold text-dark-heading">{hashtags.length} Hashtags</h4>
            <button
              onClick={() => navigator.clipboard.writeText(hashtags.join(' '))}
              className="flex items-center gap-1 text-sm text-primary-400 hover:text-primary-300 transition"
            >
              <Copy className="w-4 h-4" />
              Copy All
            </button>
          </div>
          <div className="flex flex-wrap gap-2">
            {hashtags.map((tag, i) => (
              <button
                key={i}
                onClick={() => navigator.clipboard.writeText(tag)}
                className="text-sm bg-dark-bg border border-dark-border text-primary-400 px-3 py-1.5 rounded-xl hover:bg-dark-card transition"
              >
                {tag.startsWith('#') ? tag : `#${tag}`}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
