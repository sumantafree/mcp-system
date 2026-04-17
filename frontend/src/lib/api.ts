import axios, { AxiosInstance, AxiosResponse } from 'axios'

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

const apiClient: AxiosInstance = axios.create({
  baseURL: BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor to inject auth token
apiClient.interceptors.request.use(
  (config) => {
    if (typeof window !== 'undefined') {
      const token = localStorage.getItem('mcp_token')
      if (token) {
        config.headers.Authorization = `Bearer ${token}`
      }
    }
    return config
  },
  (error) => Promise.reject(error)
)

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401 && typeof window !== 'undefined') {
      localStorage.removeItem('mcp_token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// ── AUTH ──────────────────────────────────────────────────────────────────────

export const auth = {
  login: (email: string, password: string) => {
    const form = new URLSearchParams()
    form.append('username', email)
    form.append('password', password)
    return apiClient.post('/auth/login', form, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    })
  },

  register: (data: {
    email: string
    username?: string
    full_name?: string
    password: string
  }) => apiClient.post('/auth/register', data),

  getMe: () => apiClient.get('/auth/me'),

  updateProfile: (data: {
    full_name?: string
    phone?: string
    timezone?: string
    avatar_url?: string
  }) => apiClient.patch('/auth/me', data),

  logout: () => apiClient.post('/auth/logout'),
}

// ── TASKS ─────────────────────────────────────────────────────────────────────

export const tasks = {
  list: (params?: { status?: string; priority?: string }) =>
    apiClient.get('/tasks', { params }),

  create: (data: {
    title: string
    description?: string
    priority?: string
    due_date?: string
  }) => apiClient.post('/tasks', data),

  update: (id: number, data: Partial<{
    title: string
    description: string
    priority: string
    status: string
    due_date: string
  }>) => apiClient.put(`/tasks/${id}`, data),

  delete: (id: number) => apiClient.delete(`/tasks/${id}`),

  createFromText: (text: string) =>
    apiClient.post('/tasks/ai/create-from-text', { text }),

  getSuggestions: () => apiClient.get('/tasks/ai/suggestions'),

  getBriefing: () => apiClient.get('/tasks/ai/briefing'),
}

// ── SEO ───────────────────────────────────────────────────────────────────────

export const seo = {
  clusterKeywords: (keywords: string[]) =>
    apiClient.post('/seo/cluster-keywords', { keywords }),

  generateMeta: (data: { title: string; description: string; keyword: string }) =>
    apiClient.post('/seo/generate-meta', data),

  suggestLinks: (data: { page_title: string; existing_pages: string[] }) =>
    apiClient.post('/seo/suggest-links', data),

  auditContent: (data: { content: string; keyword: string }) =>
    apiClient.post('/seo/audit-content', data),

  listKeywords: () => apiClient.get('/seo/keywords'),
}

// ── CONTENT ───────────────────────────────────────────────────────────────────

export const content = {
  generateBlog: (data: {
    topic: string
    keyword: string
    language?: string
    word_count?: number
  }) => apiClient.post('/content/generate-blog', data),

  rewriteNews: (data: { article: string; style?: string }) =>
    apiClient.post('/content/rewrite-news', data),

  generateCaptions: (data: { topic: string; platform: string }) =>
    apiClient.post('/content/generate-captions', data),

  listPosts: () => apiClient.get('/content/posts'),
}

// ── SOCIAL ────────────────────────────────────────────────────────────────────

export const social = {
  generatePost: (data: {
    platform: string
    topic: string
    tone?: string
    include_hashtags?: boolean
  }) => apiClient.post('/social/generate-post', data),

  schedulePost: (data: {
    platform: string
    content: string
    scheduled_at: string
  }) => apiClient.post('/social/schedule-post', data),

  listPosts: (params?: { platform?: string; status?: string }) =>
    apiClient.get('/social/posts', { params }),

  getHashtags: (topic: string, platform: string) =>
    apiClient.post('/social/hashtags', { topic, platform }),

  generateCalendar: (data: { topics: string[]; platforms: string[]; days?: number }) =>
    apiClient.post('/social/generate-calendar', data),
}

// ── YOUTUBE ───────────────────────────────────────────────────────────────────

export const youtube = {
  generateScript: (data: {
    topic: string
    duration_minutes?: number
    style?: string
  }) => apiClient.post('/youtube/generate-script', data),

  optimizeTitle: (data: { topic: string; niche: string }) =>
    apiClient.post('/youtube/optimize-title', data),

  generateShorts: (script: string) =>
    apiClient.post('/youtube/generate-shorts', { script }),

  listVideos: () => apiClient.get('/youtube/videos'),
}

// ── CRM ───────────────────────────────────────────────────────────────────────

export const crm = {
  createLead: (data: {
    name: string
    email?: string
    company?: string
    phone?: string
    deal_value?: number
    stage?: string
    notes?: string
  }) => apiClient.post('/crm/leads', data),

  listLeads: (params?: { stage?: string }) =>
    apiClient.get('/crm/leads', { params }),

  scoreLead: (id: number) => apiClient.post(`/crm/leads/${id}/score`),

  generateFollowup: (id: number) =>
    apiClient.post(`/crm/leads/${id}/generate-followup`),

  sendFollowup: (id: number, data: { channel: string; message: string }) =>
    apiClient.post(`/crm/leads/${id}/send-followup`, data),

  getPipelineReport: () => apiClient.get('/crm/pipeline-report'),
}

// ── WEBSITE ───────────────────────────────────────────────────────────────────

export const website = {
  scanWebsite: (url: string) =>
    apiClient.post('/website/scan', { url }),

  generatePage: (data: { keyword: string; page_type: string }) =>
    apiClient.post('/website/generate-page', data),

  analyzePerformance: (url: string) =>
    apiClient.post('/website/analyze-performance', { url }),

  listScans: () => apiClient.get('/website/scans'),
}

// ── ANALYTICS ─────────────────────────────────────────────────────────────────

export const analytics = {
  getDashboard: (days?: number) =>
    apiClient.get('/analytics/dashboard', { params: { days } }),

  generateWeeklyReport: () => apiClient.post('/analytics/weekly-report'),

  getActivity: (days?: number) =>
    apiClient.get('/analytics/activity', { params: { days } }),
}

// ── ASSISTANT ─────────────────────────────────────────────────────────────────

export const assistant = {
  processCommand: (command: string) =>
    apiClient.post('/assistant/command', { command }),

  chat: (message: string, history?: Array<{ role: string; content: string }>) =>
    apiClient.post('/assistant/chat', { message, history }),

  getDailyBriefing: () => apiClient.get('/assistant/daily-briefing'),
}

export default apiClient
