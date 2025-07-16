import React from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { ThemeProvider } from '@mui/material/styles'
import { CssBaseline } from '@mui/material'
import { QueryClient, QueryClientProvider } from 'react-query'
import { ReactQueryDevtools } from 'react-query/devtools'
import { Toaster } from 'react-hot-toast'
import { HelmetProvider } from 'react-helmet-async'

import theme from '@/theme/theme'
import Layout from '@/components/Layout/Layout'
import Dashboard from '@/pages/Dashboard'
import Tenders from '@/pages/Tenders'
import TenderDetails from '@/pages/TenderDetails'
import Analytics from '@/pages/Analytics'
import AIReports from '@/pages/AIReports'
import Settings from '@/pages/Settings'
import NotFound from '@/pages/NotFound'

// Create a client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 3,
      retryDelay: attemptIndex => Math.min(1000 * 2 ** attemptIndex, 30000),
      staleTime: 5 * 60 * 1000, // 5 minutes
      cacheTime: 10 * 60 * 1000, // 10 minutes
      refetchOnWindowFocus: false,
    },
  },
})

function App() {
  return (
    <HelmetProvider>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <QueryClientProvider client={queryClient}>
          <Router>
            <Layout>
              <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/dashboard" element={<Dashboard />} />
                <Route path="/tenders" element={<Tenders />} />
                <Route path="/tenders/:id" element={<TenderDetails />} />
                <Route path="/analytics" element={<Analytics />} />
                <Route path="/ai-reports" element={<AIReports />} />
                <Route path="/settings" element={<Settings />} />
                <Route path="*" element={<NotFound />} />
              </Routes>
            </Layout>
          </Router>
          
          {/* React Query DevTools */}
          {process.env.NODE_ENV === 'development' && <ReactQueryDevtools initialIsOpen={false} />}
          
          {/* Toast notifications */}
          <Toaster
            position="top-right"
            toastOptions={{
              duration: 4000,
              style: {
                background: theme.palette.background.paper,
                color: theme.palette.text.primary,
                border: `1px solid ${theme.palette.divider}`,
                boxShadow: theme.shadows[3],
              },
              success: {
                iconTheme: {
                  primary: theme.palette.success.main,
                  secondary: theme.palette.success.contrastText,
                },
              },
              error: {
                iconTheme: {
                  primary: theme.palette.error.main,
                  secondary: theme.palette.error.contrastText,
                },
              },
            }}
          />
        </QueryClientProvider>
      </ThemeProvider>
    </HelmetProvider>
  )
}

export default App