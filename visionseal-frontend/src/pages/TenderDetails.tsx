import React, { useState } from 'react'
import {
  Box,
  Typography,
  Card,
  CardContent,
  Stack,
  Chip,
  Button,
  IconButton,
  Divider,
  Grid,
  Link,
  Alert,
  Skeleton,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Breadcrumbs,
  useTheme,
  useMediaQuery,
  Paper,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField
} from '@mui/material'
import {
  ArrowBack as ArrowBackIcon,
  OpenInNew as ExternalIcon,
  Star as StarIcon,
  CalendarToday as CalendarIcon,
  Business as BusinessIcon,
  Public as PublicIcon,
  Description as DescriptionIcon,
  AttachFile as AttachFileIcon,
  Email as EmailIcon,
  Link as LinkIcon,
  Warning as WarningIcon,
  CheckCircle as CheckCircleIcon,
  ExpandMore as ExpandMoreIcon,
  Share as ShareIcon,
  Bookmark as BookmarkIcon,
  Print as PrintIcon,
  GetApp as DownloadIcon,
  NavigateNext as NavigateNextIcon
} from '@mui/icons-material'
import { Helmet } from 'react-helmet-async'
import { useQuery } from 'react-query'
import { useParams, useNavigate, Link as RouterLink } from 'react-router-dom'
import { format, parseISO, isValid, differenceInDays } from 'date-fns'
import { tenderApi } from '@/utils/api'
import { Tender, TenderStatus } from '@/types/tender'

