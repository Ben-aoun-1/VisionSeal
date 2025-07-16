import React, { useState } from 'react'
import { useLocation } from 'react-router-dom'
import {
  Box,
  Drawer,
  AppBar,
  Toolbar,
  Typography,
  useTheme,
  useMediaQuery,
  Container,
} from '@mui/material'
import { styled } from '@mui/material/styles'

import Sidebar from './Sidebar'
import Header from './Header'
import { colors } from '@/theme/colors'

const drawerWidth = 280

const Main = styled('main', { shouldForwardProp: (prop) => prop !== 'open' })<{
  open?: boolean
}>(({ theme, open }) => ({
  flexGrow: 1,
  padding: theme.spacing(3),
  transition: theme.transitions.create('margin', {
    easing: theme.transitions.easing.sharp,
    duration: theme.transitions.duration.leavingScreen,
  }),
  marginLeft: `-${drawerWidth}px`,
  minHeight: '100vh',
  backgroundColor: colors.background.secondary,
  ...(open && {
    transition: theme.transitions.create('margin', {
      easing: theme.transitions.easing.easeOut,
      duration: theme.transitions.duration.enteringScreen,
    }),
    marginLeft: 0,
  }),
  [theme.breakpoints.up('lg')]: {
    marginLeft: 0,
  },
}))

const DrawerHeader = styled('div')(({ theme }) => ({
  display: 'flex',
  alignItems: 'center',
  padding: theme.spacing(0, 1),
  ...theme.mixins.toolbar,
  justifyContent: 'flex-end',
}))

interface LayoutProps {
  children: React.ReactNode
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const theme = useTheme()
  const location = useLocation()
  const isMobile = useMediaQuery(theme.breakpoints.down('lg'))
  const [mobileOpen, setMobileOpen] = useState(false)

  const handleDrawerToggle = () => {
    setMobileOpen(!mobileOpen)
  }

  const handleDrawerClose = () => {
    setMobileOpen(false)
  }

  // Get page title from location
  const getPageTitle = () => {
    switch (location.pathname) {
      case '/':
      case '/dashboard':
        return 'Dashboard'
      case '/tenders':
        return 'Tenders'
      case '/analytics':
        return 'Analytics'
      case '/settings':
        return 'Settings'
      default:
        if (location.pathname.startsWith('/tenders/')) {
          return 'Tender Details'
        }
        return 'VisionSeal'
    }
  }

  return (
    <Box sx={{ display: 'flex' }}>
      {/* Header */}
      <AppBar
        position="fixed"
        elevation={0}
        sx={{
          width: { lg: `calc(100% - ${drawerWidth}px)` },
          ml: { lg: `${drawerWidth}px` },
          backgroundColor: colors.background.paper,
          borderBottom: `1px solid ${colors.border.light}`,
        }}
      >
        <Header onMenuClick={handleDrawerToggle} pageTitle={getPageTitle()} />
      </AppBar>

      {/* Sidebar */}
      <Box
        component="nav"
        sx={{ width: { lg: drawerWidth }, flexShrink: { lg: 0 } }}
        aria-label="navigation"
      >
        {/* Mobile drawer */}
        <Drawer
          variant="temporary"
          open={mobileOpen}
          onClose={handleDrawerClose}
          ModalProps={{
            keepMounted: true, // Better open performance on mobile
          }}
          sx={{
            display: { xs: 'block', lg: 'none' },
            '& .MuiDrawer-paper': {
              boxSizing: 'border-box',
              width: drawerWidth,
              backgroundColor: colors.background.paper,
              borderRight: `1px solid ${colors.border.light}`,
            },
          }}
        >
          <Sidebar onItemClick={handleDrawerClose} />
        </Drawer>

        {/* Desktop drawer */}
        <Drawer
          variant="permanent"
          sx={{
            display: { xs: 'none', lg: 'block' },
            '& .MuiDrawer-paper': {
              boxSizing: 'border-box',
              width: drawerWidth,
              backgroundColor: colors.background.paper,
              borderRight: `1px solid ${colors.border.light}`,
            },
          }}
          open
        >
          <Sidebar />
        </Drawer>
      </Box>

      {/* Main content */}
      <Main open={!isMobile}>
        <DrawerHeader />
        <Container maxWidth="xl" sx={{ px: { xs: 2, sm: 3 } }}>
          {children}
        </Container>
      </Main>
    </Box>
  )
}

export default Layout