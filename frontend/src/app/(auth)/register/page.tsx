'use client'

import { useState, FormEvent } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { Eye, EyeOff, Zap, AlertCircle, CheckCircle } from 'lucide-react'
import { auth } from '@/lib/api'

export default function RegisterPage() {
  const router = useRouter()

  const [formData, setFormData] = useState({
    email: '',
    username: '',
    full_name: '',
    password: '',
    confirmPassword: '',
  })

  const [showPassword, setShowPassword] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState(false)

  function handleChange(field: string, value: string) {
    setFormData((prev) => ({ ...prev, [field]: value }))
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setError('')

    // ✅ Validation
    if (!formData.email || !formData.username || !formData.full_name || !formData.password) {
      setError('All fields are required.')
      return
    }

    if (formData.password !== formData.confirmPassword) {
      setError('Passwords do not match.')
      return
    }

    if (formData.password.length < 8) {
      setError('Password must be at least 8 characters.')
      return
    }

    setIsLoading(true)

    try {
      await auth.register({
        email: formData.email.trim(),
        username: formData.username.trim(),
        full_name: formData.full_name.trim(),
        password: formData.password,

      })

      setSuccess(true)
      setTimeout(() => router.replace('/login'), 2000)

    } catch (err: any) {
      console.error("Register error:", err)

      const backendError = err?.response?.data?.detail

      let message = "Registration failed. Please try again."

      // ✅ FIX: Prevent React crash
      if (Array.isArray(backendError)) {
        message = backendError[0]?.msg
      } else if (typeof backendError === "string") {
        message = backendError
      }

      setError(message)

    } finally {
      setIsLoading(false)
    }
  }

  if (success) {
    return (
      <div className="min-h-screen bg-dark-bg flex items-center justify-center p-4">
        <div className="text-center">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-success/20 rounded-2xl mb-4">
            <CheckCircle className="w-8 h-8 text-success" />
          </div>
          <h2 className="text-2xl font-bold text-dark-heading">Account created!</h2>
          <p className="text-dark-text mt-2">Redirecting to login...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-dark-bg flex items-center justify-center p-4">
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-primary-500/10 rounded-full blur-3xl" />
        <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-purple-500/10 rounded-full blur-3xl" />
      </div>

      <div className="relative w-full max-w-md">

        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-primary-500/20 rounded-2xl mb-4 border border-primary-500/30">
            <Zap className="w-8 h-8 text-primary-400" />
          </div>
          <h1 className="text-3xl font-bold text-dark-heading">MCP System</h1>
          <p className="text-dark-text mt-2">Create your account</p>
        </div>

        <div className="bg-dark-card border border-dark-border rounded-2xl p-8 shadow-2xl">
          <h2 className="text-xl font-semibold text-dark-heading mb-6">Get started for free</h2>

          {error && (
            <div className="flex items-start gap-3 bg-red-500/10 border border-red-500/30 rounded-xl p-4 mb-6">
              <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
              <p className="text-red-400 text-sm">{error}</p>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">

            <input
              type="text"
              placeholder="Full Name"
              value={formData.full_name}
              onChange={(e) => handleChange('full_name', e.target.value)}
              className="input"
              required
            />

            <input
              type="text"
              placeholder="Username"
              value={formData.username}
              onChange={(e) => handleChange('username', e.target.value)}
              className="input"
              required
            />

            <input
              type="email"
              placeholder="Email"
              value={formData.email}
              onChange={(e) => handleChange('email', e.target.value)}
              className="input"
              required
            />

            <input
              type={showPassword ? 'text' : 'password'}
              placeholder="Password"
              value={formData.password}
              onChange={(e) => handleChange('password', e.target.value)}
              className="input"
              required
            />

            <input
              type={showPassword ? 'text' : 'password'}
              placeholder="Confirm Password"
              value={formData.confirmPassword}
              onChange={(e) => handleChange('confirmPassword', e.target.value)}
              className="input"
              required
            />

            <button
              type="submit"
              disabled={isLoading}
              className="w-full bg-primary-500 text-white py-3 rounded-xl"
            >
              {isLoading ? "Creating..." : "Create Account"}
            </button>

          </form>

          <p className="text-center mt-6 text-sm text-dark-text">
            Already have an account?{" "}
            <Link href="/login" className="text-primary-400">
              Sign in
            </Link>
          </p>
        </div>
      </div>
    </div>
  )
}