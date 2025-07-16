// VisionSeal Tender Types
export interface Tender {
  id: string
  title: string
  description: string
  source: TenderSource
  country: string
  organization: string
  deadline: string | null
  publication_date: string | null
  url: string
  relevance_score: number
  status: TenderStatus
  created_at: string
  updated_at: string
  additional_data?: Record<string, any>
}

export enum TenderSource {
  UNGM = 'UNGM',
  TUNIPAGES = 'TUNIPAGES',
  MANUAL = 'MANUAL',
}

export enum TenderStatus {
  ACTIVE = 'ACTIVE',
  EXPIRED = 'EXPIRED',
  CANCELLED = 'CANCELLED',
  AWARDED = 'AWARDED',
}

export interface TenderFilters {
  search?: string
  source?: TenderSource[]
  country?: string[]
  organization?: string
  status?: TenderStatus[]
  min_relevance?: number
  max_relevance?: number
  deadline_from?: string
  deadline_to?: string
  publication_from?: string
  publication_to?: string
  sort_by?: string
  sort_order?: 'asc' | 'desc'
}

export interface TenderListResponse {
  tenders: Tender[]
  total: number
  page: number
  per_page: number
  total_pages: number
  has_next: boolean
  has_prev: boolean
}

export interface TenderStats {
  total_tenders: number
  active_tenders: number
  expired_tenders: number
  sources_breakdown: Record<string, number>
  countries_breakdown: Record<string, number>
  organizations_breakdown: Record<string, number>
  recent_tenders_count: number
  avg_relevance_score: number
  countries?: string[]
  organizations?: string[]
  average_relevance?: number
}

export interface SearchSuggestion {
  type: string
  value: string
  category: string
}

export interface FilterOptions {
  sources: string[]
  countries: string[]
  organizations: string[]
  statuses: string[]
  relevance_score_range: {
    min: number
    max: number
  }
  date_range: {
    min: string | null
    max: string | null
  }
}

export interface ApiResponse<T> {
  data: T
  message: string
  status: 'success' | 'error'
}

export interface PaginationParams {
  page: number
  per_page: number
}

export interface SortParams {
  sort_by: string
  sort_order: 'asc' | 'desc'
}

// Chart data types
export interface ChartData {
  name: string
  value: number
  color?: string
}

export interface TimeSeriesData {
  date: string
  value: number
}

// UI State types
export interface TenderTableColumn {
  key: keyof Tender
  label: string
  sortable: boolean
  width?: number
  align?: 'left' | 'center' | 'right'
  format?: (value: any) => string
}

export interface TenderCardProps {
  tender: Tender
  onView?: (tender: Tender) => void
  onEdit?: (tender: Tender) => void
  onDelete?: (tender: Tender) => void
  compact?: boolean
}

export interface DashboardWidget {
  id: string
  title: string
  value: string | number
  change?: number
  trend?: 'up' | 'down' | 'neutral'
  color?: string
  icon?: string
}

// Form types
export interface TenderForm {
  title: string
  description: string
  source: TenderSource
  country: string
  organization: string
  deadline: string
  publication_date: string
  url: string
  relevance_score: number
  status: TenderStatus
  additional_data?: Record<string, any>
}

export interface TenderFormErrors {
  title?: string
  description?: string
  source?: string
  country?: string
  organization?: string
  deadline?: string
  publication_date?: string
  url?: string
  relevance_score?: string
  status?: string
}

// Export types
export interface ExportOptions {
  format: 'csv' | 'excel' | 'pdf'
  filters: TenderFilters
  columns: string[]
  filename?: string
}

export interface ExportResponse {
  download_url: string
  filename: string
  expires_at: string
}

// Search types
export interface SearchResults {
  tenders: Tender[]
  total: number
  query: string
  suggestions: SearchSuggestion[]
  facets: {
    sources: Array<{ value: TenderSource; count: number }>
    countries: Array<{ value: string; count: number }>
    organizations: Array<{ value: string; count: number }>
    statuses: Array<{ value: TenderStatus; count: number }>
  }
}

// Utility types
export type TenderField = keyof Tender
export type RequiredTenderFields = 'title' | 'description' | 'source' | 'country' | 'organization'
export type OptionalTenderFields = Exclude<TenderField, RequiredTenderFields>

// Saved Tenders Types
export interface SavedTender {
  id: string
  user_id: string
  tender_id: string
  saved_at: string
  notes?: string
  created_at: string
  updated_at: string
}

export interface SavedTenderWithDetails extends SavedTender {
  saved_tender_id: string
  // Tender details
  title: string
  description?: string
  source: TenderSource
  country: string
  organization: string
  deadline?: string
  publication_date?: string
  url: string
  reference?: string
  status: TenderStatus
  notice_type?: string
  relevance_score: number
  estimated_budget?: string
  currency?: string
  contact_email?: string
  tender_extracted_at: string
  tender_created_at: string
  tender_updated_at: string
}

export interface SavedTenderResponse {
  saved_tenders: SavedTenderWithDetails[]
  total: number
  page: number
  per_page: number
  total_pages: number
  has_next: boolean
  has_prev: boolean
}

export interface SavedTenderStats {
  total_saved: number
  saved_by_status: Record<string, number>
  saved_by_source: Record<string, number>
  recent_saves_count: number
  avg_relevance_score: number
}

export interface SavedTenderCreate {
  tender_id: string
  notes?: string
}

export interface SavedTenderUpdate {
  notes?: string
}

// Hook types
export interface UseTendersOptions {
  filters?: TenderFilters
  pagination?: PaginationParams
  sort?: SortParams
  enabled?: boolean
  refetchInterval?: number
}

export interface UseTendersResult {
  data: TenderListResponse | undefined
  isLoading: boolean
  isError: boolean
  error: Error | null
  refetch: () => void
  fetchNextPage: () => void
  hasNextPage: boolean
  isFetchingNextPage: boolean
}