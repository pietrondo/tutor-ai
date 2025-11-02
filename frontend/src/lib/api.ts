const API_BASE_URL = process.env.NODE_ENV === 'development'
  ? 'http://localhost:8000'
  : 'http://localhost:8000' // For now, use localhost for both dev and production

export const api = {
  courses: {
    get: (id: string) => `${API_BASE_URL}/courses/${id}`,
    books: (id: string) => `${API_BASE_URL}/courses/${id}/books`,
  }
}

// For backward compatibility, you can also use a direct fetch function
export async function fetchFromBackend(url: string, options?: RequestInit) {
  const fullUrl = url.startsWith('/api/')
    ? `${API_BASE_URL}${url.replace('/api', '')}`
    : `${API_BASE_URL}${url}`

  return fetch(fullUrl, options)
}