
import React, { useEffect, useMemo, useState } from 'react'
import Spinner from './Spinner'

type LedgerEntry = {
  id: number
  timestamp: number
  sprint_id: string
  manifest_hash: string
  signature: string
}

type ApiResponse = {
  entries: LedgerEntry[]
  total: number
}

const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'

export default function LedgerViewer() {
  const [data, setData] = useState<LedgerEntry[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [updatedAt, setUpdatedAt] = useState<Date | null>(null)

  const fetchData = async () => {
    try {
      setLoading(true)
      setError(null)
      const res = await fetch(`${API_URL}/api/ledger/entries`)
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const json: ApiResponse = await res.json()
      setData(json.entries || [])
      setUpdatedAt(new Date())
    } catch (e: any) {
      setError(e?.message ?? 'Failed to fetch')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchData() }, [])

  const lastUpdated = useMemo(() => updatedAt ? updatedAt.toLocaleString() : '—', [updatedAt])

  if (loading) return <Spinner />

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between gap-3">
        <h2 className="text-xl font-semibold">Sprint Ledger</h2>
        <div className="flex items-center gap-3 text-sm">
          <span className="opacity-70">Last updated: {lastUpdated}</span>
          <button
            onClick={fetchData}
            className="rounded-lg bg-blue-600 px-3 py-1.5 text-white transition hover:bg-blue-700 dark:bg-blue-500 dark:hover:bg-blue-600"
          >
            Refresh
          </button>
        </div>
      </div>

      {error && (
        <div className="rounded-lg border border-red-300 bg-red-50 p-3 text-red-700 dark:border-red-800 dark:bg-red-900/30 dark:text-red-200">
          ⚠️ {error}
        </div>
      )}

      {data.length === 0 ? (
        <div className="rounded-lg border border-gray-200 p-6 text-center text-gray-500 dark:border-gray-700 dark:text-gray-400">
          No ledger entries found.
        </div>
      ) : (
        <ul className="grid gap-3">
          {data.map((e) => (
            <li key={e.id} className="rounded-xl border border-gray-200 p-4 shadow-sm dark:border-gray-800">
              <div className="flex items-center justify-between">
                <div className="text-sm opacity-70">
                  #{e.id} • {new Date(e.timestamp * 1000).toLocaleString()}
                </div>
              </div>
              <div className="mt-2">
                <div className="text-sm opacity-70">Sprint:</div>
                <div className="font-medium">{e.sprint_id}</div>
              </div>
              <div className="mt-2 break-all">
                <div className="text-sm opacity-70">Hash:</div>
                <code className="rounded bg-gray-100 px-2 py-1 text-xs dark:bg-gray-800">
                  {e.manifest_hash}
                </code>
              </div>
              <div className="mt-2 break-all">
                <div className="text-sm opacity-70">Signature:</div>
                <code className="rounded bg-gray-100 px-2 py-1 text-xs dark:bg-gray-800">
                  {e.signature}
                </code>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
