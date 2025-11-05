
import React, { useEffect, useState } from 'react'

function applyTheme(to: 'light' | 'dark') {
  const root = document.documentElement
  if (to === 'dark') root.classList.add('dark')
  else root.classList.remove('dark')
}

export default function ThemeToggle() {
  const [theme, setTheme] = useState<'light' | 'dark'>(() => {
    const saved = localStorage.getItem('theme')
    if (saved === 'light' || saved === 'dark') return saved
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
  })

  useEffect(() => {
    applyTheme(theme)
    localStorage.setItem('theme', theme)
  }, [theme])

  return (
    <button
      onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
      className="rounded-xl border px-3 py-1 text-sm transition hover:opacity-80 border-gray-300 dark:border-gray-700"
      aria-label="Toggle theme"
      title="Toggle theme"
    >
      {theme === 'dark' ? '☀️ Light' : '🌙 Dark'}
    </button>
  )
}
