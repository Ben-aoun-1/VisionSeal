import React, { useState, useEffect, useMemo } from 'react'
import {
  Box,
  Typography,
  Card,
  CardContent,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  TextField,
  InputAdornment,
  IconButton,
  Chip,
  Button,
  Stack,
  Tooltip,
  Skeleton,
  Alert,
  Menu,
  MenuItem,
  Drawer,
  useTheme,
  useMediaQuery,
  FormControl,
  InputLabel,
  Select,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Checkbox,
  FormControlLabel,
  Slider,
  CircularProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Link
} from '@mui/material'
import {
  Search as SearchIcon,
  FilterList as FilterIcon,
  GetApp as ExportIcon,
  Sort as SortIcon,
  Visibility as ViewIcon,
  OpenInNew as ExternalIcon,
  CalendarToday as CalendarIcon,
  Business as BusinessIcon,
  Public as PublicIcon,
  Star as StarIcon,
  ExpandMore as ExpandMoreIcon,
  Close as CloseIcon,
  Refresh as RefreshIcon,
  Bookmark as BookmarkIcon,
  BookmarkBorder as BookmarkBorderIcon
} from '@mui/icons-material'
import { Helmet } from 'react-helmet-async'
import { useQuery } from 'react-query'
import { useNavigate } from 'react-router-dom'
import { format, parseISO, isValid } from 'date-fns'
import { tenderApi, savedTendersApi } from '@/utils/api'
import { Tender, TenderFilters, TenderSource, TenderStatus } from '@/types/tender'
import { useAuth } from '@/hooks/useAuth'

