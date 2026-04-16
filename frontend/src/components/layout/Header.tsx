'use client'

import { useState } from 'react'
import { Bell, Search, X } from 'lucide-react'
import { cn, getInitials } from '@/lib/utils'

interface Notification {
  id: number
  title: string
  message: string
  type: 'info' | 'warning' | 'success' | 'error'
  read: boolean
  time: string
}

interface HeaderProps {
  title: string
  user?: { full_name?: string; email?: string; username?: string } | null
  notifications?: Notification[]
}

const mockNotifications: Notification[] = [
  { id: 1, title: 'Task Overdue', message: 'Q2 Report is past due date', type: 'error', read: false, time: '5m ago' },
  { id: 2, title: 'New Lead', message: 'Sarah Johnson from Acme Corp added', type: 'success', read: false, time: '1h ago' },
  { id: 3, title: 'Content Published', message: 'Blog post "SEO Tips 2025" is live', type: 'info', read: true, time: '3h ago' },
]

export default function Header({ title, user, notifications = mockNotifications }: HeaderProps) {
  const [showNotifications, setShowNotifications] = useState(false)
  const [search, setSearch] = useState('')
  const [notifList, setNotifList] = useState(notifications)

  const unreadCount = notifList.filter((n) => !n.read).length

  function markAllRead() {
    setNotifList((prev) => prev.map((n) => ({ ...n, read: true })))
  }

  function getNotifColor(type: string) {
    switch (type) {
      case 'error': return 'bg-red-500'
      case 'warning': return 'bg-yellow-500'
      case 'success': return 'bg-green-500'
      default: return 'bg-blue-500'
    }
  }

  return (
    <header className="h-14 sm:h-16 bg-dark-card border-b border-dark-border flex items-center justify-between px-4 sm:px-6 sticky top-0 z-20">
      {/* Title */}
      <div className="flex items-center gap-3">
        <div className="lg:hidden w-9 flex-shrink-0" /> {/* Spacer for mobile menu button */}
        <h2 className="text-base sm:text-lg font-semibold text-dark-heading truncate max-w-[140px] sm:max-w-none">{title}</h2>
      </div>

      {/* Right section */}
      <div className="flex items-center gap-3">
        {/* Search */}
        <div className="hidden md:flex items-center gap-2 bg-dark-bg border border-dark-border rounded-xl px-3 py-2 w-56 focus-within:border-primary-500/50 transition">
          <Search className="w-4 h-4 text-slate-500 flex-shrink-0" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Quick search..."
            className="bg-transparent text-sm text-dark-heading placeholder-slate-500 focus:outline-none w-full"
          />
          {search && (
            <button onClick={() => setSearch('')} className="text-slate-500 hover:text-dark-text">
              <X className="w-3 h-3" />
            </button>
          )}
        </div>

        {/* Notifications */}
        <div className="relative">
          <button
            onClick={() => setShowNotifications(!showNotifications)}
            className="relative p-2 rounded-xl text-dark-text hover:text-dark-heading hover:bg-dark-bg transition"
          >
            <Bell className="w-5 h-5" />
            {unreadCount > 0 && (
              <span className="absolute top-1 right-1 w-4 h-4 bg-red-500 text-white text-xs rounded-full flex items-center justify-center font-bold">
                {unreadCount}
              </span>
            )}
          </button>

          {showNotifications && (
            <>
              <div className="fixed inset-0 z-10" onClick={() => setShowNotifications(false)} />
              <div className="absolute right-0 top-12 z-20 w-72 sm:w-80 max-w-[calc(100vw-1rem)] bg-dark-card border border-dark-border rounded-2xl shadow-2xl overflow-hidden">
                <div className="flex items-center justify-between px-4 py-3 border-b border-dark-border">
                  <span className="font-semibold text-dark-heading text-sm">Notifications</span>
                  {unreadCount > 0 && (
                    <button
                      onClick={markAllRead}
                      className="text-xs text-primary-400 hover:text-primary-300 transition"
                    >
                      Mark all read
                    </button>
                  )}
                </div>
                <div className="max-h-80 overflow-y-auto">
                  {notifList.length === 0 ? (
                    <div className="p-6 text-center text-dark-text text-sm">No notifications</div>
                  ) : (
                    notifList.map((notif) => (
                      <div
                        key={notif.id}
                        className={cn(
                          'flex items-start gap-3 px-4 py-3 border-b border-dark-border/50 hover:bg-dark-bg/50 transition',
                          !notif.read && 'bg-primary-500/5'
                        )}
                      >
                        <div className={cn('w-2 h-2 rounded-full mt-1.5 flex-shrink-0', getNotifColor(notif.type))} />
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium text-dark-heading">{notif.title}</p>
                          <p className="text-xs text-dark-text mt-0.5">{notif.message}</p>
                          <p className="text-xs text-slate-500 mt-1">{notif.time}</p>
                        </div>
                        {!notif.read && (
                          <div className="w-2 h-2 rounded-full bg-primary-500 flex-shrink-0 mt-1.5" />
                        )}
                      </div>
                    ))
                  )}
                </div>
              </div>
            </>
          )}
        </div>

        {/* User avatar */}
        <div className="flex items-center gap-2.5 pl-2 border-l border-dark-border">
          <div className="w-8 h-8 rounded-full bg-primary-500/30 border border-primary-500/30 flex items-center justify-center">
            <span className="text-xs font-bold text-primary-400">
              {getInitials(user?.full_name || user?.username || 'U')}
            </span>
          </div>
          <div className="hidden md:block">
            <p className="text-sm font-medium text-dark-heading leading-tight">
              {user?.full_name || user?.username || 'User'}
            </p>
          </div>
        </div>
      </div>
    </header>
  )
}
