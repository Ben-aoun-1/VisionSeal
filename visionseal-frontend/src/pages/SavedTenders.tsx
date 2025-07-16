import React, { useState, useMemo, useEffect } from 'react'
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
  Paper,
  useTheme,
  useMediaQuery,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Link,
  Divider,
  CircularProgress
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
  Close as CloseIcon,
  Refresh as RefreshIcon,
  Bookmark as BookmarkIcon,
  BookmarkBorder as BookmarkBorderIcon,
  Delete as DeleteIcon,
  Edit as EditIcon,
  Note as NoteIcon
} from '@mui/icons-material'
import { Helmet } from 'react-helmet-async'
import { useQuery, useMutation, useQueryClient } from 'react-query'
import { useNavigate } from 'react-router-dom'
import { format, parseISO, isValid } from 'date-fns'
import { savedTendersApi } from '@/utils/api'
import { SavedTenderWithDetails, TenderSource, TenderStatus } from '@/types/tender'
import { useAuth } from '@/hooks/useAuth'

const SavedTenders: React.FC = () => {
  const theme = useTheme()
  const isMobile = useMediaQuery(theme.breakpoints.down('md'))
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { isAuthenticated, isLoading: authLoading } = useAuth()

  // State management
  const [page, setPage] = useState(0)
  const [rowsPerPage, setRowsPerPage] = useState(25)
  const [searchQuery, setSearchQuery] = useState('')
  const [sortBy, setSortBy] = useState<string>('saved_at')
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc')
  const [sourceFilter, setSourceFilter] = useState<string>('')
  const [statusFilter, setStatusFilter] = useState<string>('')
  const [sortMenuAnchor, setSortMenuAnchor] = useState<null | HTMLElement>(null)
  const [exportLoading, setExportLoading] = useState(false)
  const [editingNotes, setEditingNotes] = useState<string | null>(null)
  const [notesText, setNotesText] = useState('')
  const [confirmDelete, setConfirmDelete] = useState<string | null>(null)

  // Build query filters
  const queryFilters = useMemo(() => ({
    search: searchQuery || undefined,
    source: sourceFilter || undefined,
    status: statusFilter || undefined,
    page: page + 1,
    per_page: rowsPerPage,
    sort_by: sortBy,
    sort_order: sortOrder,
  }), [searchQuery, sourceFilter, statusFilter, page, rowsPerPage, sortBy, sortOrder])

  // Data fetching
  const {
    data: savedTendersData,
    isLoading,
    error,
    refetch
  } = useQuery(
    ['saved-tenders', queryFilters],
    () => savedTendersApi.getSavedTenders(queryFilters),
    {
      keepPreviousData: true,
      refetchInterval: 30000,
      staleTime: 15000,
    }
  )

  const {
    data: stats
  } = useQuery(
    'saved-tenders-stats',
    savedTendersApi.getSavedTendersStats,
    {
      staleTime: 60000,
    }
  )

  // Mutations
  const unsaveMutation = useMutation(
    (tenderId: string) => savedTendersApi.unsaveTender(tenderId),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('saved-tenders')
        queryClient.invalidateQueries('saved-tenders-stats')
        setConfirmDelete(null)
      },
      onError: (error) => {
        console.error('Failed to unsave tender:', error)
      }
    }
  )

  const updateNotesMutation = useMutation(
    ({ tenderId, notes }: { tenderId: string; notes: string }) => 
      savedTendersApi.updateSavedTender(tenderId, notes),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('saved-tenders')
        setEditingNotes(null)
        setNotesText('')
      },
      onError: (error) => {
        console.error('Failed to update notes:', error)
      }
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
    setPage(0)
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

  const handleExport = async () => {
    setExportLoading(true)
    try {
      const blob = await savedTendersApi.exportSavedTenders()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.style.display = 'none'
      a.href = url
      a.download = 'saved_tenders.csv'
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

  const handleEditNotes = (tenderId: string, currentNotes: string) => {
    setEditingNotes(tenderId)
    setNotesText(currentNotes || '')
  }

  const handleSaveNotes = () => {
    if (editingNotes) {
      updateNotesMutation.mutate({ tenderId: editingNotes, notes: notesText })
    }
  }

  const handleDeleteSavedTender = (tenderId: string) => {
    unsaveMutation.mutate(tenderId)
  }

  const clearFilters = () => {
    setSearchQuery('')
    setSourceFilter('')
    setStatusFilter('')
    setPage(0)
  }

  const activeFiltersCount = [searchQuery, sourceFilter, statusFilter]
    .filter(Boolean).length

  // Redirect to login if not authenticated
  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      navigate('/login')
    }
  }, [isAuthenticated, authLoading, navigate])

  // Show loading if auth is loading
  if (authLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '50vh' }}>
        <CircularProgress />
      </Box>
    )
  }

  // Don't render if not authenticated
  if (!isAuthenticated) {
    return null
  }

  return (
    <Box>
      <Helmet>
        <title>Saved Tenders - VisionSeal</title>
        <meta name="description" content="Your saved tender opportunities" />
      </Helmet>

      {/* Header */}
      <Box sx={{ mb: 3 }}>
        <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 2 }}>
          <Box>
            <Typography variant="h4" gutterBottom>
              Saved Tenders
            </Typography>
            <Typography variant="body1" color="text.secondary">
              {savedTendersData ? `${savedTendersData.total} saved tenders` : 'Loading saved tenders...'}
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
              onClick={handleExport}
              disabled={exportLoading}
              variant="outlined"
            >
              Export CSV
            </Button>
          </Stack>
        </Stack>

        {/* Stats Cards */}
        {stats && (
          <Stack direction={isMobile ? 'column' : 'row'} spacing={2} sx={{ mb: 2 }}>
            <Paper sx={{ p: 2, flex: 1 }}>
              <Typography variant="h6" color="primary">
                {stats.total_saved}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Total Saved
              </Typography>
            </Paper>
            <Paper sx={{ p: 2, flex: 1 }}>
              <Typography variant="h6" color="success.main">
                {stats.recent_saves_count}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Recent Saves (7 days)
              </Typography>
            </Paper>
            <Paper sx={{ p: 2, flex: 1 }}>
              <Typography variant="h6" color="warning.main">
                {stats.avg_relevance_score.toFixed(0)}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Avg Relevance Score
              </Typography>
            </Paper>
          </Stack>
        )}

        {/* Search and Filter Bar */}
        <Card>
          <CardContent>
            <Stack direction={isMobile ? 'column' : 'row'} spacing={2} alignItems="center">
              <TextField
                placeholder="Search saved tenders..."
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
                <TextField
                  select
                  label="Source"
                  value={sourceFilter}
                  onChange={(e) => setSourceFilter(e.target.value)}
                  sx={{ minWidth: 120 }}
                  size="small"
                >
                  <MenuItem value="">All Sources</MenuItem>
                  <MenuItem value="UNGM">UNGM</MenuItem>
                  <MenuItem value="TUNIPAGES">TuniPages</MenuItem>
                  <MenuItem value="MANUAL">Manual</MenuItem>
                </TextField>
                
                <TextField
                  select
                  label="Status"
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                  sx={{ minWidth: 120 }}
                  size="small"
                >
                  <MenuItem value="">All Status</MenuItem>
                  <MenuItem value="ACTIVE">Active</MenuItem>
                  <MenuItem value="EXPIRED">Expired</MenuItem>
                  <MenuItem value="CANCELLED">Cancelled</MenuItem>
                  <MenuItem value="AWARDED">Awarded</MenuItem>
                </TextField>
                
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
                  {sourceFilter && (
                    <Chip
                      label={`Source: ${sourceFilter}`}
                      onDelete={() => setSourceFilter('')}
                      size="small"
                    />
                  )}
                  {statusFilter && (
                    <Chip
                      label={`Status: ${statusFilter}`}
                      onDelete={() => setStatusFilter('')}
                      size="small"
                    />
                  )}
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
          Failed to load saved tenders. Please try again.
        </Alert>
      )}

      {/* Loading State */}
      {isLoading && !savedTendersData && (
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

      {/* Empty State */}
      {savedTendersData && savedTendersData.total === 0 && (
        <Card>
          <CardContent sx={{ textAlign: 'center', py: 8 }}>
            <BookmarkBorderIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
            <Typography variant="h6" gutterBottom>
              No saved tenders yet
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
              Start saving tenders from the main tenders page to see them here.
            </Typography>
            <Button
              variant="contained"
              onClick={() => navigate('/tenders')}
            >
              Browse Tenders
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Saved Tenders Table */}
      {savedTendersData && savedTendersData.total > 0 && (
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
                  <TableCell>Saved</TableCell>
                  <TableCell>Notes</TableCell>
                  <TableCell align="center">Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {savedTendersData.saved_tenders.map((savedTender: SavedTenderWithDetails) => {
                  const daysUntilDeadline = getDaysUntilDeadline(savedTender.deadline)
                  const isUrgent = daysUntilDeadline !== null && daysUntilDeadline <= 7 && daysUntilDeadline >= 0

                  return (
                    <TableRow
                      key={savedTender.tender_id}
                      hover
                      sx={{
                        backgroundColor: isUrgent ? 'rgba(255, 152, 0, 0.1)' : 'inherit',
                        cursor: 'pointer'
                      }}
                      onClick={() => handleViewTender(savedTender.tender_id)}
                    >
                      <TableCell>
                        <Box>
                          <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 0.5 }}>
                            {savedTender.title}
                          </Typography>
                          <Typography variant="body2" color="text.secondary">
                            {savedTender.reference}
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
                            {savedTender.organization || 'N/A'}
                          </Typography>
                        </Box>
                      </TableCell>
                      
                      <TableCell>
                        <Box sx={{ display: 'flex', alignItems: 'center' }}>
                          <PublicIcon sx={{ mr: 1, fontSize: 16, color: 'text.secondary' }} />
                          <Typography variant="body2">
                            {savedTender.country || 'N/A'}
                          </Typography>
                        </Box>
                      </TableCell>
                      
                      <TableCell>
                        <Box sx={{ display: 'flex', alignItems: 'center' }}>
                          <CalendarIcon sx={{ mr: 1, fontSize: 16, color: 'text.secondary' }} />
                          <Box>
                            <Typography variant="body2">
                              {formatDate(savedTender.deadline)}
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
                          label={savedTender.status}
                          color={getStatusColor(savedTender.status)}
                          size="small"
                        />
                      </TableCell>
                      
                      <TableCell>
                        <Chip
                          label={savedTender.source}
                          color={getSourceColor(savedTender.source)}
                          size="small"
                          variant="outlined"
                        />
                      </TableCell>
                      
                      <TableCell>
                        <Box sx={{ display: 'flex', alignItems: 'center' }}>
                          <StarIcon sx={{ mr: 0.5, fontSize: 16, color: 'warning.main' }} />
                          <Typography variant="body2">
                            {savedTender.relevance_score?.toFixed(0) || 'N/A'}
                          </Typography>
                        </Box>
                      </TableCell>
                      
                      <TableCell>
                        <Typography variant="body2" color="text.secondary">
                          {formatDate(savedTender.saved_at)}
                        </Typography>
                      </TableCell>
                      
                      <TableCell>
                        <Box sx={{ maxWidth: 150 }}>
                          {savedTender.notes ? (
                            <Typography variant="body2" sx={{ 
                              overflow: 'hidden', 
                              textOverflow: 'ellipsis',
                              whiteSpace: 'nowrap'
                            }}>
                              {savedTender.notes}
                            </Typography>
                          ) : (
                            <Typography variant="body2" color="text.secondary" sx={{ fontStyle: 'italic' }}>
                              No notes
                            </Typography>
                          )}
                        </Box>
                      </TableCell>
                      
                      <TableCell align="center">
                        <Stack direction="row" spacing={1} justifyContent="center">
                          <Tooltip title="Edit notes">
                            <IconButton
                              size="small"
                              onClick={(e) => {
                                e.stopPropagation()
                                handleEditNotes(savedTender.tender_id, savedTender.notes || '')
                              }}
                            >
                              <EditIcon />
                            </IconButton>
                          </Tooltip>
                          <Tooltip title="View details">
                            <IconButton
                              size="small"
                              onClick={(e) => {
                                e.stopPropagation()
                                handleViewTender(savedTender.tender_id)
                              }}
                            >
                              <ViewIcon />
                            </IconButton>
                          </Tooltip>
                          {savedTender.url && (
                            <Tooltip title="Open original">
                              <IconButton
                                size="small"
                                component={Link}
                                href={savedTender.url}
                                target="_blank"
                                onClick={(e) => e.stopPropagation()}
                              >
                                <ExternalIcon />
                              </IconButton>
                            </Tooltip>
                          )}
                          <Tooltip title="Remove from saved">
                            <IconButton
                              size="small"
                              onClick={(e) => {
                                e.stopPropagation()
                                setConfirmDelete(savedTender.tender_id)
                              }}
                              color="error"
                            >
                              <DeleteIcon />
                            </IconButton>
                          </Tooltip>
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
            count={savedTendersData.total}
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
        <MenuItem onClick={() => handleSortChange('saved_at')}>
          Saved Date {sortBy === 'saved_at' && (sortOrder === 'asc' ? '↑' : '↓')}
        </MenuItem>
        <MenuItem onClick={() => handleSortChange('title')}>
          Title {sortBy === 'title' && (sortOrder === 'asc' ? '↑' : '↓')}
        </MenuItem>
        <MenuItem onClick={() => handleSortChange('deadline')}>
          Deadline {sortBy === 'deadline' && (sortOrder === 'asc' ? '↑' : '↓')}
        </MenuItem>
        <MenuItem onClick={() => handleSortChange('relevance_score')}>
          Relevance Score {sortBy === 'relevance_score' && (sortOrder === 'asc' ? '↑' : '↓')}
        </MenuItem>
        <MenuItem onClick={() => handleSortChange('organization')}>
          Organization {sortBy === 'organization' && (sortOrder === 'asc' ? '↑' : '↓')}
        </MenuItem>
      </Menu>

      {/* Edit Notes Dialog */}
      <Dialog
        open={editingNotes !== null}
        onClose={() => setEditingNotes(null)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Edit Notes</DialogTitle>
        <DialogContent>
          <TextField
            label="Notes"
            multiline
            rows={4}
            value={notesText}
            onChange={(e) => setNotesText(e.target.value)}
            fullWidth
            variant="outlined"
            placeholder="Add your notes about this tender..."
            sx={{ mt: 1 }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditingNotes(null)}>Cancel</Button>
          <Button 
            onClick={handleSaveNotes} 
            variant="contained"
            disabled={updateNotesMutation.isLoading}
          >
            Save Notes
          </Button>
        </DialogActions>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog
        open={confirmDelete !== null}
        onClose={() => setConfirmDelete(null)}
        maxWidth="sm"
      >
        <DialogTitle>Remove Saved Tender</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to remove this tender from your saved list? This action cannot be undone.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setConfirmDelete(null)}>Cancel</Button>
          <Button 
            onClick={() => confirmDelete && handleDeleteSavedTender(confirmDelete)} 
            color="error"
            disabled={unsaveMutation.isLoading}
          >
            Remove
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}

export default SavedTenders