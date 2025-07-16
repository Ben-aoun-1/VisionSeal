import React, { useState, useEffect } from 'react'
import {
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  Button,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  Alert,
  CircularProgress,
  Paper,
  Divider,
  useTheme,
  IconButton,
  Tooltip
} from '@mui/material'
import {
  AutoAwesome,
  Description,
  Download,
  Preview,
  Send,
  History,
  Settings,
  TrendingUp,
  Assessment,
  Refresh
} from '@mui/icons-material'
import { Helmet } from 'react-helmet-async'
import ReactMarkdown from 'react-markdown'
import { tenderApi, aiApi } from '../utils/api'
import { Tender } from '../types/tender'

interface AIReportRequest {
  tenderId: string
  reportType: 'proposal' | 'analysis' | 'summary'
  tone: 'professional' | 'technical' | 'persuasive'
  length: 'brief' | 'detailed' | 'comprehensive'
  customInstructions?: string
}

const AIReports: React.FC = () => {
  const theme = useTheme()
  const [selectedTender, setSelectedTender] = useState<Tender | null>(null)
  const [tenders, setTenders] = useState<Tender[]>([])
  const [loading, setLoading] = useState(false)
  const [generating, setGenerating] = useState(false)
  const [generatedReport, setGeneratedReport] = useState<string>('')
  const [reportRequest, setReportRequest] = useState<AIReportRequest>({
    tenderId: '',
    reportType: 'proposal',
    tone: 'professional',
    length: 'detailed',
    customInstructions: ''
  })

  useEffect(() => {
    fetchTenders()
  }, [])

  const fetchTenders = async () => {
    try {
      setLoading(true)
      const response = await tenderApi.getTenders({
        status: 'ACTIVE',
        per_page: 50,
        sort_by: 'publication_date',
        sort_order: 'desc'
      })
      setTenders(response.tenders)
    } catch (error) {
      console.error('Failed to fetch tenders:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleTenderSelect = (tender: Tender) => {
    setSelectedTender(tender)
    setReportRequest(prev => ({ ...prev, tenderId: tender.id }))
  }

  const generateReport = async () => {
    if (!selectedTender) return
    
    try {
      setGenerating(true)
      
      // Prepare request data
      const requestData = {
        tenderId: selectedTender.id,
        reportType: reportRequest.reportType,
        tone: reportRequest.tone,
        length: reportRequest.length,
        customInstructions: reportRequest.customInstructions || undefined
      }
      
      console.log('🚀 Calling AI API with data:', requestData)
      console.log('📋 Selected tender:', selectedTender)
      
      // Call the real AI API
      const response = await aiApi.generateReport(requestData)
      
      console.log('✅ AI API response received:', {
        hasContent: !!response?.content,
        contentLength: response?.content?.length || 0,
        status: response?.status,
        reportId: response?.report_id,
        fullResponse: response
      })
      
      // Validate response has content
      if (!response) {
        throw new Error('No response received from AI API')
      }
      
      if (!response.content) {
        throw new Error('Response received but no content field found')
      }
      
      if (typeof response.content !== 'string') {
        throw new Error(`Content is not a string, got: ${typeof response.content}`)
      }
      
      if (response.content.length === 0) {
        throw new Error('Content is empty')
      }
      
      console.log('✅ Content validation passed, setting report content')
      console.log('📄 Content preview:', response.content.substring(0, 200) + '...')
      
      // Set the generated content from the API response
      setGeneratedReport(response.content)
      
      console.log('✅ Report content set in state')
      
    } catch (error: any) {
      console.error('Failed to generate report:', error)
      
      // Get detailed error information
      const errorMessage = error?.response?.data?.detail || error?.response?.data?.message || error?.message || 'Erreur inconnue'
      const statusCode = error?.response?.status || 'N/A'
      const errorData = error?.response?.data || {}
      const isTimeout = error?.code === 'ECONNABORTED' || error?.message?.includes('timeout')
      
      console.log('Error details:', {
        message: errorMessage,
        status: statusCode,
        data: errorData,
        isTimeout,
        fullError: error
      })
      
      let errorReport = ''
      
      if (isTimeout) {
        errorReport = `
# Génération de Rapport en Cours

⏰ **Le rapport est en cours de génération mais prend plus de temps que prévu.**

## Statut Actuel
- **Appel d'offres:** ${selectedTender?.title || 'N/A'}
- **Type de rapport:** ${reportRequest.reportType}
- **Longueur:** ${reportRequest.length}
- **Ton:** ${reportRequest.tone}
- **Heure de démarrage:** ${new Date().toLocaleString()}

## Que se passe-t-il ?
L'IA analyse en détail votre appel d'offres pour générer un rapport de haute qualité. Les rapports détaillés et complets peuvent prendre jusqu'à 2-3 minutes pour garantir la meilleure qualité possible.

## Que faire maintenant ?
1. ✅ **Attendez encore 1-2 minutes** - La génération continue en arrière-plan
2. 🔄 **Cliquez sur "Regenerate"** pour relancer le processus
3. 📊 **Essayez un rapport "brief"** pour un résultat plus rapide
4. 🔍 **Vérifiez la console du navigateur** pour plus de détails

## Optimisations Suggérées
- Pour des tests rapides, utilisez la longueur "Brief" (30-60 secondes)
- Les rapports "Detailed" prennent 60-90 secondes
- Les rapports "Comprehensive" peuvent prendre 90-120 secondes

---
*Le système continue de travailler en arrière-plan. Réessayez dans quelques instants.*
        `
      } else {
        errorReport = `
# Erreur de Génération de Rapport

Une erreur s'est produite lors de la génération du rapport IA.

## Détails de l'Erreur
- **Code de statut:** ${statusCode}
- **Message:** ${errorMessage}
- **Appel d'offres:** ${selectedTender?.title || 'N/A'}
- **Type de rapport:** ${reportRequest.reportType}
- **Heure:** ${new Date().toLocaleString()}

## Informations Techniques
\`\`\`
${JSON.stringify(errorData, null, 2)}
\`\`\`

## Suggestions
- Vérifiez que le backend est démarré (http://localhost:8080)
- Consultez la console du navigateur pour plus de détails
- Vérifiez que l'appel d'offres existe
- Réessayez dans quelques instants
- Contactez le support si le problème persiste

---
*Généré le ${new Date().toLocaleString()} par VisionSeal AI*
        `
      }
      
      setGeneratedReport(errorReport)
    } finally {
      setGenerating(false)
    }
  }

  const downloadReport = () => {
    const blob = new Blob([generatedReport], { type: 'text/markdown' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `tender-response-${selectedTender?.id || 'report'}.md`
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <Box>
      <Helmet>
        <title>AI Reports - VisionSeal</title>
        <meta name="description" content="Generate AI-powered tender response reports" />
      </Helmet>

      {/* Header */}
      <Box mb={4}>
        <Box display="flex" alignItems="center" gap={2} mb={2}>
          <AutoAwesome color="primary" fontSize="large" />
          <Typography variant="h4" fontWeight="bold">
            AI Report Generator
          </Typography>
        </Box>
        <Typography variant="body1" color="text.secondary">
          Generate intelligent tender response reports using AI to analyze opportunities and create compelling proposals
        </Typography>
      </Box>

      <Grid container spacing={3}>
        {/* Left Panel - Tender Selection & Configuration */}
        <Grid item xs={12} lg={6}>
          {/* Tender Selection */}
          <Card elevation={2} sx={{ mb: 3 }}>
            <CardContent>
              <Box display="flex" justifyContent="between" alignItems="center" mb={2}>
                <Typography variant="h6" fontWeight="bold">
                  Select Tender Opportunity
                </Typography>
                <IconButton onClick={fetchTenders} size="small">
                  <Refresh />
                </IconButton>
              </Box>
              
              {loading ? (
                <Box display="flex" justifyContent="center" p={2}>
                  <CircularProgress />
                </Box>
              ) : (
                <FormControl fullWidth>
                  <InputLabel>Choose Tender</InputLabel>
                  <Select
                    value={selectedTender?.id || ''}
                    label="Choose Tender"
                    onChange={(e) => {
                      const tender = tenders.find(t => t.id === e.target.value)
                      if (tender) handleTenderSelect(tender)
                    }}
                  >
                    {tenders.map((tender) => (
                      <MenuItem key={tender.id} value={tender.id}>
                        <Box>
                          <Typography variant="body2" fontWeight="medium">
                            {tender.title.length > 50 ? tender.title.substring(0, 50) + '...' : tender.title}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            {tender.organization} • {tender.country}
                          </Typography>
                        </Box>
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              )}

              {selectedTender && (
                <Paper variant="outlined" sx={{ mt: 2, p: 2 }}>
                  <Typography variant="body2" fontWeight="medium" gutterBottom>
                    Selected Tender Details
                  </Typography>
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    <strong>Title:</strong> {selectedTender.title}
                  </Typography>
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    <strong>Organization:</strong> {selectedTender.organization}
                  </Typography>
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    <strong>Deadline:</strong> {selectedTender.deadline || 'Not specified'}
                  </Typography>
                  <Box mt={1}>
                    <Chip
                      size="small"
                      label={`Relevance: ${selectedTender.relevance_score}%`}
                      color={selectedTender.relevance_score > 80 ? 'success' : 'warning'}
                    />
                  </Box>
                </Paper>
              )}
            </CardContent>
          </Card>

          {/* Report Configuration */}
          <Card elevation={2}>
            <CardContent>
              <Typography variant="h6" fontWeight="bold" gutterBottom>
                Report Configuration
              </Typography>

              <Grid container spacing={2}>
                <Grid item xs={12} sm={6}>
                  <FormControl fullWidth size="small">
                    <InputLabel>Report Type</InputLabel>
                    <Select
                      value={reportRequest.reportType}
                      label="Report Type"
                      onChange={(e) => setReportRequest(prev => ({ 
                        ...prev, 
                        reportType: e.target.value as any 
                      }))}
                    >
                      <MenuItem value="proposal">Tender Proposal</MenuItem>
                      <MenuItem value="analysis">Market Analysis</MenuItem>
                      <MenuItem value="summary">Executive Summary</MenuItem>
                    </Select>
                  </FormControl>
                </Grid>

                <Grid item xs={12} sm={6}>
                  <FormControl fullWidth size="small">
                    <InputLabel>Tone</InputLabel>
                    <Select
                      value={reportRequest.tone}
                      label="Tone"
                      onChange={(e) => setReportRequest(prev => ({ 
                        ...prev, 
                        tone: e.target.value as any 
                      }))}
                    >
                      <MenuItem value="professional">Professional</MenuItem>
                      <MenuItem value="technical">Technical</MenuItem>
                      <MenuItem value="persuasive">Persuasive</MenuItem>
                    </Select>
                  </FormControl>
                </Grid>

                <Grid item xs={12}>
                  <FormControl fullWidth size="small">
                    <InputLabel>Length</InputLabel>
                    <Select
                      value={reportRequest.length}
                      label="Length"
                      onChange={(e) => setReportRequest(prev => ({ 
                        ...prev, 
                        length: e.target.value as any 
                      }))}
                    >
                      <MenuItem value="brief">Brief (1-2 pages)</MenuItem>
                      <MenuItem value="detailed">Detailed (3-5 pages)</MenuItem>
                      <MenuItem value="comprehensive">Comprehensive (6+ pages)</MenuItem>
                    </Select>
                  </FormControl>
                </Grid>

                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    multiline
                    rows={3}
                    size="small"
                    label="Custom Instructions (Optional)"
                    placeholder="Add any specific requirements or focus areas for the AI to consider..."
                    value={reportRequest.customInstructions}
                    onChange={(e) => setReportRequest(prev => ({ 
                      ...prev, 
                      customInstructions: e.target.value 
                    }))}
                  />
                </Grid>

                <Grid item xs={12}>
                  <Button
                    fullWidth
                    variant="contained"
                    size="large"
                    startIcon={generating ? <CircularProgress size={20} /> : <AutoAwesome />}
                    onClick={generateReport}
                    disabled={!selectedTender || generating}
                    sx={{ mt: 2 }}
                  >
                    {generating ? 'Generating Report... (This may take up to 2 minutes)' : 'Generate AI Report'}
                  </Button>
                  
                  {generating && (
                    <Alert severity="info" sx={{ mt: 2 }}>
                      <Typography variant="body2">
                        <strong>AI Report Generation in Progress</strong><br />
                        Please wait while our AI analyzes the tender and generates your custom report. 
                        This process typically takes 30-120 seconds depending on the complexity.
                      </Typography>
                    </Alert>
                  )}
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        {/* Right Panel - Report Preview */}
        <Grid item xs={12} lg={6}>
          <Card elevation={2} sx={{ height: 'fit-content' }}>
            <CardContent>
              <Box display="flex" justifyContent="between" alignItems="center" mb={2}>
                <Typography variant="h6" fontWeight="bold">
                  Generated Report Preview
                </Typography>
                {generatedReport && (
                  <Box>
                    <Tooltip title="Download Report">
                      <IconButton onClick={downloadReport} color="primary">
                        <Download />
                      </IconButton>
                    </Tooltip>
                  </Box>
                )}
              </Box>

              {!generatedReport ? (
                <Box 
                  display="flex" 
                  flexDirection="column" 
                  alignItems="center" 
                  justifyContent="center" 
                  minHeight="400px"
                  sx={{ 
                    border: `2px dashed ${theme.palette.divider}`,
                    borderRadius: 2,
                    backgroundColor: theme.palette.grey[50]
                  }}
                >
                  <Description sx={{ fontSize: 64, color: theme.palette.grey[400], mb: 2 }} />
                  <Typography variant="h6" color="text.secondary" gutterBottom>
                    No Report Generated Yet
                  </Typography>
                  <Typography variant="body2" color="text.secondary" align="center">
                    Select a tender and configure your report settings, then click "Generate AI Report" to create your custom tender response.
                  </Typography>
                </Box>
              ) : (
                <Paper 
                  variant="outlined" 
                  sx={{ 
                    p: 3, 
                    maxHeight: '600px', 
                    overflow: 'auto',
                    backgroundColor: theme.palette.background.paper
                  }}
                >
                  <ReactMarkdown
                    components={{
                      h1: ({ children }) => (
                        <Typography variant="h4" component="h1" gutterBottom sx={{ fontWeight: 'bold', color: theme.palette.primary.main }}>
                          {children}
                        </Typography>
                      ),
                      h2: ({ children }) => (
                        <Typography variant="h5" component="h2" gutterBottom sx={{ fontWeight: 'bold', mt: 3, mb: 2 }}>
                          {children}
                        </Typography>
                      ),
                      h3: ({ children }) => (
                        <Typography variant="h6" component="h3" gutterBottom sx={{ fontWeight: 'bold', mt: 2, mb: 1 }}>
                          {children}
                        </Typography>
                      ),
                      p: ({ children }) => (
                        <Typography variant="body1" paragraph sx={{ lineHeight: 1.7 }}>
                          {children}
                        </Typography>
                      ),
                      strong: ({ children }) => (
                        <Typography component="span" sx={{ fontWeight: 'bold' }}>
                          {children}
                        </Typography>
                      ),
                      ul: ({ children }) => (
                        <Box component="ul" sx={{ pl: 2, mb: 2 }}>
                          {children}
                        </Box>
                      ),
                      li: ({ children }) => (
                        <Typography component="li" variant="body1" sx={{ mb: 0.5, lineHeight: 1.6 }}>
                          {children}
                        </Typography>
                      ),
                      code: ({ children }) => (
                        <Typography 
                          component="code" 
                          sx={{ 
                            backgroundColor: theme.palette.grey[100],
                            padding: '2px 6px',
                            borderRadius: 1,
                            fontFamily: 'monospace',
                            fontSize: '0.875rem'
                          }}
                        >
                          {children}
                        </Typography>
                      ),
                      pre: ({ children }) => (
                        <Paper 
                          variant="outlined" 
                          sx={{ 
                            p: 2, 
                            mb: 2, 
                            backgroundColor: theme.palette.grey[50],
                            overflow: 'auto'
                          }}
                        >
                          <Typography component="pre" sx={{ fontFamily: 'monospace', fontSize: '0.875rem' }}>
                            {children}
                          </Typography>
                        </Paper>
                      ),
                      hr: () => (
                        <Divider sx={{ my: 3 }} />
                      )
                    }}
                  >
                    {generatedReport}
                  </ReactMarkdown>
                </Paper>
              )}

              {generatedReport && (
                <Box mt={2} display="flex" gap={1}>
                  <Button
                    variant="outlined"
                    startIcon={<Refresh />}
                    onClick={generateReport}
                    disabled={generating}
                  >
                    Regenerate
                  </Button>
                  <Button
                    variant="contained"
                    startIcon={<Download />}
                    onClick={downloadReport}
                  >
                    Download
                  </Button>
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  )
}

export default AIReports