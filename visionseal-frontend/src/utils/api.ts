import axios, { AxiosInstance, AxiosResponse } from 'axios'
import { 
  TenderListResponse, 
  TenderStats, 
  SearchSuggestion, 
  FilterOptions, 
  Tender, 
  TenderFilters,
  ApiResponse,
  ExportResponse,
  ExportOptions
} from '@/types/tender'

// API Configuration
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8080'

// Create axios instance
const api: AxiosInstance = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  timeout: 30000, // Default timeout
  headers: {
    'Content-Type': 'application/json',
  },
})

// Create a separate instance for AI requests with longer timeout
const aiApiInstance: AxiosInstance = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  timeout: 120000, // 2 minutes for AI requests
  headers: {
    'Content-Type': 'application/json',
  },
})

// Setup interceptors for both instances
const setupInterceptors = (instance: AxiosInstance) => {
  // Request interceptor
  instance.interceptors.request.use(
    (config) => {
      // Add auth token if available
      const token = localStorage.getItem('auth_token')
      if (token) {
        config.headers.Authorization = `Bearer ${token}`
      }
      
      // Add request timestamp
      config.headers['X-Request-Time'] = new Date().toISOString()
      
      return config
    },
    (error) => {
      return Promise.reject(error)
    }
  )

  // Response interceptor
  instance.interceptors.response.use(
    (response: AxiosResponse) => {
      return response
    },
    (error) => {
      // Handle common errors
      if (error.response?.status === 401) {
        // Handle unauthorized
        localStorage.removeItem('auth_token')
        window.location.href = '/login'
      }
      
      if (error.response?.status === 429) {
        // Handle rate limiting
        console.warn('Rate limit exceeded. Please try again later.')
      }
      
      return Promise.reject(error)
    }
  )
}

// Apply interceptors to both instances
setupInterceptors(api)
setupInterceptors(aiApiInstance)

// API Functions
export const tenderApi = {
  // Get paginated tenders with filters
  getTenders: async (params: {
    page?: number
    per_page?: number
    search?: string
    source?: string
    country?: string
    organization?: string
    status?: string
    min_relevance?: number
    max_relevance?: number
    deadline_from?: string
    deadline_to?: string
    publication_from?: string
    publication_to?: string
    sort_by?: string
    sort_order?: 'asc' | 'desc'
  } = {}): Promise<TenderListResponse> => {
    const response = await api.get('/tenders', { params })
    return response.data
  },

  // Get single tender by ID
  getTender: async (id: string): Promise<Tender> => {
    const response = await api.get(`/tenders/${id}`)
    return response.data
  },

  // Get tender statistics
  getStats: async (): Promise<TenderStats> => {
    const response = await api.get('/tenders/stats/summary')
    return response.data
  },

  // Get search suggestions
  getSearchSuggestions: async (query: string): Promise<SearchSuggestion[]> => {
    const response = await api.get('/tenders/search/suggestions', {
      params: { q: query }
    })
    return response.data.suggestions || []
  },

  // Get filter options
  getFilterOptions: async (): Promise<FilterOptions> => {
    const response = await api.get('/tenders/filters/options')
    return response.data
  },

  // Export tenders
  exportTenders: async (filters: any = {}, format: 'csv' | 'excel' = 'csv'): Promise<Blob> => {
    const response = await api.get('/tenders/export/csv', {
      params: filters,
      responseType: 'blob'
    })
    return response.data
  },

  // Create new tender (if needed)
  createTender: async (tender: Omit<Tender, 'id' | 'created_at' | 'updated_at'>): Promise<Tender> => {
    const response = await api.post('/tenders', tender)
    return response.data
  },

  // Update tender (if needed)
  updateTender: async (id: string, tender: Partial<Tender>): Promise<Tender> => {
    const response = await api.put(`/tenders/${id}`, tender)
    return response.data
  },

  // Delete tender (if needed)
  deleteTender: async (id: string): Promise<void> => {
    await api.delete(`/tenders/${id}`)
  },
}

