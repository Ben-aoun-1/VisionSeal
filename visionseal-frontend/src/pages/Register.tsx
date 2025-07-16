import React, { useState, useEffect } from 'react';
import {
  Box,
  Container,
  Paper,
  TextField,
  Button,
  Typography,
  Alert,
  Link,
  Divider,
  IconButton,
  InputAdornment,
  CircularProgress,
  Grid,
  MenuItem,
  Fade,
  Slide,
  Zoom,
  Grow,
  Stepper,
  Step,
  StepLabel
} from '@mui/material';
import { 
  Visibility, 
  VisibilityOff, 
  Email, 
  Lock, 
  Person, 
  Business, 
  Phone, 
  Public,
  PersonAdd,
  KeyboardArrowRight,
  CheckCircle,
  Work,
  LocationOn
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';

const Register: React.FC = () => {
  const navigate = useNavigate();
  const { register, isLoading } = useAuth();
  
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    confirmPassword: '',
    firstName: '',
    lastName: '',
    phone: '',
    company: '',
    sector: '',
    address: ''
  });
  
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [mounted, setMounted] = useState(false);
  const [focusedField, setFocusedField] = useState<string | null>(null);
  const [currentStep, setCurrentStep] = useState(0);

  const steps = ['Personal Info', 'Company Info'];

  useEffect(() => {
    setMounted(true);
  }, []);

  const countries = [
    'Tunisia', 'Morocco', 'Algeria', 'Egypt', 'Libya', 'Sudan',
    'Nigeria', 'Ghana', 'Senegal', 'Mali', 'Burkina Faso', 'Niger',
    'Guinea', 'Sierra Leone', 'Liberia', 'Ivory Coast', 'Benin', 'Togo',
    'Kenya', 'Ethiopia', 'Tanzania', 'Uganda', 'Rwanda', 'Burundi',
    'Somalia', 'Madagascar', 'Mauritius', 'Democratic Republic of Congo',
    'Congo', 'Cameroon', 'Chad', 'Gabon', 'Central African Republic',
    'South Africa', 'Botswana', 'Namibia', 'Zimbabwe', 'Zambia',
    'Angola', 'Mozambique', 'Malawi', 'Lesotho'
  ];

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData(prev => ({
      ...prev,
      [e.target.name]: e.target.value
    }));
    // Clear error when user starts typing
    if (error) setError('');
  };

  const validateForm = () => {
    if (formData.password !== formData.confirmPassword) {
      setError('Passwords do not match');
      return false;
    }
    
    if (formData.password.length < 8) {
      setError('Password must be at least 8 characters long');
      return false;
    }
    
    if (!formData.password.match(/[A-Z]/)) {
      setError('Password must contain at least one uppercase letter');
      return false;
    }
    
    if (!formData.password.match(/[a-z]/)) {
      setError('Password must contain at least one lowercase letter');
      return false;
    }
    
    if (!formData.password.match(/[0-9]/)) {
      setError('Password must contain at least one digit');
      return false;
    }
    
    if (!formData.firstName.trim() || !formData.lastName.trim()) {
      setError('First name and last name are required');
      return false;
    }
    
    return true;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    if (!validateForm()) {
      return;
    }

    try {
      const result = await register({
        email: formData.email,
        password: formData.password,
        firstName: formData.firstName,
        lastName: formData.lastName,
        company: formData.company,
        phone: formData.phone,
        sector: formData.sector,
        address: formData.address
      });
      
      if (result.success) {
        setSuccess('Registration successful! Please check your email for verification.');
        setTimeout(() => navigate('/login'), 3000);
      } else {
        setError(result.error || 'Registration failed. Please try again.');
      }
    } catch (err: any) {
      setError(err.message || 'An unexpected error occurred');
    }
  };

  const togglePasswordVisibility = () => {
    setShowPassword(!showPassword);
  };

  const toggleConfirmPasswordVisibility = () => {
    setShowConfirmPassword(!showConfirmPassword);
  };

  return (
    <Box sx={{ 
      minHeight: '100vh', 
      display: 'flex',
      background: 'linear-gradient(135deg, #0a0a23 0%, #1a1a2e 25%, #16213e 50%, #0f3460 75%, #533483 100%)',
      position: 'relative',
      overflow: 'hidden'
    }}>
      {/* Animated Background Elements */}
      <Box sx={{
        position: 'absolute',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        zIndex: 0,
        '&::before': {
          content: '""',
          position: 'absolute',
          top: '15%',
          left: '15%',
          width: '250px',
          height: '250px',
          background: 'radial-gradient(circle, rgba(139, 92, 246, 0.2) 0%, transparent 70%)',
          borderRadius: '50%',
          animation: 'pulse 4s ease-in-out infinite',
        },
        '&::after': {
          content: '""',
          position: 'absolute',
          bottom: '15%',
          right: '15%',
          width: '350px',
          height: '350px',
          background: 'radial-gradient(circle, rgba(59, 130, 246, 0.15) 0%, transparent 70%)',
          borderRadius: '50%',
          animation: 'pulse 6s ease-in-out infinite reverse',
        },
        '@keyframes pulse': {
          '0%, 100%': {
            transform: 'scale(1)',
            opacity: 0.5,
          },
          '50%': {
            transform: 'scale(1.2)',
            opacity: 0.8,
          },
        },
      }} />
      
      {/* Geometric Shapes */}
      <Box sx={{
        position: 'absolute',
        top: '20%',
        right: '20%',
        width: '80px',
        height: '80px',
        border: '2px solid rgba(255,255,255,0.1)',
        borderRadius: '20px',
        animation: 'rotate 10s linear infinite',
        zIndex: 0,
        '@keyframes rotate': {
          '0%': {
            transform: 'rotate(0deg)',
          },
          '100%': {
            transform: 'rotate(360deg)',
          },
        },
      }} />
      
      <Box sx={{
        position: 'absolute',
        bottom: '30%',
        left: '25%',
        width: '60px',
        height: '60px',
        border: '2px solid rgba(255,255,255,0.08)',
        borderRadius: '50%',
        animation: 'float 8s ease-in-out infinite',
        zIndex: 0,
        '@keyframes float': {
          '0%, 100%': {
            transform: 'translateY(0px)',
          },
          '50%': {
            transform: 'translateY(-30px)',
          },
        },
      }} />

      <Container maxWidth="lg" sx={{ 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'center',
        py: 4,
        zIndex: 1
      }}>
        <Fade in={mounted} timeout={1000}>
          <Box sx={{ 
            width: '100%', 
            maxWidth: 900,
            minHeight: 700,
            borderRadius: 4,
            overflow: 'hidden',
            boxShadow: '0 50px 100px -20px rgba(0, 0, 0, 0.5)',
            backgroundColor: 'rgba(255, 255, 255, 0.98)',
            backdropFilter: 'blur(20px)',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            position: 'relative',
            animation: 'slideUp 0.8s ease-out',
            '@keyframes slideUp': {
              '0%': {
                transform: 'translateY(60px)',
                opacity: 0,
              },
              '100%': {
                transform: 'translateY(0)',
                opacity: 1,
              },
            },
          }}>
            {/* Header Section */}
            <Box sx={{
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%)',
              p: 4,
              textAlign: 'center',
              color: 'white',
              position: 'relative',
              '&::before': {
                content: '""',
                position: 'absolute',
                top: 0,
                left: 0,
                right: 0,
                bottom: 0,
                background: 'linear-gradient(45deg, transparent 30%, rgba(255,255,255,0.1) 50%, transparent 70%)',
                animation: 'headerShimmer 3s infinite',
                '@keyframes headerShimmer': {
                  '0%': {
                    transform: 'translateX(-100%)',
                  },
                  '100%': {
                    transform: 'translateX(100%)',
                  },
                },
              },
            }}>
              <Zoom in={mounted} timeout={1200}>
                <Box sx={{ position: 'relative', zIndex: 1 }}>
                  <PersonAdd sx={{ fontSize: 48, mb: 2, opacity: 0.9 }} />
                  <Typography variant="h3" fontWeight="bold" gutterBottom sx={{ 
                    fontSize: { xs: '2rem', md: '3rem' },
                    background: 'linear-gradient(135deg, #ffffff 0%, #f0f8ff 100%)',
                    WebkitBackgroundClip: 'text',
                    WebkitTextFillColor: 'transparent',
                    backgroundClip: 'text',
                    textShadow: '0 4px 20px rgba(255,255,255,0.3)',
                  }}>
                    Join VisionSeal
                  </Typography>
                  <Typography variant="h6" sx={{ 
                    mb: 2, 
                    opacity: 0.9,
                    fontWeight: 300
                  }}>
                    Create your account and start discovering opportunities
                  </Typography>
                  
                  {/* Progress Steps */}
                  <Fade in={mounted} timeout={1800}>
                    <Box sx={{ mt: 3, maxWidth: 400, mx: 'auto' }}>
                      <Stepper 
                        activeStep={currentStep} 
                        alternativeLabel
                        sx={{
                          '& .MuiStepLabel-root': {
                            color: 'rgba(255,255,255,0.8)',
                          },
                          '& .MuiStepIcon-root': {
                            color: 'rgba(255,255,255,0.3)',
                            '&.Mui-active': {
                              color: 'rgba(255,255,255,0.9)',
                            },
                            '&.Mui-completed': {
                              color: 'rgba(255,255,255,0.9)',
                            },
                          },
                        }}
                      >
                        {steps.map((label, index) => (
                          <Step key={label}>
                            <StepLabel sx={{ 
                              '& .MuiStepLabel-label': {
                                color: 'rgba(255,255,255,0.8)',
                                fontSize: '0.8rem',
                              }
                            }}>
                              {label}
                            </StepLabel>
                          </Step>
                        ))}
                      </Stepper>
                    </Box>
                  </Fade>
                </Box>
              </Zoom>
            </Box>

            {/* Form Section */}
            <Box sx={{ p: 6, backgroundColor: 'white' }}>
              <Box component="form" onSubmit={handleSubmit}>
                {error && (
                  <Fade in={!!error} timeout={300}>
                    <Alert severity="error" sx={{ mb: 3, borderRadius: 2 }}>
                      {error}
                    </Alert>
                  </Fade>
                )}
                
                {success && (
                  <Fade in={!!success} timeout={300}>
                    <Alert severity="success" sx={{ mb: 3, borderRadius: 2 }}>
                      {success}
                    </Alert>
                  </Fade>
                )}

                <Slide direction="up" in={mounted} timeout={1400}>
                  <Grid container spacing={4}>
                    {/* Personal Info Section */}
                    <Grid item xs={12}>
                      <Typography variant="h6" sx={{ 
                        color: 'rgba(255, 255, 255, 0.9)',
                        fontWeight: 600,
                        mb: 2,
                        textAlign: 'center'
                      }}>
                        Personal Information
                      </Typography>
                    </Grid>
                    <Grid item xs={12} sm={6}>
                      <Fade in={mounted} timeout={1600}>
                        <TextField
                          fullWidth
                          name="firstName"
                          label="First Name"
                          value={formData.firstName}
                          onChange={handleChange}
                          onFocus={() => setFocusedField('firstName')}
                          onBlur={() => setFocusedField(null)}
                          required
                          margin="normal"
                          variant="outlined"
                          InputProps={{
                            startAdornment: (
                              <InputAdornment position="start">
                                <Person sx={{ 
                                  color: focusedField === 'firstName' ? '#667eea' : '#64748b',
                                  transition: 'all 0.3s ease'
                                }} />
                              </InputAdornment>
                            )
                          }}
                          sx={{
                            '& .MuiOutlinedInput-root': {
                              backgroundColor: '#f8fafc',
                              borderRadius: 2,
                              transition: 'all 0.3s ease',
                              '& fieldset': {
                                borderColor: '#e2e8f0',
                                borderWidth: '1px',
                              },
                              '&:hover fieldset': {
                                borderColor: '#cbd5e1',
                              },
                              '&.Mui-focused fieldset': {
                                borderColor: '#667eea',
                                borderWidth: '2px',
                                boxShadow: '0 0 0 3px rgba(102, 126, 234, 0.1)',
                              },
                            },
                            '& .MuiInputLabel-root': {
                              color: '#64748b',
                              '&.Mui-focused': {
                                color: '#667eea',
                              },
                            },
                            '& .MuiInputBase-input': {
                              color: '#1e293b',
                            },
                          }}
                        />
                      </Fade>
                    </Grid>

            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                name="lastName"
                label="Last Name"
                value={formData.lastName}
                onChange={handleChange}
                required
                margin="normal"
                variant="outlined"
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <Person sx={{ color: '#64748b' }} />
                    </InputAdornment>
                  )
                }}
                sx={{
                  '& .MuiOutlinedInput-root': {
                    backgroundColor: '#f8fafc',
                    borderRadius: 2,
                    '& fieldset': {
                      borderColor: '#e2e8f0',
                    },
                    '&:hover fieldset': {
                      borderColor: '#cbd5e1',
                    },
                    '&.Mui-focused fieldset': {
                      borderColor: '#667eea',
                    },
                  },
                  '& .MuiInputLabel-root': {
                    color: '#64748b',
                  },
                  '& .MuiInputBase-input': {
                    color: '#1e293b',
                  },
                }}
              />
            </Grid>

            <Grid item xs={12}>
              <TextField
                fullWidth
                name="email"
                label="Email Address"
                type="email"
                value={formData.email}
                onChange={handleChange}
                required
                margin="normal"
                variant="outlined"
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <Email sx={{ color: '#64748b' }} />
                    </InputAdornment>
                  )
                }}
                sx={{
                  '& .MuiOutlinedInput-root': {
                    backgroundColor: '#f8fafc',
                    borderRadius: 2,
                    '& fieldset': {
                      borderColor: '#e2e8f0',
                    },
                    '&:hover fieldset': {
                      borderColor: '#cbd5e1',
                    },
                    '&.Mui-focused fieldset': {
                      borderColor: '#667eea',
                    },
                  },
                  '& .MuiInputLabel-root': {
                    color: '#64748b',
                  },
                  '& .MuiInputBase-input': {
                    color: '#1e293b',
                  },
                }}
              />
            </Grid>

            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                name="password"
                label="Password"
                type={showPassword ? 'text' : 'password'}
                value={formData.password}
                onChange={handleChange}
                required
                margin="normal"
                variant="outlined"
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <Lock sx={{ color: '#64748b' }} />
                    </InputAdornment>
                  ),
                  endAdornment: (
                    <InputAdornment position="end">
                      <IconButton
                        onClick={togglePasswordVisibility}
                        edge="end"
                        sx={{ color: '#64748b' }}
                      >
                        {showPassword ? <VisibilityOff /> : <Visibility />}
                      </IconButton>
                    </InputAdornment>
                  )
                }}
                sx={{
                  '& .MuiOutlinedInput-root': {
                    backgroundColor: '#f8fafc',
                    borderRadius: 2,
                    '& fieldset': {
                      borderColor: '#e2e8f0',
                    },
                    '&:hover fieldset': {
                      borderColor: '#cbd5e1',
                    },
                    '&.Mui-focused fieldset': {
                      borderColor: '#667eea',
                    },
                  },
                  '& .MuiInputLabel-root': {
                    color: '#64748b',
                  },
                  '& .MuiInputBase-input': {
                    color: '#1e293b',
                  },
                }}
              />
              <Typography variant="caption" sx={{ 
                color: 'rgba(255, 255, 255, 0.7)', 
                mt: 1, 
                display: 'block',
                fontSize: '0.75rem'
              }}>
                Password must contain:
                <br />• At least 8 characters
                <br />• One uppercase letter
                <br />• One lowercase letter  
                <br />• One digit
              </Typography>
            </Grid>

            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                name="confirmPassword"
                label="Confirm Password"
                type={showConfirmPassword ? 'text' : 'password'}
                value={formData.confirmPassword}
                onChange={handleChange}
                required
                margin="normal"
                variant="outlined"
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <Lock sx={{ color: '#64748b' }} />
                    </InputAdornment>
                  ),
                  endAdornment: (
                    <InputAdornment position="end">
                      <IconButton
                        onClick={toggleConfirmPasswordVisibility}
                        edge="end"
                        sx={{ color: '#64748b' }}
                      >
                        {showConfirmPassword ? <VisibilityOff /> : <Visibility />}
                      </IconButton>
                    </InputAdornment>
                  )
                }}
                sx={{
                  '& .MuiOutlinedInput-root': {
                    backgroundColor: '#f8fafc',
                    borderRadius: 2,
                    '& fieldset': {
                      borderColor: '#e2e8f0',
                    },
                    '&:hover fieldset': {
                      borderColor: '#cbd5e1',
                    },
                    '&.Mui-focused fieldset': {
                      borderColor: '#667eea',
                    },
                  },
                  '& .MuiInputLabel-root': {
                    color: '#64748b',
                  },
                  '& .MuiInputBase-input': {
                    color: '#1e293b',
                  },
                }}
              />
            </Grid>


            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                name="phone"
                label="Phone (Optional)"
                value={formData.phone}
                onChange={handleChange}
                margin="normal"
                variant="outlined"
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <Phone sx={{ color: '#64748b' }} />
                    </InputAdornment>
                  )
                }}
                sx={{
                  '& .MuiOutlinedInput-root': {
                    backgroundColor: '#f8fafc',
                    borderRadius: 2,
                    '& fieldset': {
                      borderColor: '#e2e8f0',
                    },
                    '&:hover fieldset': {
                      borderColor: '#cbd5e1',
                    },
                    '&.Mui-focused fieldset': {
                      borderColor: '#667eea',
                    },
                  },
                  '& .MuiInputLabel-root': {
                    color: '#64748b',
                  },
                  '& .MuiInputBase-input': {
                    color: '#1e293b',
                  },
                }}
              />
            </Grid>

            {/* Company Info Section */}
            <Grid item xs={12}>
              <Typography variant="h6" sx={{ 
                color: 'rgba(255, 255, 255, 0.9)',
                fontWeight: 600,
                mb: 2,
                mt: 2,
                textAlign: 'center'
              }}>
                Company Information
              </Typography>
            </Grid>

            <Grid item xs={12}>
              <TextField
                fullWidth
                name="company"
                label="Company Name"
                value={formData.company}
                onChange={handleChange}
                onFocus={() => setFocusedField('company')}
                onBlur={() => setFocusedField(null)}
                margin="normal"
                variant="outlined"
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <Business sx={{ color: focusedField === 'company' ? '#667eea' : '#64748b' }} />
                    </InputAdornment>
                  ),
                }}
                sx={{
                  '& .MuiOutlinedInput-root': {
                    backgroundColor: 'rgba(255, 255, 255, 0.9)',
                    borderRadius: '12px',
                    '& fieldset': {
                      borderColor: 'rgba(100, 116, 139, 0.3)',
                    },
                    '&:hover fieldset': {
                      borderColor: '#667eea',
                    },
                    '&.Mui-focused fieldset': {
                      borderColor: '#667eea',
                    },
                  },
                  '& .MuiInputLabel-root': {
                    color: '#64748b',
                  },
                  '& .MuiInputBase-input': {
                    color: '#1e293b',
                  },
                }}
              />
            </Grid>

            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                name="sector"
                label="Sector / Area of Work"
                value={formData.sector}
                onChange={handleChange}
                onFocus={() => setFocusedField('sector')}
                onBlur={() => setFocusedField(null)}
                margin="normal"
                variant="outlined"
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <Work sx={{ color: focusedField === 'sector' ? '#667eea' : '#64748b' }} />
                    </InputAdornment>
                  ),
                }}
                sx={{
                  '& .MuiOutlinedInput-root': {
                    backgroundColor: 'rgba(255, 255, 255, 0.9)',
                    borderRadius: '12px',
                    '& fieldset': {
                      borderColor: 'rgba(100, 116, 139, 0.3)',
                    },
                    '&:hover fieldset': {
                      borderColor: '#667eea',
                    },
                    '&.Mui-focused fieldset': {
                      borderColor: '#667eea',
                    },
                  },
                  '& .MuiInputLabel-root': {
                    color: '#64748b',
                  },
                  '& .MuiInputBase-input': {
                    color: '#1e293b',
                  },
                }}
              />
            </Grid>

            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                name="address"
                label="Address"
                value={formData.address}
                onChange={handleChange}
                onFocus={() => setFocusedField('address')}
                onBlur={() => setFocusedField(null)}
                margin="normal"
                variant="outlined"
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <LocationOn sx={{ color: focusedField === 'address' ? '#667eea' : '#64748b' }} />
                    </InputAdornment>
                  ),
                }}
                sx={{
                  '& .MuiOutlinedInput-root': {
                    backgroundColor: 'rgba(255, 255, 255, 0.9)',
                    borderRadius: '12px',
                    '& fieldset': {
                      borderColor: 'rgba(100, 116, 139, 0.3)',
                    },
                    '&:hover fieldset': {
                      borderColor: '#667eea',
                    },
                    '&.Mui-focused fieldset': {
                      borderColor: '#667eea',
                    },
                  },
                  '& .MuiInputLabel-root': {
                    color: '#64748b',
                  },
                  '& .MuiInputBase-input': {
                    color: '#1e293b',
                  },
                }}
              />
            </Grid>
                  </Grid>
                </Slide>

                <Zoom in={mounted} timeout={2000}>
                  <Button
                    type="submit"
                    fullWidth
                    variant="contained"
                    size="large"
                    disabled={isLoading}
                    endIcon={!isLoading && <KeyboardArrowRight />}
                    sx={{
                      mt: 4,
                      py: 2,
                      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                      color: 'white',
                      fontSize: '1.1rem',
                      fontWeight: 'bold',
                      borderRadius: 3,
                      textTransform: 'none',
                      boxShadow: '0 8px 25px 0 rgba(102, 126, 234, 0.4)',
                      border: 'none',
                      position: 'relative',
                      overflow: 'hidden',
                      '&::before': {
                        content: '""',
                        position: 'absolute',
                        top: 0,
                        left: '-100%',
                        width: '100%',
                        height: '100%',
                        background: 'linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent)',
                        transition: 'left 0.5s',
                      },
                      '&:hover': {
                        background: 'linear-gradient(135deg, #5a67d8 0%, #667eea 100%)',
                        boxShadow: '0 12px 35px 0 rgba(102, 126, 234, 0.6)',
                        transform: 'translateY(-2px)',
                        '&::before': {
                          left: '100%',
                        },
                      },
                      '&:active': {
                        transform: 'translateY(0px)',
                      },
                      '&:disabled': {
                        background: '#e2e8f0',
                        color: '#94a3b8',
                        boxShadow: 'none',
                        transform: 'none',
                      },
                      transition: 'all 0.3s ease',
                    }}
                  >
                    {isLoading ? (
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <CircularProgress size={20} color="inherit" />
                        <span>Creating Account...</span>
                      </Box>
                    ) : (
                      'Create Account'
                    )}
                  </Button>
                </Zoom>

                <Fade in={mounted} timeout={2200}>
                  <Divider sx={{ my: 4, backgroundColor: '#e2e8f0' }} />
                </Fade>

                <Fade in={mounted} timeout={2400}>
                  <Box sx={{ textAlign: 'center' }}>
                    <Typography variant="body2" sx={{ color: '#64748b' }}>
                      Already have an account?{' '}
                      <Link
                        component="button"
                        type="button"
                        variant="body2"
                        onClick={() => navigate('/login')}
                        sx={{ 
                          color: '#667eea',
                          fontWeight: 'bold',
                          textDecoration: 'none',
                          transition: 'all 0.3s ease',
                          '&:hover': {
                            color: '#764ba2',
                            textDecoration: 'underline',
                            transform: 'translateY(-1px)',
                          }
                        }}
                      >
                        Sign In Here
                      </Link>
                    </Typography>
                  </Box>
                </Fade>
              </Box>
            </Box>
          </Box>
        </Fade>
      </Container>
    </Box>
  );
};

export default Register;