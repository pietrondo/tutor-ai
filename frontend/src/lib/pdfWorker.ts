import { pdfjs } from 'react-pdf'

type WorkerStrategy = 'direct' | 'blob'

export interface WorkerAttemptLog {
  url: string
  success: boolean
  via: 'head' | WorkerStrategy
  status?: number
  error?: string
}

export interface WorkerConfigResult {
  workerSrc: string
  strategy: WorkerStrategy
  attempts: WorkerAttemptLog[]
}

interface WorkerCandidate {
  url: string
  label: string
  forceBlob?: boolean
}

const API_BASE_URL = (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000').replace(/\/+$/, '')
const PDFJS_VERSION = process.env.NEXT_PUBLIC_PDFJS_VERSION || '3.11.174'

const workerCandidates: WorkerCandidate[] = [
  { url: '/pdf.worker.min.js', label: 'frontend-public' },
  { url: `${API_BASE_URL}/pdf.worker.min.js`, label: 'backend-static' },
  { url: `https://unpkg.com/pdfjs-dist@${PDFJS_VERSION}/build/pdf.worker.min.js`, label: 'cdn', forceBlob: true }
]

let configurePromise: Promise<WorkerConfigResult> | null = null
let cachedResult: WorkerConfigResult | null = null
let activeBlobUrl: string | null = null

const isClient = typeof window !== 'undefined'

function applyWorkerSrc(src: string, strategy: WorkerStrategy) {
  if (!isClient) return

  if (strategy === 'direct' && activeBlobUrl) {
    URL.revokeObjectURL(activeBlobUrl)
    activeBlobUrl = null
  }

  if (strategy === 'blob') {
    if (activeBlobUrl) {
      URL.revokeObjectURL(activeBlobUrl)
    }
    activeBlobUrl = src
  }

  pdfjs.GlobalWorkerOptions.workerSrc = src
}

async function testCandidate(candidate: WorkerCandidate, attempts: WorkerAttemptLog[]): Promise<{ src: string; strategy: WorkerStrategy } | null> {
  // Try HEAD first to avoid downloading the entire worker unnecessarily
  try {
    const headResponse = await fetch(candidate.url, { method: 'HEAD', mode: 'cors' })
    if (headResponse.ok) {
      attempts.push({ url: candidate.url, success: true, via: 'head', status: headResponse.status })
      if (!candidate.forceBlob) {
        return { src: candidate.url, strategy: 'direct' }
      }
      // Candidate requires blob usage, so continue with GET to inline the worker
      console.info(`[pdf-worker] ${candidate.label} reachable, creating blob fallback`)
    }
    attempts.push({ url: candidate.url, success: false, via: 'head', status: headResponse.status })
  } catch (error) {
    attempts.push({
      url: candidate.url,
      success: false,
      via: 'head',
      error: error instanceof Error ? error.message : String(error)
    })
  }

  // HEAD failed or was blocked, fall back to GET
  try {
    const response = await fetch(candidate.url, { method: 'GET', mode: 'cors' })
    if (!response.ok) {
      attempts.push({ url: candidate.url, success: false, via: candidate.forceBlob ? 'blob' : 'direct', status: response.status })
      return null
    }

    if (candidate.forceBlob) {
      const blob = await response.blob()
      const blobUrl = URL.createObjectURL(blob)
      attempts.push({ url: candidate.url, success: true, via: 'blob', status: response.status })
      return { src: blobUrl, strategy: 'blob' }
    }

    attempts.push({ url: candidate.url, success: true, via: 'direct', status: response.status })
    return { src: candidate.url, strategy: 'direct' }
  } catch (error) {
    attempts.push({
      url: candidate.url,
      success: false,
      via: candidate.forceBlob ? 'blob' : 'direct',
      error: error instanceof Error ? error.message : String(error)
    })
  }

  return null
}

async function configureWorker(): Promise<WorkerConfigResult> {
  if (!isClient) {
    throw new Error('PDF.js worker can only be configured in the browser')
  }

  // If another script already configured the worker, reuse it
  if (pdfjs?.GlobalWorkerOptions?.workerSrc && cachedResult && !cachedResult.workerSrc.startsWith('blob:')) {
    return cachedResult
  }

  const attempts: WorkerAttemptLog[] = []

  for (const candidate of workerCandidates) {
    const result = await testCandidate(candidate, attempts)
    if (result) {
      applyWorkerSrc(result.src, result.strategy)
      const configResult: WorkerConfigResult = {
        workerSrc: result.src,
        strategy: result.strategy,
        attempts
      }
      cachedResult = configResult
      console.info(`[pdf-worker] using ${candidate.label} (${result.strategy}) -> ${result.src}`)
      return configResult
    }
  }

  throw new Error('Unable to configure PDF.js worker. See attempts for details.')
}

export async function ensurePdfWorkerConfigured(force = false): Promise<WorkerConfigResult> {
  if (!isClient) {
    return Promise.reject(new Error('PDF.js worker can only be configured client-side'))
  }

  if (!force && cachedResult && pdfjs?.GlobalWorkerOptions?.workerSrc) {
    return cachedResult
  }

  if (!configurePromise || force) {
    configurePromise = configureWorker().finally(() => {
      configurePromise = null
    })
  }

  return configurePromise
}

export function getWorkerDiagnostics(): WorkerConfigResult | null {
  return cachedResult
}
