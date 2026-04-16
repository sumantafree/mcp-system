'use client'

import { useEffect, useState } from 'react'
import { useRouter, usePathname } from 'next/navigation'
import Sidebar from '@/components/layout/Sidebar'
import Header from '@/components/layout/Header'
import { auth } from '@/lib/api'

const PAGE_TITLES: Record<string, string> = {
  '/dashboard': 'Dashboard',
  '/tasks': 'Task Manager',
  '/seo': 'SEO Tools',
  '/content': 'Content Creation',
  '/social': 'Social Media',
  '/youtube': 'YouTube Tools',
  '/crm': 'CRM Pipeline',
  '/website': 'Website Tools',
  '/analytics': 'Analytics',
  '/assistant': 'ARIA Assistant',
}

interface User {
  id: number
  email: string
  username: string
  full_name: string
}

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter()
  const pathname = usePathname()
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    const token = localStorage.getItem('mcp_token')
    if (!token) {
      router.replace('/login')
      return
    }
    auth.getMe()
      .then((res) => {
        setUser(res.data)
        setIsLoading(false)
      })
      .catch(() => {
        localStorage.removeItem('mcp_token')
        router.replace('/login')
      })
  }, [router])

  function handleLogout() {
    localStorage.removeItem('mcp_token')
    router.replace('/login')
  }

  const currentTitle = Object.entries(PAGE_TITLES).find(([path]) =>
    pathname === path || (path !== '/dashboard' && pathname.startsWith(path))
  )?.[1] || 'Dashboard'

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-dark-bg">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 border-2 border-primary-500 border-t-transparent rounded-full animate-spin" />
          <span className="text-dark-text">Loading...</span>
        </div>
      </div>
    )
  }

  return (
    <div className="flex h-screen bg-dark-bg overflow-hidden">
      <Sidebar user={user} onLogout={handleLogout} />
      <div className="flex-1 flex flex-col lg:ml-64 overflow-hidden">
        <Header title={currentTitle} user={user} />
        <main className="flex-1 overflow-y-auto p-3 sm:p-4 lg:p-6">
          {children}
        </main>
      </div>
    </div>
  )
}
