import React from 'react'
import {
  Card,
  CardContent,
  Typography,
  Box,
  Skeleton,
  useTheme,
} from '@mui/material'
import { styled } from '@mui/material/styles'
import { colors } from '@/theme/colors'

// Styled Components
const StatsCardContainer = styled(Card)(({ theme }) => ({
  height: '100%',
  borderRadius: 12,
  border: `1px solid ${colors.border.light}`,
  boxShadow: '0px 2px 8px rgba(0, 0, 0, 0.04)',
  transition: 'all 0.2s ease-in-out',
  '&:hover': {
    boxShadow: '0px 4px 16px rgba(0, 0, 0, 0.08)',
    transform: 'translateY(-2px)',
  },
}))

const IconContainer = styled(Box)<{ iconColor: string }>(({ iconColor }) => ({
  width: 48,
  height: 48,
  borderRadius: 12,
  backgroundColor: `${iconColor}15`,
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  color: iconColor,
  '& svg': {
    fontSize: 24,
  },
}))

const ValueText = styled(Typography)({
  fontSize: '2rem',
  fontWeight: 700,
  lineHeight: 1.2,
  color: colors.text.primary,
})

const TitleText = styled(Typography)({
  fontSize: '0.875rem',
  fontWeight: 500,
  color: colors.text.secondary,
  marginBottom: 8,
})

const ChangeIndicator = styled(Box)<{ positive: boolean }>(({ positive }) => ({
  display: 'flex',
  alignItems: 'center',
  gap: 4,
  fontSize: '0.75rem',
  fontWeight: 500,
  color: positive ? colors.success[600] : colors.error[600],
}))

interface StatsCardProps {
  title: string
  value: string | number
  icon: React.ReactNode
  color: string
  change?: number
  loading?: boolean
  onClick?: () => void
}

const StatsCard: React.FC<StatsCardProps> = ({
  title,
  value,
  icon,
  color,
  change,
  loading = false,
  onClick,
}) => {
  const theme = useTheme()

  const formatValue = (val: string | number): string => {
    if (typeof val === 'number') {
      if (val >= 1000000) {
        return `${(val / 1000000).toFixed(1)}M`
      }
      if (val >= 1000) {
        return `${(val / 1000).toFixed(1)}K`
      }
      return val.toString()
    }
    return val
  }

  if (loading) {
    return (
      <StatsCardContainer>
        <CardContent sx={{ p: 3 }}>
          <Box display="flex" alignItems="flex-start" justifyContent="space-between" mb={2}>
            <Box flex={1}>
              <Skeleton variant="text" width="60%" height={20} />
              <Skeleton variant="text" width="40%" height={40} sx={{ mt: 1 }} />
            </Box>
            <Skeleton variant="rectangular" width={48} height={48} sx={{ borderRadius: 1.5 }} />
          </Box>
          {change !== undefined && (
            <Skeleton variant="text" width="30%" height={16} />
          )}
        </CardContent>
      </StatsCardContainer>
    )
  }

  return (
    <StatsCardContainer
      onClick={onClick}
      sx={{
        cursor: onClick ? 'pointer' : 'default',
      }}
    >
      <CardContent sx={{ p: 3 }}>
        <Box display="flex" alignItems="flex-start" justifyContent="space-between" mb={2}>
          <Box flex={1}>
            <TitleText>{title}</TitleText>
            <ValueText>{formatValue(value)}</ValueText>
          </Box>
          <IconContainer iconColor={color}>
            {icon}
          </IconContainer>
        </Box>
        
        {change !== undefined && (
          <ChangeIndicator positive={change >= 0}>
            {change >= 0 ? '+' : ''}{change}%
            <Typography variant="caption" sx={{ color: colors.text.tertiary, ml: 1 }}>
              vs last month
            </Typography>
          </ChangeIndicator>
        )}
      </CardContent>
    </StatsCardContainer>
  )
}

export default StatsCard