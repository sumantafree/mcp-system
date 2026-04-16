'use client'

import { useState } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import {
  LayoutDashboard,
  CheckSquare,
  Search,
  FileText,
  Share2,
  Play,
  Users,
  Globe,
  BarChart3,
  Bot,
  Zap,
  LogOut,
  Menu,
  X,
  ChevronRight,
} from 'lucide-react'
import { cn, getInitials } from '@/lib/utils'

interface NavItem {
  label: string
  href: string
  icon: React.ElementType
  badge?: number
}

const navItems: NavItem[] = [
  { label: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
  { label: 'Tasks', href: '/tasks', icon: CheckSquare },
  { label: 'SEO Tools', href: '/seo', icon: Search },
  { label: 'Content', href: '/content', icon: FileText },
  { label: 'Social Media', href: '/social', icon: Share2 },
  { label: 'YouTube', href: '/youtube', icon: Play },
  { label: 'CRM', href: '/crm', icon: Users },
  { label: 'Website', href: '/website', icon: Globe },
  { label: 'Analytics', href: '/analytics', icon: BarChart3 },
  { label: 'ARIA Assistant', href: '/assistant', icon: Bot },
]

interface SidebarProps {
  user?: { full_name?: string; email?: string; username?: string } | null
  onLogout?: () => void
}

export default function Sidebar({ user, onLogout }: SidebarProps) {
  const pathname = usePathname()
  const [mobileOpen, setMobileOpen] = useState(false)

  const SidebarContent = () => (
    <div className="flex flex-col h-full">
      {/* Logo */}
      <div className="flex items-center gap-3 px-6 py-5 border-b border-dark-border">
        <div className="w-9 h-9 bg-primary-500/20 border border-primary-500/30 rounded-xl flex items-center justify-center flex-shrink-0">
          <Zap className="w-5 h-5 text-primary-400" />
        </div>
        <div>
          <h1 className="text-base font-bold text-dark-heading leading-tight">MCP System</h1>
          <p className="text-xs text-dark-text">AI Dashboard</p>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto py-4 px-3">
        <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider px-3 mb-3">
          Main Menu
        </p>
        <ul className="space-y-1">
          {navItems.map((item) => {
            const isActive =
              pathname === item.href ||
              (item.href !== '/dashboard' && pathname.startsWith(item.href))
            const Icon = item.icon
            return (
              <li key={item.href}>
                <Link
                  href={item.href}
                  onClick={() => setMobileOpen(false)}
                  className={cn(
                    'flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all group',
                    isActive
                      ? 'bg-primary-500/20 text-primary-400 border border-primary-500/20'
                      : 'text-dark-text hover:bg-dark-card hover:text-dark-heading'
                  )}
                >
                  <Icon
                    className={cn(
                      'w-5 h-5 flex-shrink-0 transition-colors',
                      isActive ? 'text-primary-400' : 'text-slate-500 group-hover:text-dark-text'
                    )}
                  />
                  <span className="flex-1">{item.label}</span>
                  {isActive && (
                    <ChevronRight className="w-4 h-4 text-primary-400/60" />
                  )}
                  {item.badge && !isActive && (
                    <span className="bg-red-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">
                      {item.badge}
                    </span>
                  )}
                </Link>
              </li>
            )
          })}
        </ul>
      </nav>

      {/* User section */}
      <div className="border-t border-dark-border p-4">
        <div className="flex items-center gap-3 px-2 py-2 rounded-xl hover:bg-dark-card transition cursor-pointer group">
          <div className="w-8 h-8 rounded-full bg-primary-500/30 border border-primary-500/30 flex items-center justify-center flex-shrink-0">
            <span className="text-xs font-bold text-primary-400">
              {getInitials(user?.full_name || user?.username || 'U')}
            </span>
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-dark-heading truncate">
              {user?.full_name || user?.username || 'User'}
            </p>
            <p className="text-xs text-dark-text truncate">{user?.email || ''}</p>
          </div>
          <button
            onClick={onLogout}
            className="text-dark-text hover:text-red-400 transition p-1 rounded"
            title="Sign out"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  )

  return (
    <>
      {/* Mobile toggle button */}
      <button
        onClick={() => setMobileOpen(true)}
        className="lg:hidden fixed top-4 left-4 z-50 p-2 bg-dark-card border border-dark-border rounded-xl text-dark-text hover:text-dark-heading transition"
      >
        <Menu className="w-5 h-5" />
      </button>

      {/* Mobile overlay */}
      {mobileOpen && (
        <div
          className="lg:hidden fixed inset-0 z-40 bg-black/60 backdrop-blur-sm"
          onClick={() => setMobileOpen(false)}
        />
      )}

      {/* Mobile sidebar */}
      <div
        className={cn(
          'lg:hidden fixed inset-y-0 left-0 z-50 w-72 bg-dark-sidebar border-r border-dark-border transform transition-transform duration-300',
          mobileOpen ? 'translate-x-0' : '-translate-x-full'
        )}
      >
        <button
          onClick={() => setMobileOpen(false)}
          className="absolute top-4 right-4 text-dark-text hover:text-dark-heading transition"
        >
          <X className="w-5 h-5" />
        </button>
        <SidebarContent />
      </div>

      {/* Desktop sidebar */}
      <div className="hidden lg:flex flex-col w-64 bg-dark-sidebar border-r border-dark-border h-screen fixed left-0 top-0 z-30">
        <SidebarContent />
      </div>
    </>
  )
}
