
import React from 'react'

export default function Spinner() {
  return (
    <div className="flex items-center justify-center py-10">
      <div
        className="h-8 w-8 animate-spin rounded-full border-4 border-gray-300 border-t-transparent dark:border-gray-700 dark:border-t-transparent"
        aria-label="Loading"
        role="status"
      />
    </div>
  )
}
