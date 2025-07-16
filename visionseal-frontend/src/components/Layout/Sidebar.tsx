import React from 'react'
import {
  Box,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Typography,
  Divider,
  Chip,
} from '@mui/material'
import {
  Dashboard as DashboardIcon,
  Description as TendersIcon,
  Analytics as AnalyticsIcon,
  AutoAwesome as AIIcon,
  Settings as SettingsIcon,
  TrendingUp as TrendingIcon,
  Business as BusinessIcon,
} from '@mui/icons-material'
import { useNavigate, useLocation } from 'react-router-dom'
import { styled } from '@mui/material/styles'
import { colors } from '@/theme/colors'

// Styled Components
const SidebarContainer = styled(Box)({
  width: '100%',
  height: '100vh',
  backgroundColor: colors.background.paper,
  display: 'flex',
  flexDirection: 'column',
})

const LogoSection = styled(Box)(({ theme }) => ({
  padding: theme.spacing(3),
  borderBottom: `1px solid ${colors.border.light}`,
  display: 'flex',
  alignItems: 'center',
  gap: theme.spacing(2),
}))

const Logo = styled(Box)({
  width: 40,
  height: 40,
  borderRadius: 8,
  background: colors.gradients.primary,
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  color: colors.text.inverse,
  fontWeight: 700,
  fontSize: '1.125rem',
})

const NavSection = styled(Box)(({ theme }) => ({
  flex: 1,
  padding: theme.spacing(2, 0),
  overflowY: 'auto',
}))

const NavItem = styled(ListItemButton)<{ active?: boolean }>(({ theme, active }) => ({
  margin: theme.spacing(0, 2),
  borderRadius: theme.shape.borderRadius,
  marginBottom: theme.spacing(0.5),
  '&:hover': {
    backgroundColor: colors.primary[50],
  },
  ...(active && {
    backgroundColor: colors.primary[100],
    '& .MuiListItemIcon-root': {
      color: colors.primary[600],
    },
    '& .MuiListItemText-primary': {
      color: colors.primary[700],
      fontWeight: 600,
    },
  }),
}))

const StatsSection = styled(Box)(({ theme }) => ({
  padding: theme.spacing(2),
  borderTop: `1px solid ${colors.border.light}`,
}))

const StatCard = styled(Box)(({ theme }) => ({
  backgroundColor: colors.background.tertiary,
  borderRadius: theme.shape.borderRadius,
  padding: theme.spacing(2),
  marginBottom: theme.spacing(2),
}))

interface SidebarProps {
  onItemClick?: () => void
}

const navigationItems = [
  {
    text: 'Dashboard',
    icon: <DashboardIcon />,
    path: '/dashboard',
  },
  {
    text: 'Tenders',
    icon: <TendersIcon />,
    path: '/tenders',
    badge: '1.2k',
  },
  {
    text: 'Analytics',
    icon: <AnalyticsIcon />,
    path: '/analytics',
  },
  {
    text: 'AI Reports',
    icon: <AIIcon />,
    path: '/ai-reports',
    badge: 'NEW',
  },
  {
    text: 'Settings',
    icon: <SettingsIcon />,
    path: '/settings',
  },
]

const Sidebar: React.FC<SidebarProps> = ({ onItemClick }) => {
  const navigate = useNavigate()
  const location = useLocation()

  const handleNavigation = (path: string) => {
    navigate(path)
    onItemClick?.()
  }

  const isActive = (path: string) => {
    if (path === '/dashboard') {
      return location.pathname === '/' || location.pathname === '/dashboard'
    }
    return location.pathname.startsWith(path)
  }

  return (
    <SidebarContainer>
      {/* Logo Section */}
      <LogoSection>
        <Logo>VS</Logo>
        <Box>
          <Typography
            variant="h6"
            sx={{
              color: colors.text.primary,
              fontWeight: 700,
              fontSize: '1.125rem',
              lineHeight: 1.2,
            }}
          >
            VisionSeal
          </Typography>
          <Typography
            variant="caption"
            sx={{
              color: colors.text.tertiary,
              fontSize: '0.75rem',
              textTransform: 'uppercase',
              letterSpacing: '0.5px',
            }}
          >
            Tender Platform
          </Typography>
        </Box>
      </LogoSection>

      {/* Navigation Section */}
      <NavSection>
        <List sx={{ px: 0 }}>
          {navigationItems.map((item) => (
            <ListItem key={item.text} disablePadding>
              <NavItem
                active={isActive(item.path)}
                onClick={() => handleNavigation(item.path)}
              >
                <ListItemIcon
                  sx={{
                    minWidth: 40,
                    color: colors.text.secondary,
                  }}
                >
                  {item.icon}
                </ListItemIcon>
                <ListItemText
                  primary={item.text}
                  primaryTypographyProps={{
                    fontSize: '0.875rem',
                    fontWeight: 500,
                  }}
                />
                {item.badge && (
                  <Chip
                    label={item.badge}
                    size="small"
                    sx={{
                      height: 20,
                      fontSize: '0.75rem',
                      backgroundColor: colors.primary[100],
                      color: colors.primary[700],
                    }}
                  />
                )}
              </NavItem>
            </ListItem>
          ))}
        </List>
      </NavSection>

      {/* Stats Section */}
      <StatsSection>
        <StatCard>
          <Box display="flex" alignItems="center" gap={1} mb={1}>
            <TrendingIcon
              sx={{
                fontSize: 16,
                color: colors.success[600],
              }}
            />
            <Typography
              variant="caption"
              sx={{
                color: colors.text.secondary,
                fontSize: '0.75rem',
                fontWeight: 500,
                textTransform: 'uppercase',
              }}
            >
              Active Tenders
            </Typography>
          </Box>
          <Typography
            variant="h6"
            sx={{
              color: colors.text.primary,
              fontWeight: 700,
              fontSize: '1.25rem',
            }}
          >
            847
          </Typography>
        </StatCard>

        <StatCard>
          <Box display="flex" alignItems="center" gap={1} mb={1}>
            <BusinessIcon
              sx={{
                fontSize: 16,
                color: colors.secondary[600],
              }}
            />
            <Typography
              variant="caption"
              sx={{
                color: colors.text.secondary,
                fontSize: '0.75rem',
                fontWeight: 500,
                textTransform: 'uppercase',
              }}
            >
              Organizations
            </Typography>
          </Box>
          <Typography
            variant="h6"
            sx={{
              color: colors.text.primary,
              fontWeight: 700,
              fontSize: '1.25rem',
            }}
          >
            156
          </Typography>
        </StatCard>
      </StatsSection>
    </SidebarContainer>
  )
}

export default Sidebar