const TenderDetails: React.FC = () => {
  const theme = useTheme()
  const isMobile = useMediaQuery(theme.breakpoints.down('md'))
  const navigate = useNavigate()
  const { id } = useParams<{ id: string }>()
  
  const [shareDialogOpen, setShareDialogOpen] = useState(false)
  const [isBookmarked, setIsBookmarked] = useState(false)

  // Data fetching
  const {
    data: tender,
    isLoading,
    error
  } = useQuery(
    ['tender', id],
    () => tenderApi.getTender(id!),
    {
      enabled: !!id,
      staleTime: 60000, // 1 minute
    }
  )

  // Helper functions
  const formatDate = (dateString: string) => {
    if (!dateString) return 'Not specified'
    try {
      const date = parseISO(dateString)
      return isValid(date) ? format(date, 'MMMM dd, yyyy') : 'Invalid date'
    } catch {
      return 'Invalid date'
    }
  }

  const getTimeLeft = (deadline: string) => {
    if (!deadline) return null
    try {
      const deadlineDate = parseISO(deadline)
      const today = new Date()
      const daysLeft = differenceInDays(deadlineDate, today)
      
      if (daysLeft < 0) return { text: 'Expired', color: 'error', urgent: false }
      if (daysLeft === 0) return { text: 'Due today', color: 'error', urgent: true }
      if (daysLeft <= 3) return { text: `${daysLeft} days left`, color: 'warning', urgent: true }
      if (daysLeft <= 7) return { text: `${daysLeft} days left`, color: 'warning', urgent: false }
      return { text: `${daysLeft} days left`, color: 'success', urgent: false }
    } catch {
      return null
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

  const getSourceColor = (source: string) => {
    switch (source) {
      case 'UNGM': return 'primary'
      case 'TUNIPAGES': return 'secondary'
      case 'MANUAL': return 'default'
      default: return 'default'
    }
  }

  const getRelevanceScoreColor = (score: number) => {
    if (score >= 80) return 'success'
    if (score >= 60) return 'warning'
    return 'error'
  }

  const handleShareTender = () => {
    if (navigator.share && tender) {
      navigator.share({
        title: tender.title,
        text: `Check out this tender opportunity: ${tender.title}`,
        url: window.location.href,
      })
    } else {
      setShareDialogOpen(true)
    }
  }

  const handleBookmark = () => {
    setIsBookmarked(!isBookmarked)
    // TODO: Implement actual bookmarking logic
  }

  const handlePrint = () => {
    window.print()
  }

  if (isLoading) {
    return (
      <Box>
        <Skeleton variant="text" width="60%" height={40} sx={{ mb: 2 }} />
        <Skeleton variant="rectangular" height={200} sx={{ mb: 2 }} />
        <Skeleton variant="rectangular" height={300} />
      </Box>
    )
  }

  if (error || !tender) {
    return (
      <Box>
        <Alert severity="error" sx={{ mb: 3 }}>
          {error ? 'Failed to load tender details' : 'Tender not found'}
        </Alert>
        <Button startIcon={<ArrowBackIcon />} onClick={() => navigate('/tenders')}>
          Back to Tenders
        </Button>
      </Box>
    )
  }

  const timeLeft = getTimeLeft(tender.deadline)

  return (
    <Box>
      <Helmet>
        <title>{tender.title} - VisionSeal</title>
        <meta name="description" content={`Tender details for ${tender.title} by ${tender.organization}`} />
      </Helmet>

      {/* Breadcrumbs */}
      <Breadcrumbs 
        separator={<NavigateNextIcon fontSize="small" />} 
        aria-label="breadcrumb"
        sx={{ mb: 3 }}
      >
        <Link component={RouterLink} to="/dashboard" underline="hover">
          Dashboard
        </Link>
        <Link component={RouterLink} to="/tenders" underline="hover">
          Tenders
        </Link>
        <Typography color="text.primary">Details</Typography>
      </Breadcrumbs>

      {/* Header */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Stack direction="row" justifyContent="space-between" alignItems="flex-start" sx={{ mb: 2 }}>
            <IconButton 
              onClick={() => navigate('/tenders')}
              sx={{ mr: 2, mt: -1 }}
            >
              <ArrowBackIcon />
            </IconButton>
            <Box sx={{ flexGrow: 1 }}>
              <Typography variant="h4" gutterBottom>
                {tender.title}
              </Typography>
              <Typography variant="body1" color="text.secondary" sx={{ mb: 2 }}>
                Reference: {tender.reference || 'N/A'}
              </Typography>
            </Box>
            
            {/* Action Buttons */}
            <Stack direction="row" spacing={1}>
              <Tooltip title="Share">
                <IconButton onClick={handleShareTender}>
                  <ShareIcon />
                </IconButton>
              </Tooltip>
              <Tooltip title={isBookmarked ? 'Remove bookmark' : 'Bookmark'}>
                <IconButton onClick={handleBookmark} color={isBookmarked ? 'primary' : 'default'}>
                  <BookmarkIcon />
                </IconButton>
              </Tooltip>
              <Tooltip title="Print">
                <IconButton onClick={handlePrint}>
                  <PrintIcon />
                </IconButton>
              </Tooltip>
            </Stack>
          </Stack>

          {/* Status and Urgency Alerts */}
          {timeLeft?.urgent && (
            <Alert 
              severity={timeLeft.color as any} 
              icon={<WarningIcon />}
              sx={{ mb: 2 }}
            >
              <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                Urgent: {timeLeft.text}
              </Typography>
              <Typography variant="body2">
                This tender deadline is approaching soon. Take action immediately.
              </Typography>
            </Alert>
          )}

          {/* Key Information Chips */}
          <Stack direction="row" spacing={1} flexWrap="wrap" sx={{ mb: 3 }}>
            <Chip
              label={tender.status}
              color={getStatusColor(tender.status)}
              icon={<CheckCircleIcon />}
            />
            <Chip
              label={tender.source}
              color={getSourceColor(tender.source)}
              variant="outlined"
            />
            {timeLeft && (
              <Chip
                label={timeLeft.text}
                color={timeLeft.color as any}
                icon={<CalendarIcon />}
              />
            )}
            {tender.relevance_score && (
              <Chip
                label={`Score: ${tender.relevance_score.toFixed(0)}`}
                color={getRelevanceScoreColor(tender.relevance_score)}
                icon={<StarIcon />}
              />
            )}
          </Stack>

          {/* Quick Actions */}
          <Stack direction={isMobile ? 'column' : 'row'} spacing={2}>
            {tender.url && (
              <Button
                variant="contained"
                startIcon={<ExternalIcon />}
                component={Link}
                href={tender.url}
                target="_blank"
                size="large"
              >
                View Original Tender
              </Button>
            )}
            <Button
              variant="outlined"
              startIcon={<DownloadIcon />}
              onClick={() => {
                // TODO: Implement tender download as PDF
                console.log('Download tender details')
              }}
            >
              Download Details
            </Button>
          </Stack>
        </CardContent>
      </Card>

      <Grid container spacing={3}>
        {/* Main Information */}
        <Grid item xs={12} md={8}>
          <Stack spacing={3}>
            {/* Basic Information */}
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Basic Information
                </Typography>
                <Grid container spacing={3}>
                  <Grid item xs={12} sm={6}>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                      <BusinessIcon sx={{ mr: 2, color: 'primary.main' }} />
                      <Box>
                        <Typography variant="body2" color="text.secondary">
                          Organization
                        </Typography>
                        <Typography variant="body1">
                          {tender.organization || 'Not specified'}
                        </Typography>
                      </Box>
                    </Box>
                  </Grid>
                  
                  <Grid item xs={12} sm={6}>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                      <PublicIcon sx={{ mr: 2, color: 'primary.main' }} />
                      <Box>
                        <Typography variant="body2" color="text.secondary">
                          Country
                        </Typography>
                        <Typography variant="body1">
                          {tender.country || 'Not specified'}
                        </Typography>
                      </Box>
                    </Box>
                  </Grid>

                  <Grid item xs={12} sm={6}>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                      <CalendarIcon sx={{ mr: 2, color: 'primary.main' }} />
                      <Box>
                        <Typography variant="body2" color="text.secondary">
                          Deadline
                        </Typography>
                        <Typography variant="body1">
                          {formatDate(tender.deadline)}
                        </Typography>
                      </Box>
                    </Box>
                  </Grid>

                  <Grid item xs={12} sm={6}>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                      <CalendarIcon sx={{ mr: 2, color: 'secondary.main' }} />
                      <Box>
                        <Typography variant="body2" color="text.secondary">
                          Publication Date
                        </Typography>
                        <Typography variant="body1">
                          {formatDate(tender.publication_date)}
                        </Typography>
                      </Box>
                    </Box>
                  </Grid>

                  {tender.notice_type && (
                    <Grid item xs={12}>
                      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                        <DescriptionIcon sx={{ mr: 2, color: 'primary.main' }} />
                        <Box>
                          <Typography variant="body2" color="text.secondary">
                            Notice Type
                          </Typography>
                          <Typography variant="body1">
                            {tender.notice_type}
                          </Typography>
                        </Box>
                      </Box>
                    </Grid>
                  )}
                </Grid>
              </CardContent>
            </Card>

            {/* Description */}
            {tender.description && (
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Description
                  </Typography>
                  <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap' }}>
                    {tender.description}
                  </Typography>
                </CardContent>
              </Card>
            )}

            {/* Financial Information */}
            {(tender.estimated_budget || tender.currency) && (
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Financial Information
                  </Typography>
                  <Grid container spacing={3}>
                    {tender.estimated_budget && (
                      <Grid item xs={12} sm={6}>
                        <Typography variant="body2" color="text.secondary">
                          Estimated Budget
                        </Typography>
                        <Typography variant="h6">
                          {tender.estimated_budget}
                        </Typography>
                      </Grid>
                    )}
                    {tender.currency && (
                      <Grid item xs={12} sm={6}>
                        <Typography variant="body2" color="text.secondary">
                          Currency
                        </Typography>
                        <Typography variant="h6">
                          {tender.currency}
                        </Typography>
                      </Grid>
                    )}
                  </Grid>
                </CardContent>
              </Card>
            )}

            {/* Documents */}
            {tender.document_links && tender.document_links.length > 0 && (
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Documents
                  </Typography>
                  <List>
                    {tender.document_links.map((doc, index) => (
                      <ListItem key={index} divider>
                        <ListItemIcon>
                          <AttachFileIcon />
                        </ListItemIcon>
                        <ListItemText
                          primary={
                            <Link href={doc} target="_blank" rel="noopener">
                              Document {index + 1}
                            </Link>
                          }
                          secondary="Click to download"
                        />
                      </ListItem>
                    ))}
                  </List>
                </CardContent>
              </Card>
            )}
          </Stack>
        </Grid>

        {/* Sidebar */}
        <Grid item xs={12} md={4}>
          <Stack spacing={3}>
            {/* Contact Information */}
            {tender.contact_email && (
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Contact Information
                  </Typography>
                  <Box sx={{ display: 'flex', alignItems: 'center' }}>
                    <EmailIcon sx={{ mr: 2, color: 'primary.main' }} />
                    <Box>
                      <Typography variant="body2" color="text.secondary">
                        Email
                      </Typography>
                      <Link href={`mailto:${tender.contact_email}`}>
                        {tender.contact_email}
                      </Link>
                    </Box>
                  </Box>
                </CardContent>
              </Card>
            )}

            {/* Relevance Analysis */}
            {tender.relevance_score && (
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Relevance Analysis
                  </Typography>
                  <Box sx={{ textAlign: 'center', mb: 2 }}>
                    <Typography variant="h3" color={`${getRelevanceScoreColor(tender.relevance_score)}.main`}>
                      {tender.relevance_score.toFixed(0)}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Relevance Score
                    </Typography>
                  </Box>
                  <Typography variant="body2">
                    This score is calculated based on geographic relevance, keywords matching, 
                    deadline urgency, and organization importance.
                  </Typography>
                </CardContent>
              </Card>
            )}

            {/* Additional Information */}
            {tender.additional_data && (
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Additional Information
                  </Typography>
                  <Accordion>
                    <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                      <Typography>Technical Details</Typography>
                    </AccordionSummary>
                    <AccordionDetails>
                      <Typography variant="body2" color="text.secondary">
                        Source: {tender.source}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Extracted: {formatDate(tender.extracted_at)}
                      </Typography>
                      {tender.url && (
                        <Typography variant="body2" color="text.secondary">
                          <Link href={tender.url} target="_blank">
                            Original URL
                          </Link>
                        </Typography>
                      )}
                    </AccordionDetails>
                  </Accordion>
                </CardContent>
              </Card>
            )}
          </Stack>
        </Grid>
      </Grid>

      {/* Share Dialog */}
      <Dialog open={shareDialogOpen} onClose={() => setShareDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Share Tender</DialogTitle>
        <DialogContent>
          <Typography variant="body2" sx={{ mb: 2 }}>
            Copy the link below to share this tender:
          </Typography>
          <TextField
            fullWidth
            value={window.location.href}
            InputProps={{
              readOnly: true,
              endAdornment: (
                <Button
                  onClick={() => {
                    navigator.clipboard.writeText(window.location.href)
                    setShareDialogOpen(false)
                  }}
                >
                  Copy
                </Button>
              )
            }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShareDialogOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}

export default TenderDetails