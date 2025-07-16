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
  Fade,
  Slide,
  Zoom,
  Grow
} from '@mui/material';
import { Visibility, VisibilityOff, Email, Lock, KeyboardArrowRight } from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';

const Login: React.FC = () => {
  const navigate = useNavigate();
  const { login, isLoading } = useAuth();
  
  const [formData, setFormData] = useState({
    email: '',
    password: ''
  });
  
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [mounted, setMounted] = useState(false);
  const [focusedField, setFocusedField] = useState<string | null>(null);

  useEffect(() => {
    setMounted(true);
  }, []);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData(prev => ({
      ...prev,
      [e.target.name]: e.target.value
    }));
    // Clear error when user starts typing
    if (error) setError('');
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    try {
      const result = await login(formData.email, formData.password);
      
      if (result.success) {
        setSuccess('Login successful! Redirecting...');
        setTimeout(() => navigate('/dashboard'), 1500);
      } else {
        setError(result.error || 'Login failed. Please try again.');
      }
    } catch (err: any) {
      setError(err.message || 'An unexpected error occurred');
    }
  };

  const togglePasswordVisibility = () => {
    setShowPassword(!showPassword);
  };

  return (
    <Box sx={{ 
      minHeight: '100vh', 
      display: 'flex',
      background: 'linear-gradient(135deg, #0a0a23 0%, #1a1a2e 25%, #16213e 50%, #0f3460 75%, #533483 100%)',
      position: 'relative',
      overflow: 'hidden'
    }}>
      {/* Animated Background Orbs */}
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
          top: '10%',
          left: '10%',
          width: '300px',
          height: '300px',
          background: 'radial-gradient(circle, rgba(59, 130, 246, 0.15) 0%, transparent 70%)',
          borderRadius: '50%',
          animation: 'float 6s ease-in-out infinite',
        },
        '&::after': {
          content: '""',
          position: 'absolute',
          bottom: '10%',
          right: '10%',
          width: '400px',
          height: '400px',
          background: 'radial-gradient(circle, rgba(139, 92, 246, 0.12) 0%, transparent 70%)',
          borderRadius: '50%',
          animation: 'float 8s ease-in-out infinite reverse',
        },
        '@keyframes float': {
          '0%, 100%': {
            transform: 'translateY(0px) scale(1)',
          },
          '50%': {
            transform: 'translateY(-20px) scale(1.05)',
          },
        },
      }} />
      
      {/* Moving Particles */}
      <Box sx={{
        position: 'absolute',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundImage: `
          radial-gradient(2px 2px at 20px 30px, rgba(255,255,255,0.1), transparent),
          radial-gradient(2px 2px at 40px 70px, rgba(255,255,255,0.08), transparent),
          radial-gradient(1px 1px at 90px 40px, rgba(255,255,255,0.1), transparent),
          radial-gradient(1px 1px at 130px 80px, rgba(255,255,255,0.08), transparent),
          radial-gradient(2px 2px at 160px 30px, rgba(255,255,255,0.1), transparent)
        `,
        backgroundRepeat: 'repeat',
        backgroundSize: '200px 100px',
        animation: 'sparkle 20s linear infinite',
        zIndex: 0,
        '@keyframes sparkle': {
          '0%': {
            transform: 'translateY(0)',
          },
          '100%': {
            transform: 'translateY(-100px)',
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
            display: 'flex', 
            width: '100%', 
            maxWidth: 1200,
            minHeight: 650,
            borderRadius: 4,
            overflow: 'hidden',
            boxShadow: '0 40px 80px -20px rgba(0, 0, 0, 0.4)',
            backgroundColor: 'rgba(255, 255, 255, 0.98)',
            backdropFilter: 'blur(20px)',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            animation: 'slideUp 0.8s ease-out',
            '@keyframes slideUp': {
              '0%': {
                transform: 'translateY(50px)',
                opacity: 0,
              },
              '100%': {
                transform: 'translateY(0)',
                opacity: 1,
              },
            },
          }}>
            {/* Left Side - Brand/Info */}
            <Slide direction="right" in={mounted} timeout={1200}>
              <Box sx={{ 
                flex: 1, 
                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%)',
                display: 'flex', 
                flexDirection: 'column', 
                justifyContent: 'center', 
                alignItems: 'center',
                p: 6,
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
                  animation: 'shimmer 3s infinite',
                  '@keyframes shimmer': {
                    '0%': {
                      transform: 'translateX(-100%)',
                    },
                    '100%': {
                      transform: 'translateX(100%)',
                    },
                  },
                },
              }}>
                <Box sx={{
                  position: 'absolute',
                  top: 0,
                  left: 0,
                  right: 0,
                  bottom: 0,
                  backgroundImage: `
                    radial-gradient(circle at 20% 30%, rgba(255, 255, 255, 0.15) 0%, transparent 50%),
                    radial-gradient(circle at 80% 70%, rgba(255, 255, 255, 0.1) 0%, transparent 50%),
                    radial-gradient(circle at 40% 80%, rgba(255, 255, 255, 0.08) 0%, transparent 50%)
                  `,
                }} />
                
                <Box sx={{ textAlign: 'center', zIndex: 1 }}>
                  <Zoom in={mounted} timeout={1500}>
                    <Typography variant="h2" fontWeight="bold" gutterBottom sx={{ 
                      fontSize: { xs: '2.5rem', md: '4rem' },
                      background: 'linear-gradient(135deg, #ffffff 0%, #f0f8ff 100%)',
                      WebkitBackgroundClip: 'text',
                      WebkitTextFillColor: 'transparent',
                      backgroundClip: 'text',
                      mb: 3,
                      textShadow: '0 4px 20px rgba(255,255,255,0.3)',
                      animation: 'glow 2s ease-in-out infinite alternate',
                      '@keyframes glow': {
                        '0%': {
                          filter: 'drop-shadow(0 0 5px rgba(255,255,255,0.5))',
                        },
                        '100%': {
                          filter: 'drop-shadow(0 0 20px rgba(255,255,255,0.8))',
                        },
                      },
                    }}>
                      VisionSeal
                    </Typography>
                  </Zoom>
                  
                  <Fade in={mounted} timeout={2000}>
                    <Typography variant="h5" sx={{ 
                      mb: 4, 
                      fontWeight: 400,
                      opacity: 0.95,
                      lineHeight: 1.4,
                      textShadow: '0 2px 10px rgba(0,0,0,0.2)',
                    }}>
                      Enterprise Tender Management Platform
                    </Typography>
                  </Fade>
                  
                  <Fade in={mounted} timeout={2500}>
                    <Typography variant="body1" sx={{ 
                      opacity: 0.9,
                      lineHeight: 1.6,
                      maxWidth: 400,
                      fontSize: '1.1rem',
                      textShadow: '0 1px 5px rgba(0,0,0,0.1)',
                    }}>
                      Streamline your procurement process with advanced tender discovery, 
                      analysis, and management tools designed for African markets.
                    </Typography>
                  </Fade>
                </Box>
              </Box>
            </Slide>

            {/* Right Side - Login Form */}
            <Slide direction="left" in={mounted} timeout={1400}>
              <Box sx={{ 
                flex: 1, 
                display: 'flex', 
                flexDirection: 'column', 
                justifyContent: 'center',
                p: 6,
                backgroundColor: 'white',
                position: 'relative'
              }}>
                <Box sx={{ maxWidth: 420, mx: 'auto', width: '100%' }}>
                  <Grow in={mounted} timeout={1800}>
                    <Box sx={{ mb: 5, textAlign: 'center' }}>
                      <Typography variant="h4" fontWeight="bold" gutterBottom sx={{ 
                        color: '#1e293b',
                        mb: 2,
                        background: 'linear-gradient(135deg, #1e293b 0%, #3b82f6 100%)',
                        WebkitBackgroundClip: 'text',
                        WebkitTextFillColor: 'transparent',
                        backgroundClip: 'text',
                      }}>
                        Welcome Back
                      </Typography>
                      <Typography variant="body1" sx={{ 
                        color: '#64748b',
                        fontSize: '1.1rem',
                        lineHeight: 1.6
                      }}>
                        Sign in to your account to continue your journey
                      </Typography>
                    </Box>
                  </Grow>

                  <Box component="form" onSubmit={handleSubmit} sx={{ mt: 2 }}>
                    {error && (
                      <Fade in={!!error} timeout={300}>
                        <Alert severity="error" sx={{ mb: 2, borderRadius: 2 }}>
                          {error}
                        </Alert>
                      </Fade>
                    )}
                    
                    {success && (
                      <Fade in={!!success} timeout={300}>
                        <Alert severity="success" sx={{ mb: 2, borderRadius: 2 }}>
                          {success}
                        </Alert>
                      </Fade>
                    )}

                    <Fade in={mounted} timeout={2200}>
                      <TextField
                        fullWidth
                        name="email"
                        label="Email Address"
                        type="email"
                        value={formData.email}
                        onChange={handleChange}
                        onFocus={() => setFocusedField('email')}
                        onBlur={() => setFocusedField(null)}
                        required
                        margin="normal"
                        variant="outlined"
                        InputProps={{
                          startAdornment: (
                            <InputAdornment position="start">
                              <Email sx={{ 
                                color: focusedField === 'email' ? '#3b82f6' : '#64748b',
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
                              borderWidth: '1px',
                            },
                            '&.Mui-focused fieldset': {
                              borderColor: '#3b82f6',
                              borderWidth: '2px',
                              boxShadow: '0 0 0 3px rgba(59, 130, 246, 0.1)',
                            },
                          },
                          '& .MuiInputLabel-root': {
                            color: '#64748b',
                            '&.Mui-focused': {
                              color: '#3b82f6',
                            },
                          },
                          '& .MuiInputBase-input': {
                            color: '#1e293b',
                          },
                        }}
                      />
                    </Fade>

                    <Fade in={mounted} timeout={2400}>
                      <TextField
                        fullWidth
                        name="password"
                        label="Password"
                        type={showPassword ? 'text' : 'password'}
                        value={formData.password}
                        onChange={handleChange}
                        onFocus={() => setFocusedField('password')}
                        onBlur={() => setFocusedField(null)}
                        required
                        margin="normal"
                        variant="outlined"
                        InputProps={{
                          startAdornment: (
                            <InputAdornment position="start">
                              <Lock sx={{ 
                                color: focusedField === 'password' ? '#3b82f6' : '#64748b',
                                transition: 'all 0.3s ease'
                              }} />
                            </InputAdornment>
                          ),
                          endAdornment: (
                            <InputAdornment position="end">
                              <IconButton
                                onClick={togglePasswordVisibility}
                                edge="end"
                                sx={{ 
                                  color: '#64748b',
                                  transition: 'all 0.3s ease',
                                  '&:hover': {
                                    color: '#3b82f6',
                                    transform: 'scale(1.1)',
                                  }
                                }}
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
                            transition: 'all 0.3s ease',
                            '& fieldset': {
                              borderColor: '#e2e8f0',
                              borderWidth: '1px',
                            },
                            '&:hover fieldset': {
                              borderColor: '#cbd5e1',
                              borderWidth: '1px',
                            },
                            '&.Mui-focused fieldset': {
                              borderColor: '#3b82f6',
                              borderWidth: '2px',
                              boxShadow: '0 0 0 3px rgba(59, 130, 246, 0.1)',
                            },
                          },
                          '& .MuiInputLabel-root': {
                            color: '#64748b',
                            '&.Mui-focused': {
                              color: '#3b82f6',
                            },
                          },
                          '& .MuiInputBase-input': {
                            color: '#1e293b',
                          },
                        }}
                      />
                    </Fade>

                    <Zoom in={mounted} timeout={2600}>
                      <Button
                        type="submit"
                        fullWidth
                        variant="contained"
                        size="large"
                        disabled={isLoading}
                        endIcon={!isLoading && <KeyboardArrowRight />}
                        sx={{
                          mt: 4,
                          py: 1.8,
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
                            <span>Signing In...</span>
                          </Box>
                        ) : (
                          'Sign In'
                        )}
                      </Button>
                    </Zoom>

                    <Fade in={mounted} timeout={2800}>
                      <Box sx={{ mt: 4, textAlign: 'center' }}>
                        <Link
                          component="button"
                          type="button"
                          variant="body2"
                          onClick={() => navigate('/forgot-password')}
                          sx={{ 
                            color: '#64748b',
                            textDecoration: 'none',
                            transition: 'all 0.3s ease',
                            '&:hover': {
                              color: '#3b82f6',
                              textDecoration: 'underline',
                              transform: 'translateY(-1px)',
                            }
                          }}
                        >
                          Forgot your password?
                        </Link>
                      </Box>
                    </Fade>

                    <Fade in={mounted} timeout={3000}>
                      <Divider sx={{ 
                        my: 4, 
                        backgroundColor: '#e2e8f0',
                        '&::before, &::after': {
                          borderColor: '#e2e8f0',
                        }
                      }} />
                    </Fade>

                    <Fade in={mounted} timeout={3200}>
                      <Box sx={{ textAlign: 'center' }}>
                        <Typography variant="body2" sx={{ color: '#64748b' }}>
                          Don't have an account?{' '}
                          <Link
                            component="button"
                            type="button"
                            variant="body2"
                            onClick={() => navigate('/register')}
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
                            Sign Up Here
                          </Link>
                        </Typography>
                      </Box>
                    </Fade>
                  </Box>
                </Box>
              </Box>
            </Slide>
          </Box>
        </Fade>
      </Container>
    </Box>
  );
};

export default Login;