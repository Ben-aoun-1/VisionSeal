import React, { useState } from 'react'
import {
  Card,
  CardContent,
  Typography,
  Box,
  Tabs,
  Tab,
  useTheme,
  Skeleton,
} from '@mui/material'
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from 'recharts'
import { styled } from '@mui/material/styles'
import { colors } from '@/theme/colors'
import { TenderStats } from '@/types/tender'

// Styled Components
const ChartContainer = styled(Card)(({ theme }) => ({
  height: 400,
  borderRadius: 12,
  border: `1px solid ${colors.border.light}`,
  boxShadow: '0px 2px 8px rgba(0, 0, 0, 0.04)',
}))

const TabPanel = styled(Box)({
  height: 320,
  padding: 16,
})

const ChartTitle = styled(Typography)({
  fontSize: '1.125rem',
  fontWeight: 600,
  color: colors.text.primary,
  marginBottom: 16,
})

const LegendContainer = styled(Box)({
  display: 'flex',
  flexWrap: 'wrap',
  gap: 16,
  marginTop: 16,
})

const LegendItem = styled(Box)({
  display: 'flex',
  alignItems: 'center',
  gap: 8,
})

const LegendDot = styled(Box)<{ color: string }>(({ color }) => ({
  width: 12,
  height: 12,
  borderRadius: '50%',
  backgroundColor: color,
}))

// Chart Colors
const CHART_COLORS = [
  colors.primary[500],
  colors.secondary[500],
  colors.success[500],
  colors.warning[500],
  colors.error[500],
  colors.neutral[500],
]

interface TenderChartProps {
  data: TenderStats | undefined
  loading?: boolean
}

const TenderChart: React.FC<TenderChartProps> = ({ data, loading = false }) => {
  const theme = useTheme()
  const [activeTab, setActiveTab] = useState(0)

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue)
  }

  // Prepare data for charts
  const sourcesData = data?.sources?.map((source, index) => ({
    name: source.source,
    value: source.count,
    color: CHART_COLORS[index % CHART_COLORS.length],
  })) || []

  const countriesData = data?.countries?.slice(0, 6).map((country, index) => ({
    name: country.country,
    value: country.count,
    color: CHART_COLORS[index % CHART_COLORS.length],
  })) || []

  const statusData = data?.status_breakdown?.map((status, index) => ({
    name: status.status,
    value: status.count,
    color: CHART_COLORS[index % CHART_COLORS.length],
  })) || []

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <Box
          sx={{
            backgroundColor: colors.background.paper,
            border: `1px solid ${colors.border.light}`,
            borderRadius: 1,
            padding: 2,
            boxShadow: theme.shadows[3],
          }}
        >
          <Typography variant="body2" sx={{ fontWeight: 600 }}>
            {label}
          </Typography>
          <Typography variant="body2" sx={{ color: colors.text.secondary }}>
            {payload[0].value} tenders
          </Typography>
        </Box>
      )
    }
    return null
  }

  const renderPieChart = (chartData: any[], title: string) => (
    <TabPanel>
      <ChartTitle>{title}</ChartTitle>
      <ResponsiveContainer width="100%" height={200}>
        <PieChart>
          <Pie
            data={chartData}
            cx="50%"
            cy="50%"
            outerRadius={80}
            dataKey="value"
            label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
            labelLine={false}
          >
            {chartData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.color} />
            ))}
          </Pie>
          <Tooltip content={<CustomTooltip />} />
        </PieChart>
      </ResponsiveContainer>
      <LegendContainer>
        {chartData.map((entry, index) => (
          <LegendItem key={entry.name}>
            <LegendDot color={entry.color} />
            <Typography variant="body2" sx={{ color: colors.text.secondary }}>
              {entry.name} ({entry.value})
            </Typography>
          </LegendItem>
        ))}
      </LegendContainer>
    </TabPanel>
  )

  const renderBarChart = (chartData: any[], title: string) => (
    <TabPanel>
      <ChartTitle>{title}</ChartTitle>
      <ResponsiveContainer width="100%" height={240}>
        <BarChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke={colors.border.light} />
          <XAxis
            dataKey="name"
            tick={{ fontSize: 12, fill: colors.text.secondary }}
            axisLine={{ stroke: colors.border.light }}
          />
          <YAxis
            tick={{ fontSize: 12, fill: colors.text.secondary }}
            axisLine={{ stroke: colors.border.light }}
          />
          <Tooltip content={<CustomTooltip />} />
          <Bar dataKey="value" fill={colors.primary[500]} radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </TabPanel>
  )

  if (loading) {
    return (
      <ChartContainer>
        <CardContent sx={{ p: 0 }}>
          <Box sx={{ px: 3, pt: 2 }}>
            <Skeleton variant="rectangular" width={200} height={40} />
          </Box>
          <Box sx={{ p: 3 }}>
            <Skeleton variant="rectangular" width="100%" height={300} />
          </Box>
        </CardContent>
      </ChartContainer>
    )
  }

  return (
    <ChartContainer>
      <CardContent sx={{ p: 0 }}>
        <Box sx={{ borderBottom: 1, borderColor: colors.border.light }}>
          <Tabs
            value={activeTab}
            onChange={handleTabChange}
            sx={{
              px: 2,
              '& .MuiTab-root': {
                textTransform: 'none',
                fontSize: '0.875rem',
                fontWeight: 500,
              },
            }}
          >
            <Tab label="Sources" />
            <Tab label="Countries" />
            <Tab label="Status" />
          </Tabs>
        </Box>

        {activeTab === 0 && renderPieChart(sourcesData, 'Tenders by Source')}
        {activeTab === 1 && renderBarChart(countriesData, 'Top Countries')}
        {activeTab === 2 && renderPieChart(statusData, 'Tenders by Status')}
      </CardContent>
    </ChartContainer>
  )
}

export default TenderChart