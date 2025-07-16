import React, { useState, useEffect } from 'react'
import {
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  CircularProgress,
  Alert,
  Chip,
  useTheme
} from '@mui/material'
import {
  TrendingUp,
  Assessment,
  Language,
  Business,
  Schedule,
  CheckCircle
} from '@mui/icons-material'
import { Helmet } from 'react-helmet-async'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line,
  ResponsiveContainer,
  AreaChart,
  Area
} from 'recharts'
import { tenderApi } from '../utils/api'
import { TenderStats } from '../types/tender'
import AnalyticsFilters from '../components/Analytics/AnalyticsFilters'

// Chart color palette
const COLORS = {
  primary: '#1976d2',
  secondary: '#dc004e',
  success: '#2e7d32',
  warning: '#ed6c02',
  info: '#0288d1',
  gradient: ['#1976d2', '#42a5f5', '#64b5f6', '#90caf9', '#bbdefb']
}

interface MetricCardProps {
  title: string
  value: string | number
  icon: React.ReactNode
  trend?: number
  color: string
}

const MetricCard: React.FC<MetricCardProps> = ({ title, value, icon, trend, color }) => {
  const theme = useTheme()
  
  return (
    <Card elevation={2} sx={{ height: '100%' }}>
      <CardContent>
        <Box display="flex" alignItems="center" justifyContent="space-between">
          <Box>
            <Typography variant="h4" component="div" color={color} fontWeight="bold">
              {value}
            </Typography>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              {title}
            </Typography>
            {trend !== undefined && (
              <Chip
                size="small"
                label={`${trend > 0 ? '+' : ''}${trend}%`}
                color={trend > 0 ? 'success' : trend < 0 ? 'error' : 'default'}
                sx={{ mt: 1 }}
              />
            )}
          </Box>
          <Box
            sx={{
              p: 1.5,
              borderRadius: 2,
              backgroundColor: `${color}15`,
              color: color
            }}
          >
            {icon}
          </Box>
        </Box>
      </CardContent>
    </Card>
  )
}

