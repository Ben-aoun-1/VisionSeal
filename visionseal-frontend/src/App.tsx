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
import SavedTenders from '@/pages/SavedTenders'
import TenderDetails from '@/pages/TenderDetails'
import Analytics from '@/pages/Analytics'
import AIReports from '@/pages/AIReports'
import Settings from '@/pages/Settings'
import Login from '@/pages/Login'
import Register from '@/pages/Register'
import NotFound from '@/pages/NotFound'
import ProtectedRoute from '@/components/Auth/ProtectedRoute'
import { AuthProvider } from '@/hooks/useAuth'

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
            <AuthProvider>
              <Routes>
                {/* Public routes - redirect to dashboard if already authenticated */}
                <Route path="/login" element={
                  <ProtectedRoute requireAuth={false}>
                    <Login />
                  </ProtectedRoute>
                } />
                <Route path="/register" element={
                  <ProtectedRoute requireAuth={false}>
                    <Register />
                  </ProtectedRoute>
                } />
                
                {/* Protected routes */}
                <Route path="/" element={
                  <ProtectedRoute>
                    <Layout>
                      <Dashboard />
                    </Layout>
                  </ProtectedRoute>
                } />
                <Route path="/dashboard" element={
                  <ProtectedRoute>
                    <Layout>
                      <Dashboard />
                    </Layout>
                  </ProtectedRoute>
                } />
                <Route path="/tenders" element={
                  <ProtectedRoute>
                    <Layout>
                      <Tenders />
                    </Layout>
                  </ProtectedRoute>
                } />
                <Route path="/saved-tenders" element={
                  <ProtectedRoute>
                    <Layout>
                      <SavedTenders />
                    </Layout>
                  </ProtectedRoute>
                } />
                <Route path="/tenders/:id" element={
                  <ProtectedRoute>
                    <Layout>
                      <TenderDetails />
                    </Layout>
                  </ProtectedRoute>
                } />
                <Route path="/analytics" element={
                  <ProtectedRoute>
                    <Layout>
                      <Analytics />
                    </Layout>
                  </ProtectedRoute>
                } />
                <Route path="/ai-reports" element={
                  <ProtectedRoute>
                    <Layout>
                      <AIReports />
                    </Layout>
                  </ProtectedRoute>
                } />
                <Route path="/settings" element={
                  <ProtectedRoute>
                    <Layout>
                      <Settings />
                    </Layout>
                  </ProtectedRoute>
                } />
                <Route path="*" element={<NotFound />} />
              </Routes>
            </AuthProvider>
          </Router>
          
          {/* React Query DevTools */}
          {import.meta.env.DEV && <ReactQueryDevtools initialIsOpen={false} />}
          
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