const Tenders: React.FC = () => {
  const theme = useTheme()
  const isMobile = useMediaQuery(theme.breakpoints.down('md'))
  const navigate = useNavigate()

  // State management
  const [page, setPage] = useState(0)
  const [rowsPerPage, setRowsPerPage] = useState(25)
  const [searchQuery, setSearchQuery] = useState('')
  const [sortBy, setSortBy] = useState<string>('deadline')
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc')
  const [filters, setFilters] = useState<TenderFilters>({})
  const [filtersOpen, setFiltersOpen] = useState(false)
  const [sortMenuAnchor, setSortMenuAnchor] = useState<null | HTMLElement>(null)
  const [exportLoading, setExportLoading] = useState(false)
  const [selectedTenders, setSelectedTenders] = useState<string[]>([])
  const [savedTenders, setSavedTenders] = useState<Set<string>>(new Set())
  const [savingTender, setSavingTender] = useState<string | null>(null)

  // Build query filters
  const queryFilters = useMemo(() => ({
    ...filters,
    search: searchQuery || undefined,
    page: page + 1,
    per_page: rowsPerPage,
    sort_by: sortBy,
    sort_order: sortOrder,
  }), [filters, searchQuery, page, rowsPerPage, sortBy, sortOrder])

  // Data fetching
  const {
    data: tendersData,
    isLoading,
    error,
    refetch
  } = useQuery(
    ['tenders', queryFilters],
    () => tenderApi.getTenders(queryFilters),
    {
      keepPreviousData: true,
      refetchInterval: 30000, // Refresh every 30 seconds
      staleTime: 15000, // Consider data stale after 15 seconds
    }
  )

  const {
    data: filterOptions
  } = useQuery(
    'filter-options',
    tenderApi.getFilterOptions,
    {
      staleTime: 300000, // 5 minutes
    }
  )

  // Helper functions
  const formatDate = (dateString: string) => {
    if (!dateString) return 'N/A'
    try {
      const date = parseISO(dateString)
      return isValid(date) ? format(date, 'MMM dd, yyyy') : 'Invalid date'
    } catch {
      return 'Invalid date'
    }
  }

  const getStatusColor = (status: TenderStatus) => {
    switch (status) {
      case 'ACTIVE': return 'success'
      case 'EXPIRED': return 'error'
      case 'CANCELLED': return 'warning'
      case 'AWARDED': return 'info'
      default: return 'default'
    }
  }

  const getSourceColor = (source: TenderSource) => {
    switch (source) {
      case 'UNGM': return 'primary'
      case 'TUNIPAGES': return 'secondary'
      case 'MANUAL': return 'default'
      default: return 'default'
    }
  }

  const getDaysUntilDeadline = (deadline: string) => {
    if (!deadline) return null
    try {
      const deadlineDate = parseISO(deadline)
      const today = new Date()
      const diffTime = deadlineDate.getTime() - today.getTime()
      const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))
      return diffDays
    } catch {
      return null
    }
  }

  // Event handlers
  const handleSearchChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setSearchQuery(event.target.value)
    setPage(0) // Reset to first page when searching
  }

  const handleSortChange = (field: string) => {
    if (sortBy === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')
    } else {
      setSortBy(field)
      setSortOrder('asc')
    }
    setSortMenuAnchor(null)
  }

  const handlePageChange = (_: unknown, newPage: number) => {
    setPage(newPage)
  }

  const handleRowsPerPageChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setRowsPerPage(parseInt(event.target.value, 10))
    setPage(0)
  }

  const handleFilterChange = (filterKey: keyof TenderFilters, value: any) => {
    setFilters(prev => ({
      ...prev,
      [filterKey]: value
    }))
    setPage(0)
  }

  const clearFilters = () => {
    setFilters({})
    setSearchQuery('')
    setPage(0)
  }

  const handleExport = async (format: 'csv' | 'excel') => {
    setExportLoading(true)
    try {
      const blob = await tenderApi.exportTenders(queryFilters, format)
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.style.display = 'none'
      a.href = url
      a.download = `tenders-export.${format === 'csv' ? 'csv' : 'xlsx'}`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
    } catch (error) {
      console.error('Export failed:', error)
    } finally {
      setExportLoading(false)
    }
  }

  const handleViewTender = (tenderId: string) => {
    navigate(`/tenders/${tenderId}`)
  }

  const handleSaveTender = async (tenderId: string) => {
    if (savingTender) return // Prevent multiple saves
    
    setSavingTender(tenderId)
    try {
      if (savedTenders.has(tenderId)) {
        // Unsave tender
        await savedTendersApi.unsaveTender(tenderId)
        setSavedTenders(prev => {
          const newSet = new Set(prev)
          newSet.delete(tenderId)
          return newSet
        })
      } else {
        // Save tender
        await savedTendersApi.saveTender(tenderId)
        setSavedTenders(prev => new Set(prev).add(tenderId))
      }
    } catch (error) {
      console.error('Failed to save/unsave tender:', error)
    } finally {
      setSavingTender(null)
    }
  }

  // Load saved tenders status for current page
  const loadSavedTendersStatus = async () => {
    if (!tendersData?.tenders) return
    
    try {
      const savedChecks = await Promise.all(
        tendersData.tenders.map(tender => 
          savedTendersApi.checkTenderSaved(tender.id)
        )
      )
      
      const savedSet = new Set<string>()
      savedChecks.forEach((check, index) => {
        if (check.is_saved) {
          savedSet.add(tendersData.tenders[index].id)
        }
      })
      
      setSavedTenders(savedSet)
    } catch (error) {
      console.error('Failed to load saved tenders status:', error)
    }
  }

  // Load saved status when tenders data changes
  useEffect(() => {
    loadSavedTendersStatus()
  }, [tendersData?.tenders])

  const activeFiltersCount = Object.values(filters).filter(v => 
    v !== undefined && v !== null && v !== '' && 
    (Array.isArray(v) ? v.length > 0 : true)
  ).length + (searchQuery ? 1 : 0)

  return (
    <Box>
      <Helmet>
        <title>Tenders - VisionSeal</title>
        <meta name="description" content="Browse and search tender opportunities from UNGM and TuniPages" />
      </Helmet>

      {/* Header */}
      <Box sx={{ mb: 3 }}>
        <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 2 }}>
          <Box>
            <Typography variant="h4" gutterBottom>
              Tender Opportunities
            </Typography>
            <Typography variant="body1" color="text.secondary">
              {tendersData ? `${tendersData.total} tenders found` : 'Loading tenders...'}
            </Typography>
          </Box>
          <Stack direction="row" spacing={1}>
            <Tooltip title="Refresh data">
              <IconButton onClick={() => refetch()} disabled={isLoading}>
                <RefreshIcon />
              </IconButton>
            </Tooltip>
            <Button
              startIcon={<ExportIcon />}
              onClick={(e) => {
                const menu = document.createElement('div')
                // Simple export for now
                handleExport('csv')
              }}
              disabled={exportLoading}
            >
              {exportLoading ? <CircularProgress size={20} /> : 'Export'}
            </Button>
          </Stack>
        </Stack>

        {/* Search and Filter Bar */}
        <Card>
          <CardContent>
            <Stack direction={isMobile ? 'column' : 'row'} spacing={2} alignItems="center">
              <TextField
                placeholder="Search tenders..."
                value={searchQuery}
                onChange={handleSearchChange}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <SearchIcon />
                    </InputAdornment>
                  ),
                }}
                sx={{ flexGrow: 1, minWidth: isMobile ? '100%' : 300 }}
              />
              
              <Stack direction="row" spacing={1}>
                <Button
                  startIcon={<FilterIcon />}
                  onClick={() => setFiltersOpen(true)}
                  variant={activeFiltersCount > 0 ? 'contained' : 'outlined'}
                  sx={{ minWidth: 'auto' }}
                >
                  Filters {activeFiltersCount > 0 && `(${activeFiltersCount})`}
                </Button>
                
                <Button
                  startIcon={<SortIcon />}
                  onClick={(e) => setSortMenuAnchor(e.currentTarget)}
                  variant="outlined"
                  sx={{ minWidth: 'auto' }}
                >
                  Sort
                </Button>
              </Stack>
            </Stack>

            {activeFiltersCount > 0 && (
              <Box sx={{ mt: 2 }}>
                <Stack direction="row" spacing={1} alignItems="center" flexWrap="wrap">
                  <Typography variant="body2" color="text.secondary">
                    Active filters:
                  </Typography>
                  {searchQuery && (
                    <Chip
                      label={`Search: ${searchQuery}`}
                      onDelete={() => setSearchQuery('')}
                      size="small"
                    />
                  )}
                  {Object.entries(filters).map(([key, value]) => {
                    if (!value || (Array.isArray(value) && value.length === 0)) return null
                    
                    // Format date range filters
                    let label = `${key}: ${Array.isArray(value) ? value.join(', ') : value}`
                    if (key === 'deadline_from') label = `Deadline from: ${formatDate(value as string)}`
                    if (key === 'deadline_to') label = `Deadline to: ${formatDate(value as string)}`
                    if (key === 'publication_from') label = `Published from: ${formatDate(value as string)}`
                    if (key === 'publication_to') label = `Published to: ${formatDate(value as string)}`
                    if (key === 'min_relevance') label = `Min relevance: ${value}`
                    if (key === 'max_relevance') label = `Max relevance: ${value}`
                    
                    return (
                      <Chip
                        key={key}
                        label={label}
                        onDelete={() => handleFilterChange(key as keyof TenderFilters, undefined)}
                        size="small"
                      />
                    )
                  })}
                  <Button size="small" onClick={clearFilters}>
                    Clear all
                  </Button>
                </Stack>
              </Box>
            )}
          </CardContent>
        </Card>
      </Box>

      {/* Error State */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          Failed to load tenders. Please try again.
        </Alert>
      )}

      {/* Loading State */}
      {isLoading && !tendersData && (
        <Card>
          <CardContent>
            {Array.from({ length: 5 }).map((_, index) => (
              <Box key={index} sx={{ mb: 2 }}>
                <Skeleton variant="text" width="40%" height={24} />
                <Skeleton variant="text" width="60%" />
                <Skeleton variant="text" width="80%" />
              </Box>
            ))}
          </CardContent>
        </Card>
      )}

      {/* Tenders Table */}
      {tendersData && (
        <Card>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Title</TableCell>
                  <TableCell>Organization</TableCell>
                  <TableCell>Country</TableCell>
                  <TableCell>Deadline</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Source</TableCell>
                  <TableCell>Score</TableCell>
                  <TableCell align="center">Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {tendersData.tenders.map((tender: Tender) => {
                  const daysUntilDeadline = getDaysUntilDeadline(tender.deadline)
                  const isUrgent = daysUntilDeadline !== null && daysUntilDeadline <= 7 && daysUntilDeadline >= 0

                  return (
                    <TableRow
                      key={tender.id}
                      hover
                      sx={{
                        backgroundColor: isUrgent ? 'rgba(255, 152, 0, 0.1)' : 'inherit',
                        cursor: 'pointer'
                      }}
                      onClick={() => handleViewTender(tender.id)}
                    >
                      <TableCell>
                        <Box>
                          <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 0.5 }}>
                            {tender.title}
                          </Typography>
                          <Typography variant="body2" color="text.secondary">
                            {tender.reference}
                          </Typography>
                          {isUrgent && (
                            <Chip
                              label={`${daysUntilDeadline} days left`}
                              color="warning"
                              size="small"
                              sx={{ mt: 0.5 }}
                            />
                          )}
                        </Box>
                      </TableCell>
                      
                      <TableCell>
                        <Box sx={{ display: 'flex', alignItems: 'center' }}>
                          <BusinessIcon sx={{ mr: 1, fontSize: 16, color: 'text.secondary' }} />
                          <Typography variant="body2">
                            {tender.organization || 'N/A'}
                          </Typography>
                        </Box>
                      </TableCell>
                      
                      <TableCell>
                        <Box sx={{ display: 'flex', alignItems: 'center' }}>
                          <PublicIcon sx={{ mr: 1, fontSize: 16, color: 'text.secondary' }} />
                          <Typography variant="body2">
                            {tender.country || 'N/A'}
                          </Typography>
                        </Box>
                      </TableCell>
                      
                      <TableCell>
                        <Box sx={{ display: 'flex', alignItems: 'center' }}>
                          <CalendarIcon sx={{ mr: 1, fontSize: 16, color: 'text.secondary' }} />
                          <Box>
                            <Typography variant="body2">
                              {formatDate(tender.deadline)}
                            </Typography>
                            {daysUntilDeadline !== null && (
                              <Typography variant="caption" color="text.secondary">
                                {daysUntilDeadline > 0 ? `${daysUntilDeadline} days left` : 
                                 daysUntilDeadline === 0 ? 'Due today' : 'Expired'}
                              </Typography>
                            )}
                          </Box>
                        </Box>
                      </TableCell>
                      
                      <TableCell>
                        <Chip
                          label={tender.status}
                          color={getStatusColor(tender.status)}
                          size="small"
                        />
                      </TableCell>
                      
                      <TableCell>
                        <Chip
                          label={tender.source}
                          color={getSourceColor(tender.source)}
                          size="small"
                          variant="outlined"
                        />
                      </TableCell>
                      
                      <TableCell>
                        <Box sx={{ display: 'flex', alignItems: 'center' }}>
                          <StarIcon sx={{ mr: 0.5, fontSize: 16, color: 'warning.main' }} />
                          <Typography variant="body2">
                            {tender.relevance_score?.toFixed(0) || 'N/A'}
                          </Typography>
                        </Box>
                      </TableCell>
                      
                      <TableCell align="center">
                        <Stack direction="row" spacing={1} justifyContent="center">
                          <Tooltip title={savedTenders.has(tender.id) ? "Remove from saved" : "Save tender"}>
                            <IconButton
                              size="small"
                              onClick={(e) => {
                                e.stopPropagation()
                                handleSaveTender(tender.id)
                              }}
                              disabled={savingTender === tender.id}
                              color={savedTenders.has(tender.id) ? "primary" : "default"}
                            >
                              {savingTender === tender.id ? (
                                <CircularProgress size={16} />
                              ) : savedTenders.has(tender.id) ? (
                                <BookmarkIcon />
                              ) : (
                                <BookmarkBorderIcon />
                              )}
                            </IconButton>
                          </Tooltip>
                          <Tooltip title="View details">
                            <IconButton
                              size="small"
                              onClick={(e) => {
                                e.stopPropagation()
                                handleViewTender(tender.id)
                              }}
                            >
                              <ViewIcon />
                            </IconButton>
                          </Tooltip>
                          {tender.url && (
                            <Tooltip title="Open original">
                              <IconButton
                                size="small"
                                component={Link}
                                href={tender.url}
                                target="_blank"
                                onClick={(e) => e.stopPropagation()}
                              >
                                <ExternalIcon />
                              </IconButton>
                            </Tooltip>
                          )}
                        </Stack>
                      </TableCell>
                    </TableRow>
                  )
                })}
              </TableBody>
            </Table>
          </TableContainer>

          {/* Pagination */}
          <TablePagination
            rowsPerPageOptions={[10, 25, 50, 100]}
            component="div"
            count={tendersData.total}
            rowsPerPage={rowsPerPage}
            page={page}
            onPageChange={handlePageChange}
            onRowsPerPageChange={handleRowsPerPageChange}
          />
        </Card>
      )}

      {/* Sort Menu */}
      <Menu
        anchorEl={sortMenuAnchor}
        open={Boolean(sortMenuAnchor)}
        onClose={() => setSortMenuAnchor(null)}
      >
        <MenuItem onClick={() => handleSortChange('title')}>
          Title {sortBy === 'title' && (sortOrder === 'asc' ? '↑' : '↓')}
        </MenuItem>
        <MenuItem onClick={() => handleSortChange('deadline')}>
          Deadline {sortBy === 'deadline' && (sortOrder === 'asc' ? '↑' : '↓')}
        </MenuItem>
        <MenuItem onClick={() => handleSortChange('relevance_score')}>
          Relevance Score {sortBy === 'relevance_score' && (sortOrder === 'asc' ? '↑' : '↓')}
        </MenuItem>
        <MenuItem onClick={() => handleSortChange('publication_date')}>
          Publication Date {sortBy === 'publication_date' && (sortOrder === 'asc' ? '↑' : '↓')}
        </MenuItem>
        <MenuItem onClick={() => handleSortChange('organization')}>
          Organization {sortBy === 'organization' && (sortOrder === 'asc' ? '↑' : '↓')}
        </MenuItem>
      </Menu>

      {/* Filters Drawer */}
      <Drawer
        anchor="right"
        open={filtersOpen}
        onClose={() => setFiltersOpen(false)}
        PaperProps={{
          sx: { width: { xs: '100%', sm: 400 } }
        }}
      >
        <Box sx={{ p: 3 }}>
          <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 3 }}>
            <Typography variant="h6">Filter Tenders</Typography>
            <IconButton onClick={() => setFiltersOpen(false)}>
              <CloseIcon />
            </IconButton>
          </Stack>

          <Stack spacing={3}>
            {/* Status Filter */}
            <FormControl fullWidth>
              <InputLabel>Status</InputLabel>
              <Select
                multiple
                value={filters.status || []}
                onChange={(e) => handleFilterChange('status', e.target.value)}
                renderValue={(selected) => (
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                    {(selected as string[]).map((value) => (
                      <Chip key={value} label={value} size="small" />
                    ))}
                  </Box>
                )}
              >
                <MenuItem value="ACTIVE">Active</MenuItem>
                <MenuItem value="EXPIRED">Expired</MenuItem>
                <MenuItem value="CANCELLED">Cancelled</MenuItem>
                <MenuItem value="AWARDED">Awarded</MenuItem>
              </Select>
            </FormControl>

            {/* Source Filter */}
            <FormControl fullWidth>
              <InputLabel>Source</InputLabel>
              <Select
                multiple
                value={filters.source || []}
                onChange={(e) => handleFilterChange('source', e.target.value)}
                renderValue={(selected) => (
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                    {(selected as string[]).map((value) => (
                      <Chip key={value} label={value} size="small" />
                    ))}
                  </Box>
                )}
              >
                <MenuItem value="UNGM">UNGM</MenuItem>
                <MenuItem value="TUNIPAGES">TuniPages</MenuItem>
                <MenuItem value="MANUAL">Manual</MenuItem>
              </Select>
            </FormControl>

            {/* Countries Filter */}
            <FormControl fullWidth>
              <InputLabel>Countries</InputLabel>
              <Select
                multiple
                value={filters.country || []}
                onChange={(e) => handleFilterChange('country', e.target.value)}
                renderValue={(selected) => (
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                    {(selected as string[]).map((value) => (
                      <Chip key={value} label={value} size="small" />
                    ))}
                  </Box>
                )}
              >
                {filterOptions?.countries?.map((country) => (
                  <MenuItem key={country} value={country}>
                    {country}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            {/* Relevance Score Filter */}
            <Box>
              <Typography gutterBottom>
                Relevance Score: {filters.min_relevance || 0} - {filters.max_relevance || 100}
              </Typography>
              <Slider
                value={[filters.min_relevance || 0, filters.max_relevance || 100]}
                onChange={(_, value) => {
                  const [min, max] = value as number[]
                  handleFilterChange('min_relevance', min)
                  handleFilterChange('max_relevance', max)
                }}
                valueLabelDisplay="auto"
                min={0}
                max={100}
              />
            </Box>

            {/* Date Range Filters */}
            <Accordion>
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <Typography>Date Filters</Typography>
              </AccordionSummary>
              <AccordionDetails>
                <Stack spacing={2}>
                  {/* Deadline Date Range */}
                  <Typography variant="subtitle2" gutterBottom>
                    Deadline Range
                  </Typography>
                  <Stack direction="row" spacing={2}>
                    <TextField
                      label="From"
                      type="date"
                      value={filters.deadline_from || ''}
                      onChange={(e) => handleFilterChange('deadline_from', e.target.value || undefined)}
                      InputLabelProps={{ shrink: true }}
                      fullWidth
                    />
                    <TextField
                      label="To"
                      type="date"
                      value={filters.deadline_to || ''}
                      onChange={(e) => handleFilterChange('deadline_to', e.target.value || undefined)}
                      InputLabelProps={{ shrink: true }}
                      fullWidth
                    />
                  </Stack>
                  
                  {/* Publication Date Range */}
                  <Typography variant="subtitle2" gutterBottom sx={{ mt: 2 }}>
                    Publication Range
                  </Typography>
                  <Stack direction="row" spacing={2}>
                    <TextField
                      label="From"
                      type="date"
                      value={filters.publication_from || ''}
                      onChange={(e) => handleFilterChange('publication_from', e.target.value || undefined)}
                      InputLabelProps={{ shrink: true }}
                      fullWidth
                    />
                    <TextField
                      label="To"
                      type="date"
                      value={filters.publication_to || ''}
                      onChange={(e) => handleFilterChange('publication_to', e.target.value || undefined)}
                      InputLabelProps={{ shrink: true }}
                      fullWidth
                    />
                  </Stack>
                </Stack>
              </AccordionDetails>
            </Accordion>

            {/* Clear Filters */}
            <Button
              variant="outlined"
              onClick={clearFilters}
              fullWidth
            >
              Clear All Filters
            </Button>
          </Stack>
        </Box>
      </Drawer>
    </Box>
  )
}

export default Tenders