const Analytics: React.FC = () => {
  const theme = useTheme()
  const [stats, setStats] = useState<TenderStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [timeRange, setTimeRange] = useState('30')

  useEffect(() => {
    fetchAnalytics()
  }, [timeRange])

  const fetchAnalytics = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await tenderApi.getStats()
      setStats(data)
    } catch (err: any) {
      console.error('Failed to fetch analytics:', err)
      setError('Failed to load analytics data. Please try again later.')
    } finally {
      setLoading(false)
    }
  }

  // Transform data for charts
  const getSourceData = () => {
    if (!stats?.sources_breakdown) return []
    return Object.entries(stats.sources_breakdown).map(([name, value]) => ({
      name,
      value,
      color: COLORS.gradient[Object.keys(stats.sources_breakdown).indexOf(name) % COLORS.gradient.length]
    }))
  }

  const getCountryData = () => {
    if (!stats?.countries_breakdown) return []
    return Object.entries(stats.countries_breakdown)
      .sort(([,a], [,b]) => b - a)
      .slice(0, 10)
      .map(([name, value]) => ({ name, value }))
  }

  const getOrganizationData = () => {
    if (!stats?.organizations_breakdown) return []
    return Object.entries(stats.organizations_breakdown)
      .sort(([,a], [,b]) => b - a)
      .slice(0, 8)
      .map(([name, value]) => ({ name: name.length > 20 ? name.substring(0, 20) + '...' : name, value }))
  }

  // Generate mock time series data for demonstration
  const getTimeSeriesData = () => {
    const data = []
    const days = parseInt(timeRange)
    for (let i = days; i >= 0; i--) {
      const date = new Date()
      date.setDate(date.getDate() - i)
      data.push({
        date: date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
        tenders: Math.floor(Math.random() * 50) + 10,
        active: Math.floor(Math.random() * 30) + 5
      })
    }
    return data
  }

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress size={60} />
      </Box>
    )
  }

  if (error) {
    return (
      <Box>
        <Helmet>
          <title>Analytics - VisionSeal</title>
        </Helmet>
        <Alert severity="error" action={
          <button onClick={fetchAnalytics}>Retry</button>
        }>
          {error}
        </Alert>
      </Box>
    )
  }

  return (
    <Box>
      <Helmet>
        <title>Analytics - VisionSeal</title>
        <meta name="description" content="View analytics and insights about tenders" />
      </Helmet>
      
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Box>
          <Typography variant="h4" fontWeight="bold" gutterBottom>
            Analytics Dashboard
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Comprehensive insights into tender opportunities and performance metrics
          </Typography>
        </Box>
        
        <AnalyticsFilters
          timeRange={timeRange}
          onTimeRangeChange={setTimeRange}
        />
      </Box>

      {/* Key Metrics */}
      <Grid container spacing={3} mb={4}>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Total Tenders"
            value={stats?.total_tenders?.toLocaleString() || 0}
            icon={<Assessment fontSize="large" />}
            color={COLORS.primary}
            trend={12}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Active Tenders"
            value={stats?.active_tenders?.toLocaleString() || 0}
            icon={<CheckCircle fontSize="large" />}
            color={COLORS.success}
            trend={8}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Avg Relevance"
            value={`${(stats?.avg_relevance_score || 0).toFixed(1)}%`}
            icon={<TrendingUp fontSize="large" />}
            color={COLORS.warning}
            trend={-2}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Recent Tenders"
            value={stats?.recent_tenders_count?.toLocaleString() || 0}
            icon={<Schedule fontSize="large" />}
            color={COLORS.info}
            trend={15}
          />
        </Grid>
      </Grid>

      {/* Charts Grid */}
      <Grid container spacing={3}>
        {/* Tender Sources Pie Chart */}
        <Grid item xs={12} md={6}>
          <Card elevation={2}>
            <CardContent>
              <Typography variant="h6" gutterBottom fontWeight="bold">
                Tender Sources Distribution
              </Typography>
              <Box height={300}>
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={getSourceData()}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {getSourceData().map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Tender Trends Line Chart */}
        <Grid item xs={12} md={6}>
          <Card elevation={2}>
            <CardContent>
              <Typography variant="h6" gutterBottom fontWeight="bold">
                Tender Activity Trends
              </Typography>
              <Box height={300}>
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={getTimeSeriesData()}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Area
                      type="monotone"
                      dataKey="tenders"
                      stackId="1"
                      stroke={COLORS.primary}
                      fill={COLORS.primary}
                      fillOpacity={0.7}
                      name="Total Tenders"
                    />
                    <Area
                      type="monotone"
                      dataKey="active"
                      stackId="1"
                      stroke={COLORS.success}
                      fill={COLORS.success}
                      fillOpacity={0.7}
                      name="Active Tenders"
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Top Countries Bar Chart */}
        <Grid item xs={12} md={6}>
          <Card elevation={2}>
            <CardContent>
              <Typography variant="h6" gutterBottom fontWeight="bold">
                <Language sx={{ mr: 1, verticalAlign: 'middle' }} />
                Top Countries by Tender Count
              </Typography>
              <Box height={350}>
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={getCountryData()} layout="horizontal">
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis type="number" />
                    <YAxis dataKey="name" type="category" width={100} />
                    <Tooltip />
                    <Bar dataKey="value" fill={COLORS.info} />
                  </BarChart>
                </ResponsiveContainer>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Top Organizations Bar Chart */}
        <Grid item xs={12} md={6}>
          <Card elevation={2}>
            <CardContent>
              <Typography variant="h6" gutterBottom fontWeight="bold">
                <Business sx={{ mr: 1, verticalAlign: 'middle' }} />
                Top Organizations by Tender Count
              </Typography>
              <Box height={350}>
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={getOrganizationData()}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis
                      dataKey="name"
                      angle={-45}
                      textAnchor="end"
                      height={100}
                      fontSize={12}
                    />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="value" fill={COLORS.secondary} />
                  </BarChart>
                </ResponsiveContainer>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  )
}

export default Analytics