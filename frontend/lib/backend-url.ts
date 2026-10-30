export function getBackendUrl(): string {
  const configured = process.env.NEXT_API_URL?.trim()
  if (!configured) throw new Error('NEXT_API_URL is not configured.')
  const value = configured
  return /^https?:\/\//i.test(value) ? value.replace(/\/+$/, '') : `https://${value.replace(/\/+$/, '')}`
}
