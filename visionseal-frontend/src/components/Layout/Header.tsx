import React, { useState } from 'react'
import {
  Toolbar,
  Typography,
  IconButton,
  Box,
  Avatar,
  Menu,
  MenuItem,
  Badge,
  InputBase,
} from '@mui/material'
import {
  Menu as MenuIcon,
  Search as SearchIcon,
  Notifications as NotificationsIcon,
  Settings as SettingsIcon,
  Person as PersonIcon,
  Logout as LogoutIcon,
} from '@mui/icons-material'
import { styled, alpha } from '@mui/material/styles'
import { useNavigate } from 'react-router-dom'
import { colors } from '@/theme/colors'

// Styled Components
const StyledToolbar = styled(Toolbar)(({ theme }) => ({
  display: 'flex',
  justifyContent: 'space-between',
  alignItems: 'center',
  padding: theme.spacing(0, 3),
  minHeight: 64,
}))

const SearchBox = styled(Box)(({ theme }) => ({
  position: 'relative',
  borderRadius: theme.shape.borderRadius,
  backgroundColor: alpha(colors.neutral[100], 0.8),
  '&:hover': {
    backgroundColor: alpha(colors.neutral[100], 1),
  },
  marginLeft: theme.spacing(3),
  width: 300,
  [theme.breakpoints.down('md')]: {
    display: 'none',
  },
}))

const SearchIconWrapper = styled('div')(({ theme }) => ({
  padding: theme.spacing(0, 2),
  height: '100%',
  position: 'absolute',
  pointerEvents: 'none',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  color: colors.text.tertiary,
}))

const StyledInputBase = styled(InputBase)(({ theme }) => ({
  color: colors.text.primary,
  '& .MuiInputBase-input': {
    padding: theme.spacing(1, 1, 1, 0),
    paddingLeft: `calc(1em + ${theme.spacing(4)})`,
    width: '100%',
  },
}))

const ActionButton = styled(IconButton)({
  color: colors.text.secondary,
  '&:hover': {
    backgroundColor: alpha(colors.primary[500], 0.08),
    color: colors.primary[600],
  },
})

const UserAvatar = styled(Avatar)({
  width: 36,
  height: 36,
  backgroundColor: colors.primary[500],
  cursor: 'pointer',
  fontSize: '0.875rem',
  fontWeight: 600,
})

interface HeaderProps {
  onMenuClick: () => void
  pageTitle: string
}

const Header: React.FC<HeaderProps> = ({ onMenuClick, pageTitle }) => {
  const navigate = useNavigate()
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null)
  const [searchQuery, setSearchQuery] = useState('')

  const handleProfileMenu = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget)
  }

  const handleMenuClose = () => {
    setAnchorEl(null)
  }

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    if (searchQuery.trim()) {
      navigate(`/tenders?search=${encodeURIComponent(searchQuery.trim())}`)
    }
  }

  const handleLogout = () => {
    localStorage.removeItem('auth_token')
    navigate('/login')
    handleMenuClose()
  }

  return (
    <StyledToolbar>
      {/* Left Section */}
      <Box display="flex" alignItems="center">
        <IconButton
          edge="start"
          color="inherit"
          onClick={onMenuClick}
          sx={{ mr: 2, display: { lg: 'none' }, color: colors.text.secondary }}
        >
          <MenuIcon />
        </IconButton>
        
        <Typography
          variant="h6"
          component="h1"
          sx={{
            color: colors.text.primary,
            fontWeight: 600,
            fontSize: '1.125rem',
          }}
        >
          {pageTitle}
        </Typography>
      </Box>

      {/* Center - Search */}
      <SearchBox>
        <SearchIconWrapper>
          <SearchIcon />
        </SearchIconWrapper>
        <form onSubmit={handleSearch}>
          <StyledInputBase
            placeholder="Search tenders, organizations..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            inputProps={{ 'aria-label': 'search' }}
          />
        </form>
      </SearchBox>

      {/* Right Section */}
      <Box display="flex" alignItems="center" gap={1}>
        {/* Mobile Search */}
        <ActionButton
          sx={{ display: { md: 'none' } }}
          onClick={() => navigate('/tenders')}
        >
          <SearchIcon />
        </ActionButton>

        {/* Notifications */}
        <ActionButton>
          <Badge badgeContent={3} color="error">
            <NotificationsIcon />
          </Badge>
        </ActionButton>

        {/* Settings */}
        <ActionButton onClick={() => navigate('/settings')}>
          <SettingsIcon />
        </ActionButton>

        {/* User Menu */}
        <UserAvatar onClick={handleProfileMenu}>
          VS
        </UserAvatar>
      </Box>

      {/* Profile Menu */}
      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleMenuClose}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
        transformOrigin={{ vertical: 'top', horizontal: 'right' }}
        PaperProps={{
          elevation: 3,
          sx: {
            mt: 1.5,
            minWidth: 180,
            '& .MuiMenuItem-root': {
              fontSize: '0.875rem',
              py: 1.5,
            },
          },
        }}
      >
        <MenuItem onClick={handleMenuClose}>
          <PersonIcon sx={{ mr: 2, fontSize: 20 }} />
          Profile
        </MenuItem>
        <MenuItem onClick={() => navigate('/settings')}>
          <SettingsIcon sx={{ mr: 2, fontSize: 20 }} />
          Settings
        </MenuItem>
        <MenuItem onClick={handleLogout}>
          <LogoutIcon sx={{ mr: 2, fontSize: 20 }} />
          Logout
        </MenuItem>
      </Menu>
    </StyledToolbar>
  )
}

export default Header