// Direct Scraper API (New Simple Implementation)
export const scraperApi = {
  // Start UNGM scraper
  startUNGM: async (config: {
    max_pages?: number
    headless?: boolean
    save_to_supabase?: boolean
  } = {}) => {
    const response = await api.post('/scrapers/ungm/start', {
      max_pages: config.max_pages || 5,
      headless: config.headless !== false,
      save_to_supabase: config.save_to_supabase !== false
    })
    return response.data
  },

  // Start TuniPages scraper
  startTuniPages: async (config: {
    max_pages?: number
    headless?: boolean
    save_to_supabase?: boolean
  } = {}) => {
    const response = await api.post('/scrapers/tunipages/start', {
      max_pages: config.max_pages || 5,
      headless: config.headless !== false,
      save_to_supabase: config.save_to_supabase !== false
    })
    return response.data
  },

  // Get scraper status
  getStatus: async (sessionId: string) => {
    const response = await api.get(`/scrapers/status/${sessionId}`)
    return response.data
  },

  // Get all scraper statuses
  getAllStatuses: async () => {
    const response = await api.get('/scrapers/status')
    return response.data
  }
}

// Automation API (Legacy)
export const automationApi = {
  // Get automation capabilities
  getCapabilities: async () => {
    const response = await api.get('/automation/capabilities')
    return response.data
  },

  // Start scraping session
  startScraping: async (source: string, config: any = {}) => {
    const response = await api.post('/automation/start', {
      source,
      config
    })
    return response.data
  },

  // Get session status
  getSessionStatus: async (sessionId: string) => {
    const response = await api.get(`/automation/sessions/${sessionId}`)
    return response.data
  },

  // Get all sessions
  getSessions: async () => {
    const response = await api.get('/automation/sessions')
    return response.data
  },

  // Stop session
  stopSession: async (sessionId: string) => {
    const response = await api.post(`/automation/sessions/${sessionId}/stop`)
    return response.data
  },

  // Get automation metrics
  getMetrics: async () => {
    const response = await api.get('/automation/metrics')
    return response.data
  },
}

// AI API for report generation with extended timeout
export const aiApi = {
  // Generate AI report with long timeout
  generateReport: async (request: {
    tenderId: string
    reportType: 'proposal' | 'analysis' | 'summary'
    tone: 'professional' | 'technical' | 'persuasive'
    length: 'brief' | 'detailed' | 'comprehensive'
    customInstructions?: string
  }) => {
    const response = await aiApiInstance.post('/ai/generate-report', request)
    return response.data
  },

  // Get AI status
  getStatus: async () => {
    const response = await api.get('/ai/status')
    return response.data
  },

  // Download generated report
  downloadReport: async (filename: string): Promise<Blob> => {
    const response = await api.get(`/ai/download/${filename}`, {
      responseType: 'blob'
    })
    return response.data
  },
}

// Health check
export const healthApi = {
  check: async (): Promise<{ status: string; timestamp: string }> => {
    const response = await api.get('/health')
    return response.data
  },
}

// Generic API utilities
export const apiUtils = {
  // Format API errors
  formatError: (error: any): string => {
    if (error.response?.data?.detail) {
      return error.response.data.detail
    }
    if (error.response?.data?.message) {
      return error.response.data.message
    }
    if (error.message) {
      return error.message
    }
    return 'An unexpected error occurred'
  },

  // Handle API response
  handleResponse: <T>(response: AxiosResponse<ApiResponse<T>>): T => {
    if (response.data.status === 'error') {
      throw new Error(response.data.message)
    }
    return response.data.data
  },

  // Build query string
  buildQueryString: (params: Record<string, any>): string => {
    const filteredParams = Object.entries(params)
      .filter(([_, value]) => value !== undefined && value !== null && value !== '')
      .reduce((acc, [key, value]) => ({ ...acc, [key]: value }), {})
    
    return new URLSearchParams(filteredParams).toString()
  },

  // Debounce function for search
  debounce: <T extends (...args: any[]) => any>(
    func: T,
    delay: number
  ): ((...args: Parameters<T>) => void) => {
    let timeoutId: NodeJS.Timeout
    return (...args: Parameters<T>) => {
      clearTimeout(timeoutId)
      timeoutId = setTimeout(() => func(...args), delay)
    }
  },

  // Format date for API
  formatDate: (date: Date | string): string => {
    if (typeof date === 'string') {
      return new Date(date).toISOString().split('T')[0]
    }
    return date.toISOString().split('T')[0]
  },

  // Parse API date
  parseDate: (dateString: string): Date => {
    return new Date(dateString)
  },

  // Retry failed requests
  retryRequest: async <T>(
    requestFn: () => Promise<T>,
    maxRetries: number = 3,
    delay: number = 1000
  ): Promise<T> => {
    for (let i = 0; i < maxRetries; i++) {
      try {
        return await requestFn()
      } catch (error) {
        if (i === maxRetries - 1) throw error
        await new Promise(resolve => setTimeout(resolve, delay * Math.pow(2, i)))
      }
    }
    throw new Error('Max retries exceeded')
  },
}

// Export the configured axios instance
export default api