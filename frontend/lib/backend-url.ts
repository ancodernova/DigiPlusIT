const DEFAULT_BACKEND_URL = 'https://backend-two-chi-77.vercel.app'

export function getBackendUrl(): string {
  const configured = process.env.NEXT_API_URL?.trim()
  const value = configured && !configured.includes('localhost')
    ? configured
    : DEFAULT_BACKEND_URL

  return /^https?:\/\//i.test(value) ? value.replace(/\/+$/, '') : `https://${value.replace(/\/+$/, '')}`
}
