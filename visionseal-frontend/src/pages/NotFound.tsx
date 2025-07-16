import React from 'react'
import { Box, Typography, Button } from '@mui/material'
import { useNavigate } from 'react-router-dom'
import { Helmet } from 'react-helmet-async'

const NotFound: React.FC = () => {
  const navigate = useNavigate()

  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '60vh',
        textAlign: 'center',
      }}
    >
      <Helmet>
        <title>Page Not Found - VisionSeal</title>
        <meta name="description" content="The page you're looking for doesn't exist" />
      </Helmet>
      
      <Typography variant="h1" sx={{ fontSize: '6rem', fontWeight: 700, mb: 2 }}>
        404
      </Typography>
      <Typography variant="h4" gutterBottom>
        Page Not Found
      </Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
        The page you're looking for doesn't exist.
      </Typography>
      <Button
        variant="contained"
        onClick={() => navigate('/')}
        sx={{ px: 4, py: 1.5 }}
      >
        Go Home
      </Button>
    </Box>
  )
}

export default NotFound