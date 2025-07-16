import React from 'react'
import {
  Box,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  SelectChangeEvent
} from '@mui/material'

interface AnalyticsFiltersProps {
  timeRange: string
  onTimeRangeChange: (value: string) => void
}

const AnalyticsFilters: React.FC<AnalyticsFiltersProps> = ({
  timeRange,
  onTimeRangeChange
}) => {
  const handleChange = (event: SelectChangeEvent) => {
    onTimeRangeChange(event.target.value)
  }

  return (
    <Box>
      <FormControl size="small" sx={{ minWidth: 120 }}>
        <InputLabel>Time Range</InputLabel>
        <Select
          value={timeRange}
          label="Time Range"
          onChange={handleChange}
        >
          <MenuItem value="7">Last 7 days</MenuItem>
          <MenuItem value="30">Last 30 days</MenuItem>
          <MenuItem value="90">Last 90 days</MenuItem>
          <MenuItem value="365">Last year</MenuItem>
        </Select>
      </FormControl>
    </Box>
  )
}

export default AnalyticsFilters