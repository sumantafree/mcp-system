'use client'

import { useState, FormEvent } from 'react'
import { useRouter } from 'next/navigation'
import { Eye, EyeOff, CheckCircle, AlertCircle } from 'lucide-react'
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

  const [passwordStrength, setPasswordStrength] = useState(0)

  // 🔥 LIVE VALIDATION
  function handleChange(field: string, value: string) {
    setFormData((prev) => ({ ...prev, [field]: value }))

    if (field === 'password') {
      let strength = 0
      if (value.length >= 6) strength++
      if (/[A-Z]/.test(value)) strength++
      if (/[0-9]/.test(value)) strength++
      setPasswordStrength(strength)
    }
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setError('')

    if (!formData.email || !formData.password) {
      setError('Email and password are required')
      return
    }

    if (formData.password !== formData.confirmPassword) {
      setError('Passwords do not match')
      return
    }

    if (formData.password.length > 72) {
      setError('Password must be less than 72 characters)')
      return
    }

    setIsLoading(true)

    try {
      await auth.register({
        email: formData.email,
        password: formData.password,
        username: formData.username || "",
        full_name: formData.full_name || "",
      })

      setSuccess(true)
      setTimeout(() => router.push('/login'), 2000)

    } catch (err: any) {
      console.error("Register error:", err)

  const backend = err?.response?.data?.detail

  let message = "Registration failed"

  if (Array.isArray(backend)) {
    message = backend[0]?.msg || message
  } else if (typeof backend === "string") {
    message = backend
  }

  setError(message)
      }

      setError(message)

    } finally {
      setIsLoading(false)
    }
  }

  // 🎉 SUCCESS STATE
  if (success) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#0B1120] text-white">
        <div className="text-center">
          <CheckCircle className="mx-auto mb-4 text-green-400" size={48} />
          <h2 className="text-2xl font-semibold">Account Created</h2>
          <p className="text-gray-400 mt-2">Redirecting to login...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-[#0B1120] flex items-center justify-center p-4">

      <div className="w-full max-w-md bg-white/5 backdrop-blur-xl border border-white/10 rounded-2xl p-8 shadow-xl">

        <h1 className="text-2xl font-bold text-white mb-2">Create Account</h1>
        <p className="text-gray-400 mb-6">Start your journey</p>

        {/* ERROR */}
        {error && (
          <div className="flex items-center gap-2 bg-red-500/10 border border-red-500/30 p-3 rounded-lg mb-4">
            <AlertCircle size={18} className="text-red-400" />
            <span className="text-red-400 text-sm">{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">

          <input
            type="text"
            placeholder="Full Name (optional)"
            value={formData.full_name}
            onChange={(e) => handleChange('full_name', e.target.value)}
            className="input"
          />

          <input
            type="text"
            placeholder="Username (optional)"
            value={formData.username}
            onChange={(e) => handleChange('username', e.target.value)}
            className="input"
          />

          <input
            type="email"
            placeholder="Email"
            value={formData.email}
            onChange={(e) => handleChange('email', e.target.value)}
            className="input"
            required
          />

          <div className="relative">
            <input
              type={showPassword ? 'text' : 'password'}
              placeholder="Password"
              value={formData.password}
              onChange={(e) => handleChange('password', e.target.value)}
              className="input pr-10"
              required
            />
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="absolute right-3 top-3 text-gray-400"
            >
              {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
            </button>
          </div>

          {/* 🔥 PASSWORD STRENGTH */}
          <div className="h-2 rounded bg-gray-700 overflow-hidden">
            <div
              className={`h-full transition-all ${
                passwordStrength === 1 ? 'bg-red-500 w-1/3' :
                passwordStrength === 2 ? 'bg-yellow-500 w-2/3' :
                passwordStrength === 3 ? 'bg-green-500 w-full' :
                'w-0'
              }`}
            />
          </div>

          <input
            type="password"
            placeholder="Confirm Password"
            value={formData.confirmPassword}
            onChange={(e) => handleChange('confirmPassword', e.target.value)}
            className="input"
            required
          />

          <button
            type="submit"
            disabled={isLoading}
            className="w-full bg-blue-600 hover:bg-blue-700 transition py-3 rounded-lg font-semibold text-white"
          >
            {isLoading ? "Creating..." : "Create Account"}
          </button>

        </form>

        <p className="text-sm text-gray-400 mt-6 text-center">
          Already have an account?{" "}
          <a href="/login" className="text-blue-400 hover:underline">
            Sign in
          </a>
        </p>
      </div>

      {/* 🔥 GLOBAL INPUT STYLE */}
      <style jsx global>{`
        .input {
          width: 100%;
          background: rgba(255,255,255,0.05);
          border: 1px solid rgba(255,255,255,0.1);
          padding: 12px 14px;
          border-radius: 10px;
          color: white;
          outline: none;
        }
        .input::placeholder {
          color: #9CA3AF;
        }
        .input:focus {
          border-color: #3B82F6;
          box-shadow: 0 0 0 1px #3B82F6;
        }
      `}</style>

    </div>
  )
}