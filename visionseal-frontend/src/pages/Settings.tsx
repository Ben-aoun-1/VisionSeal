import React from 'react'
import { Box, Typography } from '@mui/material'
import { Helmet } from 'react-helmet-async'

const Settings: React.FC = () => {
  return (
    <Box>
      <Helmet>
        <title>Settings - VisionSeal</title>
        <meta name="description" content="Configure your VisionSeal preferences" />
      </Helmet>
      
      <Typography variant="h4" gutterBottom>
        Settings
      </Typography>
      <Typography variant="body1" color="text.secondary">
        Settings and configuration page coming soon.
      </Typography>
    </Box>
  )
}

export default Settings