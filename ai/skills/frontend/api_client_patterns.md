# Frontend API Client Patterns

## When to use

- Writing or reviewing code in `frontend/src/api/`
- Adding a new API call from a React component
- Handling authentication tokens, retries, or error normalization in API calls

## Core idea

All HTTP communication must go through a single centralised client module.
Components never instantiate their own `axios` or `fetch` — they import from
the shared client. This ensures consistent auth headers, error handling, and
retry behaviour across the entire application.

---

## Centralised client module

```javascript
// frontend/src/api/client.js
import axios from 'axios'
import { getAccessToken, refreshToken } from './auth'

const client = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  timeout: 30000,
})

// Request interceptor: attach auth token
client.interceptors.request.use(async (config) => {
  const token = await getAccessToken()  // refreshes if expired
  if (token) {
    config.headers['Authorization'] = `Bearer ${token}`
  }
  return config
})

// Response interceptor: normalise errors
client.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (!error.response) {
      // Network error — no HTTP response
      return Promise.reject({ type: 'network', message: 'Network error' })
    }
    const { status, data, headers } = error.response
    // API Gateway / CloudFront may return HTML on 5xx — check content-type
    const isJson = headers['content-type']?.includes('application/json')
    const message = isJson ? (data?.message ?? data?.error) : `HTTP ${status}`
    return Promise.reject({ type: 'api', status, message })
  }
)

export default client
```

---

## Retry with exponential backoff

Retry `5xx` responses automatically. Never retry `4xx` — they indicate a client
error that will not resolve on its own.

```javascript
// frontend/src/api/retry.js
export async function withRetry(fn, maxRetries = 2) {
  let lastError
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await fn()
    } catch (err) {
      if (err.type === 'api' && err.status >= 400 && err.status < 500) {
        throw err  // 4xx: do not retry
      }
      lastError = err
      if (attempt < maxRetries) {
        await new Promise((r) => setTimeout(r, 1000 * Math.pow(2, attempt)))
      }
    }
  }
  throw lastError
}
```

Usage:

```javascript
import client from './client'
import { withRetry } from './retry'

export const uploadDocument = (payload) =>
  withRetry(() => client.post('/upload', payload).then((r) => r.data))
```

---

## Abort controller pattern

Cancel in-flight requests on component unmount to prevent React state updates
after the component is gone:

```javascript
// In a React component or custom hook
import { useEffect, useState } from 'react'
import { getDocumentStatus } from '../api/documents'

export function useDocumentStatus(documentId) {
  const [state, setState] = useState({ data: null, isLoading: true, error: null })

  useEffect(() => {
    const controller = new AbortController()

    getDocumentStatus(documentId, controller.signal)
      .then((data) => setState({ data, isLoading: false, error: null }))
      .catch((err) => {
        if (err.name !== 'CanceledError') {
          setState({ data: null, isLoading: false, error: err })
        }
      })

    return () => controller.abort()
  }, [documentId])

  return state
}
```

Pass `signal` to axios: `client.get(url, { signal })`.

---

## Three-state object pattern

All data-fetching hooks and components must return the same three-state shape.
This is the shared contract across `ChatPage`, `UploadPage`, and similar components:

```javascript
{ data: T | null, isLoading: boolean, error: ApiError | null }
```

- `isLoading: true` → show spinner
- `error !== null` → show error message
- `data !== null` → render content

Never return a two-state shape (loading/data) that silently ignores errors.

---

## Avoid

- Calling `axios.create()` or `fetch()` directly inside components — always use the shared client
- Ignoring `content-type` before calling `.json()` — API Gateway errors can be HTML
- Retrying `4xx` responses — the client sent an invalid request; retrying will not help
- Using `localStorage` for auth tokens — prefer memory storage or `sessionStorage` with a short lifetime
- Forgetting to call `controller.abort()` on unmount — causes React "setState on unmounted component" warnings

## See also

- `ai/skills/frontend/react_vite_aws.md` — `VITE_API_BASE_URL` setup
- `ai/skills/aws/api_gateway.md` — API endpoint structure and CORS
- `ai/skills/frontend/file_upload_ux.md` — presigned URL request flow using this client
