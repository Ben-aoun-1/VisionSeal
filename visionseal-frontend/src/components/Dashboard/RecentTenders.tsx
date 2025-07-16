import React from 'react'
import {
  Card,
  CardContent,
  Typography,
  Box,
  List,
  ListItem,
  ListItemText,
  ListItemAvatar,
  Avatar,
  Chip,
  Button,
  Skeleton,
  Divider,
} from '@mui/material'
import {
  Business as BusinessIcon,
  Schedule as ScheduleIcon,
  ArrowForward as ArrowForwardIcon,
} from '@mui/icons-material'
import { styled } from '@mui/material/styles'
import { useNavigate } from 'react-router-dom'
import { format, parseISO } from 'date-fns'
import { colors } from '@/theme/colors'
import { Tender, TenderStatus } from '@/types/tender'

// Styled Components
const RecentTendersCard = styled(Card)(({ theme }) => ({
  height: '100%',
  borderRadius: 12,
  border: `1px solid ${colors.border.light}`,
  boxShadow: '0px 2px 8px rgba(0, 0, 0, 0.04)',
}))

const CardHeader = styled(Box)({
  display: 'flex',
  justifyContent: 'space-between',
  alignItems: 'center',
  marginBottom: 16,
})

const TenderItem = styled(ListItem)(({ theme }) => ({
  padding: theme.spacing(2, 0),
  borderRadius: 8,
  '&:hover': {
    backgroundColor: colors.background.tertiary,
    cursor: 'pointer',
  },
}))

const TenderAvatar = styled(Avatar)({
  width: 40,
  height: 40,
  backgroundColor: colors.primary[100],
  color: colors.primary[600],
  '& svg': {
    fontSize: 20,
  },
})

const TenderTitle = styled(Typography)({
  fontSize: '0.875rem',
  fontWeight: 600,
  color: colors.text.primary,
  lineHeight: 1.4,
  display: '-webkit-box',
  WebkitLineClamp: 2,
  WebkitBoxOrient: 'vertical',
  overflow: 'hidden',
})

const TenderMeta = styled(Box)({
  display: 'flex',
  alignItems: 'center',
  gap: 8,
  marginTop: 4,
})

const MetaItem = styled(Box)({
  display: 'flex',
  alignItems: 'center',
  gap: 4,
  fontSize: '0.75rem',
  color: colors.text.tertiary,
})

const getStatusColor = (status: TenderStatus): string => {
  switch (status) {
    case TenderStatus.ACTIVE:
      return colors.success[500]
    case TenderStatus.EXPIRED:
      return colors.error[500]
    case TenderStatus.CANCELLED:
      return colors.neutral[500]
    case TenderStatus.AWARDED:
      return colors.secondary[500]
    default:
      return colors.neutral[500]
  }
}

interface RecentTendersProps {
  tenders: Tender[]
  loading?: boolean
}

const RecentTenders: React.FC<RecentTendersProps> = ({ tenders, loading = false }) => {
  const navigate = useNavigate()

  const handleTenderClick = (tender: Tender) => {
    navigate(`/tenders/${tender.id}`)
  }

  const handleViewAll = () => {
    navigate('/tenders')
  }

  const formatDate = (dateString: string) => {
    try {
      return format(parseISO(dateString), 'MMM d')
    } catch {
      return 'N/A'
    }
  }

  const renderSkeleton = () => (
    <List sx={{ py: 0 }}>
      {[...Array(5)].map((_, index) => (
        <ListItem key={index} sx={{ py: 2 }}>
          <ListItemAvatar>
            <Skeleton variant="circular" width={40} height={40} />
          </ListItemAvatar>
          <ListItemText
            primary={<Skeleton variant="text" width="80%" height={20} />}
            secondary={
              <Box sx={{ mt: 1 }}>
                <Skeleton variant="text" width="60%" height={16} />
                <Skeleton variant="text" width="40%" height={16} sx={{ mt: 0.5 }} />
              </Box>
            }
          />
        </ListItem>
      ))}
    </List>
  )

  const renderEmptyState = () => (
    <Box
      sx={{
        textAlign: 'center',
        py: 4,
        color: colors.text.tertiary,
      }}
    >
      <BusinessIcon sx={{ fontSize: 48, mb: 2, opacity: 0.5 }} />
      <Typography variant="body2">
        No recent tenders found
      </Typography>
    </Box>
  )

  return (
    <RecentTendersCard>
      <CardContent sx={{ p: 3 }}>
        <CardHeader>
          <Typography
            variant="h6"
            sx={{
              fontSize: '1.125rem',
              fontWeight: 600,
              color: colors.text.primary,
            }}
          >
            Recent Tenders
          </Typography>
          <Button
            size="small"
            onClick={handleViewAll}
            sx={{
              fontSize: '0.75rem',
              textTransform: 'none',
              color: colors.primary[600],
            }}
            endIcon={<ArrowForwardIcon sx={{ fontSize: 16 }} />}
          >
            View All
          </Button>
        </CardHeader>

        {loading ? (
          renderSkeleton()
        ) : tenders.length === 0 ? (
          renderEmptyState()
        ) : (
          <List sx={{ py: 0 }}>
            {tenders.map((tender, index) => (
              <React.Fragment key={tender.id}>
                <TenderItem onClick={() => handleTenderClick(tender)}>
                  <ListItemAvatar>
                    <TenderAvatar>
                      <BusinessIcon />
                    </TenderAvatar>
                  </ListItemAvatar>
                  <ListItemText
                    primary={<TenderTitle>{tender.title}</TenderTitle>}
                    secondary={
                      <Box sx={{ mt: 1 }}>
                        <TenderMeta>
                          <MetaItem>
                            <BusinessIcon sx={{ fontSize: 12 }} />
                            {tender.organization}
                          </MetaItem>
                          <MetaItem>
                            <ScheduleIcon sx={{ fontSize: 12 }} />
                            {tender.deadline ? formatDate(tender.deadline) : 'No deadline'}
                          </MetaItem>
                        </TenderMeta>
                        <Box sx={{ mt: 1, display: 'flex', gap: 1 }}>
                          <Chip
                            label={tender.status}
                            size="small"
                            sx={{
                              fontSize: '0.625rem',
                              height: 20,
                              backgroundColor: `${getStatusColor(tender.status)}15`,
                              color: getStatusColor(tender.status),
                            }}
                          />
                          <Chip
                            label={tender.source}
                            size="small"
                            sx={{
                              fontSize: '0.625rem',
                              height: 20,
                              backgroundColor: colors.neutral[100],
                              color: colors.neutral[700],
                            }}
                          />
                        </Box>
                      </Box>
                    }
                  />
                </TenderItem>
                {index < tenders.length - 1 && <Divider sx={{ mx: 0 }} />}
              </React.Fragment>
            ))}
          </List>
        )}
      </CardContent>
    </RecentTendersCard>
  )
}

export default RecentTenders