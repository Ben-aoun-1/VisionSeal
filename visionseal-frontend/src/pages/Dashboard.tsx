import React from 'react'
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Button,
  useTheme,
} from '@mui/material'
import {
  TrendingUp as TrendingUpIcon,
  Business as BusinessIcon,
  Public as PublicIcon,
  Assignment as AssignmentIcon,
  ArrowForward as ArrowForwardIcon,
} from '@mui/icons-material'
import { styled } from '@mui/material/styles'
import { useNavigate } from 'react-router-dom'
import { useQuery } from 'react-query'
import { Helmet } from 'react-helmet-async'

import { tenderApi } from '@/utils/api'
import { colors } from '@/theme/colors'
import StatsCard from '@/components/Dashboard/StatsCard'
import RecentTenders from '@/components/Dashboard/RecentTenders'
import TenderChart from '@/components/Dashboard/TenderChart'
import QuickActions from '@/components/Dashboard/QuickActions'

// Styled Components
const DashboardContainer = styled(Box)({
  minHeight: '100vh',
  backgroundColor: colors.background.secondary,
})

const WelcomeSection = styled(Card)(({ theme }) => ({
  background: colors.gradients.hero,
  color: colors.text.inverse,
  marginBottom: theme.spacing(4),
  overflow: 'hidden',
  position: 'relative',
  '&::before': {
    content: '""',
    position: 'absolute',
    top: 0,
    right: 0,
    width: '50%',
    height: '100%',
    background: 'rgba(255, 255, 255, 0.1)',
    transform: 'skewX(-15deg)',
    transformOrigin: 'top right',
  },
}))

const Dashboard: React.FC = () => {
  const theme = useTheme()
  const navigate = useNavigate()

  // Fetch dashboard data
  const { data: stats, isLoading: statsLoading } = useQuery(
    'tender-stats',
    tenderApi.getStats,
    {
      refetchInterval: 5 * 60 * 1000, // Refresh every 5 minutes
    }
  )

  const { data: recentTenders, isLoading: tendersLoading } = useQuery(
    'recent-tenders',
    () => tenderApi.getTenders({ page: 1, per_page: 5, sort_by: 'created_at', sort_order: 'desc' }),
    {
      refetchInterval: 2 * 60 * 1000, // Refresh every 2 minutes
    }
  )

  const handleViewAllTenders = () => {
    navigate('/tenders')
  }

  const handleViewAnalytics = () => {
    navigate('/analytics')
  }

  return (
    <DashboardContainer>
      <Helmet>
        <title>Dashboard - VisionSeal</title>
        <meta name="description" content="VisionSeal tender management dashboard with real-time statistics and insights" />
      </Helmet>

      {/* Welcome Section */}
      <WelcomeSection>
        <CardContent sx={{ py: 4, px: 4, position: 'relative', zIndex: 1 }}>
          <Grid container spacing={4} alignItems="center">
            <Grid item xs={12} md={8}>
              <Typography
                variant="h3"
                sx={{
                  fontWeight: 700,
                  fontSize: { xs: '1.875rem', md: '2.25rem' },
                  mb: 2,
                  lineHeight: 1.2,
                }}
              >
                Welcome to VisionSeal
              </Typography>
              <Typography
                variant="subtitle1"
                sx={{
                  fontSize: '1.125rem',
                  opacity: 0.9,
                  mb: 3,
                  maxWidth: '600px',
                }}
              >
                Your comprehensive platform for African tender opportunities. 
                Track, analyze, and manage procurement opportunities across multiple sources.
              </Typography>
              <Box display="flex" gap={2} flexWrap="wrap">
                <Button
                  variant="contained"
                  size="large"
                  onClick={handleViewAllTenders}
                  sx={{
                    backgroundColor: 'rgba(255, 255, 255, 0.2)',
                    color: 'white',
                    '&:hover': {
                      backgroundColor: 'rgba(255, 255, 255, 0.3)',
                    },
                  }}
                  endIcon={<ArrowForwardIcon />}
                >
                  Browse Tenders
                </Button>
                <Button
                  variant="outlined"
                  size="large"
                  onClick={handleViewAnalytics}
                  sx={{
                    borderColor: 'rgba(255, 255, 255, 0.3)',
                    color: 'white',
                    '&:hover': {
                      borderColor: 'rgba(255, 255, 255, 0.5)',
                      backgroundColor: 'rgba(255, 255, 255, 0.1)',
                    },
                  }}
                >
                  View Analytics
                </Button>
              </Box>
            </Grid>
            <Grid item xs={12} md={4}>
              <Box
                sx={{
                  textAlign: 'center',
                  display: { xs: 'none', md: 'block' },
                }}
              >
                <Typography
                  variant="h2"
                  sx={{
                    fontWeight: 700,
                    fontSize: '3rem',
                    opacity: 0.8,
                  }}
                >
                  {stats?.total_tenders || '---'}
                </Typography>
                <Typography
                  variant="subtitle2"
                  sx={{
                    fontSize: '0.875rem',
                    opacity: 0.8,
                    textTransform: 'uppercase',
                    letterSpacing: '0.5px',
                  }}
                >
                  Total Tenders
                </Typography>
              </Box>
            </Grid>
          </Grid>
        </CardContent>
      </WelcomeSection>

      {/* Stats Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <StatsCard
            title="Active Tenders"
            value={stats?.active_tenders || 0}
            icon={<AssignmentIcon />}
            color={colors.success[500]}
            loading={statsLoading}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatsCard
            title="Organizations"
            value={Object.keys(stats?.organizations_breakdown || {}).length}
            icon={<BusinessIcon />}
            color={colors.primary[500]}
            loading={statsLoading}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatsCard
            title="Countries"
            value={Object.keys(stats?.countries_breakdown || {}).length}
            icon={<PublicIcon />}
            color={colors.secondary[500]}
            loading={statsLoading}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatsCard
            title="Avg. Relevance"
            value={`${Math.round(stats?.avg_relevance_score || 0)}%`}
            icon={<TrendingUpIcon />}
            color={colors.warning[500]}
            loading={statsLoading}
          />
        </Grid>
      </Grid>

      {/* Main Content */}
      <Grid container spacing={3}>
        {/* Charts Section */}
        <Grid item xs={12} lg={8}>
          <TenderChart data={stats} loading={statsLoading} />
        </Grid>

        {/* Side Panel */}
        <Grid item xs={12} lg={4}>
          <Box display="flex" flexDirection="column" gap={3}>
            <QuickActions />
            <RecentTenders 
              tenders={recentTenders?.tenders || []} 
              loading={tendersLoading}
            />
          </Box>
        </Grid>
      </Grid>
    </DashboardContainer>
  )
}

export default Dashboard