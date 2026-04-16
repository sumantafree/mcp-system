'use client'

import { useEffect, useRef, useState, KeyboardEvent } from 'react'
import { Bot, Send, Zap, RefreshCw, User, ChevronRight } from 'lucide-react'
import { assistant } from '@/lib/api'
import { cn, formatRelative } from '@/lib/utils'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
  mcp_route?: string
}

const QUICK_ACTIONS = [
  'Show my task summary',
  'What leads need follow-up?',
  'Generate a blog post idea',
  'What are my overdue tasks?',
  'Summarize this week\'s analytics',
  'Create a content calendar for next week',
]

export default function AssistantPage() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [isTyping, setIsTyping] = useState(false)
  const [briefing, setBriefing] = useState('')
  const [briefingLoading, setBriefingLoading] = useState(true)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    // Get daily briefing
    assistant.getDailyBriefing()
      .then((res) => setBriefing(res.data?.briefing || res.data?.message || ''))
      .catch(() => { })
      .finally(() => setBriefingLoading(false))

    // Add welcome message
    setMessages([{
      id: 'welcome',
      role: 'assistant',
      content: 'Hello! I\'m ARIA, your AI assistant for the MCP System. I can help you manage tasks, generate content, analyze leads, create reports, and much more. What would you like to do today?',
      timestamp: new Date(),
    }])
  }, [])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isTyping])

  async function sendMessage(text?: string) {
    const messageText = (text || input).trim()
    if (!messageText) return

    const userMsg: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: messageText,
      timestamp: new Date(),
    }

    setMessages((prev) => [...prev, userMsg])
    setInput('')
    setIsTyping(true)

    try {
      // Build history for context
      const history = messages.slice(-10).map((m) => ({
        role: m.role,
        content: m.content,
      }))

      const res = await assistant.chat(messageText, history)
      const data = res.data

      const assistantMsg: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: data.response || data.message || data.content || 'I processed your request.',
        timestamp: new Date(),
        mcp_route: data.mcp_route || data.route || data.module,
      }

      setMessages((prev) => [...prev, assistantMsg])
    } catch (e: any) {
      const errorMsg: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: 'Sorry, I encountered an error processing your request. Please try again.',
        timestamp: new Date(),
      }
      setMessages((prev) => [...prev, errorMsg])
    } finally {
      setIsTyping(false)
    }
  }

  function handleKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  function handleRefreshBriefing() {
    setBriefingLoading(true)
    assistant.getDailyBriefing()
      .then((res) => setBriefing(res.data?.briefing || res.data?.message || ''))
      .catch(() => { })
      .finally(() => setBriefingLoading(false))
  }

  return (
    <div className="flex flex-col h-[calc(100vh-112px)] animate-fade-in">
      {/* Daily briefing */}
      {(briefing || briefingLoading) && (
        <div className="bg-gradient-to-r from-primary-500/10 to-purple-500/10 border border-primary-500/20 rounded-2xl p-4 mb-4 flex-shrink-0">
          <div className="flex items-start justify-between gap-3">
            <div className="flex items-start gap-3 flex-1">
              <div className="w-7 h-7 bg-primary-500/20 rounded-lg flex items-center justify-center flex-shrink-0">
                <Zap className="w-3.5 h-3.5 text-primary-400" />
              </div>
              <div className="flex-1">
                <p className="text-xs font-semibold text-primary-400 mb-1">Today's Briefing</p>
                {briefingLoading ? (
                  <div className="space-y-1.5">
                    <div className="h-3 bg-primary-500/20 rounded animate-pulse w-3/4" />
                    <div className="h-3 bg-primary-500/20 rounded animate-pulse w-1/2" />
                  </div>
                ) : (
                  <p className="text-sm text-dark-text leading-relaxed">{briefing}</p>
                )}
              </div>
            </div>
            <button
              onClick={handleRefreshBriefing}
              className="text-dark-text hover:text-dark-heading transition flex-shrink-0"
            >
              <RefreshCw className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {/* Quick actions */}
      <div className="flex gap-2 overflow-x-auto pb-2 flex-shrink-0 scrollbar-hide">
        {QUICK_ACTIONS.map((action, i) => (
          <button
            key={i}
            onClick={() => sendMessage(action)}
            className="flex items-center gap-1.5 whitespace-nowrap text-xs bg-dark-card border border-dark-border hover:border-primary-500/30 text-dark-text hover:text-dark-heading px-3 py-1.5 rounded-xl transition flex-shrink-0"
          >
            <ChevronRight className="w-3 h-3" />
            {action}
          </button>
        ))}
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto py-4 space-y-4 min-h-0">
        {messages.map((message) => (
          <MessageBubble key={message.id} message={message} />
        ))}

        {/* Typing indicator */}
        {isTyping && (
          <div className="flex items-start gap-3">
            <div className="w-8 h-8 rounded-full bg-primary-500/20 border border-primary-500/30 flex items-center justify-center flex-shrink-0">
              <Bot className="w-4 h-4 text-primary-400" />
            </div>
            <div className="bg-dark-card border border-dark-border rounded-2xl rounded-tl-sm px-4 py-3">
              <div className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-primary-400 typing-dot" />
                <span className="w-2 h-2 rounded-full bg-primary-400 typing-dot" />
                <span className="w-2 h-2 rounded-full bg-primary-400 typing-dot" />
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="flex-shrink-0 bg-dark-card border border-dark-border rounded-2xl p-3 mt-2">
        <div className="flex items-end gap-3">
          <textarea
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask ARIA anything... (Enter to send, Shift+Enter for newline)"
            rows={1}
            style={{ maxHeight: '120px', overflowY: 'auto' }}
            className="flex-1 bg-transparent text-dark-heading placeholder-slate-500 focus:outline-none text-sm resize-none leading-relaxed py-1"
            onInput={(e) => {
              const target = e.target as HTMLTextAreaElement
              target.style.height = 'auto'
              target.style.height = Math.min(target.scrollHeight, 120) + 'px'
            }}
          />
          <button
            onClick={() => sendMessage()}
            disabled={!input.trim() || isTyping}
            className="w-9 h-9 bg-primary-500 hover:bg-primary-600 disabled:bg-primary-500/40 rounded-xl flex items-center justify-center transition flex-shrink-0"
          >
            <Send className="w-4 h-4 text-white" />
          </button>
        </div>
      </div>
    </div>
  )
}

function MessageBubble({ message }: { message: Message }) {
  const isUser = message.role === 'user'

  return (
    <div className={cn('flex items-start gap-3', isUser && 'flex-row-reverse')}>
      {/* Avatar */}
      <div className={cn(
        'w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0',
        isUser
          ? 'bg-dark-card border border-dark-border'
          : 'bg-primary-500/20 border border-primary-500/30'
      )}>
        {isUser ? (
          <User className="w-4 h-4 text-dark-text" />
        ) : (
          <Bot className="w-4 h-4 text-primary-400" />
        )}
      </div>

      {/* Bubble */}
      <div className={cn('max-w-[80%] space-y-1', isUser && 'items-end')}>
        <div className={cn(
          'px-4 py-3 rounded-2xl text-sm leading-relaxed',
          isUser
            ? 'bg-primary-500 text-white rounded-tr-sm'
            : 'bg-dark-card border border-dark-border text-dark-heading rounded-tl-sm'
        )}>
          <p className="whitespace-pre-wrap">{message.content}</p>
        </div>
        <div className={cn('flex items-center gap-2', isUser && 'flex-row-reverse')}>
          <span className="text-xs text-slate-500">{formatRelative(message.timestamp)}</span>
          {message.mcp_route && (
            <span className="text-xs bg-dark-card border border-dark-border text-dark-text px-2 py-0.5 rounded-full flex items-center gap-1">
              <Zap className="w-2.5 h-2.5" />
              {message.mcp_route}
            </span>
          )}
        </div>
      </div>
    </div>
  )
}
