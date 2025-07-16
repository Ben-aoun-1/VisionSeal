import React, { useState } from 'react'
import {
  Card,
  CardContent,
  Typography,
  Box,
  Button,
  Grid,
  CircularProgress,
} from '@mui/material'
import {
  Add as AddIcon,
  Download as DownloadIcon,
  Analytics as AnalyticsIcon,
  Refresh as RefreshIcon,
  Search as SearchIcon,
  Settings as SettingsIcon,
  PlayArrow as PlayIcon,
  Stop as StopIcon,
} from '@mui/icons-material'
import { styled } from '@mui/material/styles'
import { useNavigate } from 'react-router-dom'
import { useMutation, useQuery } from 'react-query'
import { scraperApi } from '@/utils/api'
import { colors } from '@/theme/colors'

// Styled Components
const QuickActionsCard = styled(Card)(({ theme }) => ({
  height: '100%',
  borderRadius: 12,
  border: `1px solid ${colors.border.light}`,
  boxShadow: '0px 2px 8px rgba(0, 0, 0, 0.04)',
}))

const ActionButton = styled(Button)(({ theme }) => ({
  width: '100%',
  padding: theme.spacing(1.5),
  borderRadius: 8,
  textTransform: 'none',
  fontSize: '0.875rem',
  fontWeight: 500,
  justifyContent: 'flex-start',
  gap: 12,
  border: `1px solid ${colors.border.light}`,
  backgroundColor: colors.background.paper,
  color: colors.text.primary,
  '&:hover': {
    backgroundColor: colors.background.tertiary,
    borderColor: colors.primary[300],
  },
}))

const QuickActions: React.FC = () => {
  const navigate = useNavigate()
  const [ungmRunning, setUngmRunning] = useState(false)
  const [tunipagesRunning, setTunipagesRunning] = useState(false)

  // Get scraper status
  const { data: scraperStatuses } = useQuery(
    'scraper-statuses',
    scraperApi.getAllStatuses,
    {
      refetchInterval: 10000, // Refresh every 10 seconds (reduced from 5s)
      onSuccess: (data) => {
        const runningScrapers = data?.running_scrapers || {}
        const hasUngmRunning = Object.values(runningScrapers).some((session: any) => 
          session.source === 'ungm' && session.status === 'running'
        )
        const hasTunipagesRunning = Object.values(runningScrapers).some((session: any) => 
          session.source === 'tunipages' && session.status === 'running'
        )
        setUngmRunning(hasUngmRunning)
        setTunipagesRunning(hasTunipagesRunning)
      }
    }
  )

  // Start UNGM scraper mutation
  const startUngmMutation = useMutation(
    (config: any) => scraperApi.startUNGM(config),
    {
      onSuccess: () => {
        setUngmRunning(true)
      },
      onError: (error) => {
        console.error('Failed to start UNGM scraper:', error)
      }
    }
  )

  // Start TuniPages scraper mutation
  const startTunipagesMutation = useMutation(
    (config: any) => scraperApi.startTuniPages(config),
    {
      onSuccess: () => {
        setTunipagesRunning(true)
      },
      onError: (error) => {
        console.error('Failed to start TuniPages scraper:', error)
      }
    }
  )

  const handleStartUngm = () => {
    startUngmMutation.mutate({ max_pages: 10, headless: true, save_to_supabase: true })
  }

  const handleStartTunipages = () => {
    startTunipagesMutation.mutate({ max_pages: 10, headless: true, save_to_supabase: true })
  }

  const actions = [
    {
      label: 'Search Tenders',
      icon: <SearchIcon />,
      onClick: () => navigate('/tenders'),
      color: colors.primary[500],
    },
    {
      label: ungmRunning ? 'UNGM Scraping Active' : 'Start UNGM Scraper',
      icon: ungmRunning ? (
        startUngmMutation.isLoading ? <CircularProgress size={20} /> : <StopIcon />
      ) : (
        <PlayIcon />
      ),
      onClick: ungmRunning ? () => {} : handleStartUngm,
      color: ungmRunning ? colors.warning[500] : colors.success[500],
      disabled: startUngmMutation.isLoading,
    },
    {
      label: tunipagesRunning ? 'TuniPages Scraping Active' : 'Start TuniPages Scraper',
      icon: tunipagesRunning ? (
        startTunipagesMutation.isLoading ? <CircularProgress size={20} /> : <StopIcon />
      ) : (
        <PlayIcon />
      ),
      onClick: tunipagesRunning ? () => {} : handleStartTunipages,
      color: tunipagesRunning ? colors.warning[500] : colors.success[500],
      disabled: startTunipagesMutation.isLoading,
    },
    {
      label: 'View Analytics',
      icon: <AnalyticsIcon />,
      onClick: () => navigate('/analytics'),
      color: colors.info[500],
    },
    {
      label: 'Export Data',
      icon: <DownloadIcon />,
      onClick: () => navigate('/tenders?export=true'),
      color: colors.secondary[500],
    },
  ]

  const handleRefreshData = () => {
    window.location.reload()
  }

  return (
    <QuickActionsCard>
      <CardContent sx={{ p: 3 }}>
        <Box
          sx={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            mb: 3,
          }}
        >
          <Typography
            variant="h6"
            sx={{
              fontSize: '1.125rem',
              fontWeight: 600,
              color: colors.text.primary,
            }}
          >
            Quick Actions
          </Typography>
          <Button
            size="small"
            onClick={handleRefreshData}
            sx={{
              minWidth: 'auto',
              p: 1,
              color: colors.text.secondary,
              '&:hover': {
                backgroundColor: colors.background.tertiary,
                color: colors.primary[600],
              },
            }}
          >
            <RefreshIcon sx={{ fontSize: 18 }} />
          </Button>
        </Box>

        <Grid container spacing={2}>
          {actions.map((action, index) => (
            <Grid item xs={12} key={index}>
              <ActionButton
                onClick={action.onClick}
                disabled={action.disabled || false}
                startIcon={
                  <Box
                    sx={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      color: action.color,
                    }}
                  >
                    {action.icon}
                  </Box>
                }
              >
                {action.label}
              </ActionButton>
            </Grid>
          ))}
        </Grid>
      </CardContent>
    </QuickActionsCard>
  )
}

export default QuickActions