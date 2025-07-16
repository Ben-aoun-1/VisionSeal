// VisionSeal Corporate Typography System
export const typography = {
  // Font families
  fontFamily: {
    primary: '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
    secondary: '"Roboto", -apple-system, BlinkMacSystemFont, "Segoe UI", "Helvetica Neue", Arial, sans-serif',
    mono: '"JetBrains Mono", "Fira Code", Monaco, Consolas, "Liberation Mono", "Courier New", monospace',
  },
  
  // Font weights
  fontWeight: {
    light: 300,
    regular: 400,
    medium: 500,
    semiBold: 600,
    bold: 700,
    extraBold: 800,
  },
  
  // Font sizes (rem units)
  fontSize: {
    xs: '0.75rem',    // 12px
    sm: '0.875rem',   // 14px
    base: '1rem',     // 16px
    lg: '1.125rem',   // 18px
    xl: '1.25rem',    // 20px
    '2xl': '1.5rem',  // 24px
    '3xl': '1.875rem', // 30px
    '4xl': '2.25rem', // 36px
    '5xl': '3rem',    // 48px
    '6xl': '3.75rem', // 60px
    '7xl': '4.5rem',  // 72px
  },
  
  // Line heights
  lineHeight: {
    tight: 1.25,
    snug: 1.375,
    normal: 1.5,
    relaxed: 1.625,
    loose: 2,
  },
  
  // Letter spacing
  letterSpacing: {
    tighter: '-0.05em',
    tight: '-0.025em',
    normal: '0em',
    wide: '0.025em',
    wider: '0.05em',
    widest: '0.1em',
  },
  
  // Text styles for different components
  styles: {
    // Hero section
    hero: {
      fontSize: '3.75rem',
      fontWeight: 700,
      lineHeight: 1.1,
      letterSpacing: '-0.025em',
    },
    
    // Main headings
    h1: {
      fontSize: '2.25rem',
      fontWeight: 700,
      lineHeight: 1.2,
      letterSpacing: '-0.025em',
    },
    
    h2: {
      fontSize: '1.875rem',
      fontWeight: 600,
      lineHeight: 1.3,
      letterSpacing: '-0.025em',
    },
    
    h3: {
      fontSize: '1.5rem',
      fontWeight: 600,
      lineHeight: 1.4,
    },
    
    h4: {
      fontSize: '1.25rem',
      fontWeight: 600,
      lineHeight: 1.4,
    },
    
    h5: {
      fontSize: '1.125rem',
      fontWeight: 600,
      lineHeight: 1.5,
    },
    
    h6: {
      fontSize: '1rem',
      fontWeight: 600,
      lineHeight: 1.5,
    },
    
    // Body text
    body1: {
      fontSize: '1rem',
      fontWeight: 400,
      lineHeight: 1.5,
    },
    
    body2: {
      fontSize: '0.875rem',
      fontWeight: 400,
      lineHeight: 1.5,
    },
    
    // Special text styles
    subtitle1: {
      fontSize: '1.125rem',
      fontWeight: 500,
      lineHeight: 1.5,
    },
    
    subtitle2: {
      fontSize: '1rem',
      fontWeight: 500,
      lineHeight: 1.5,
    },
    
    caption: {
      fontSize: '0.75rem',
      fontWeight: 400,
      lineHeight: 1.4,
    },
    
    overline: {
      fontSize: '0.75rem',
      fontWeight: 600,
      lineHeight: 1.4,
      letterSpacing: '0.1em',
      textTransform: 'uppercase',
    },
    
    // Button text
    button: {
      fontSize: '0.875rem',
      fontWeight: 600,
      lineHeight: 1.4,
      letterSpacing: '0.025em',
    },
    
    // Corporate specific styles
    corporate: {
      brandTitle: {
        fontSize: '2.25rem',
        fontWeight: 700,
        lineHeight: 1.2,
        letterSpacing: '-0.025em',
      },
      
      statValue: {
        fontSize: '2rem',
        fontWeight: 700,
        lineHeight: 1.2,
      },
      
      statLabel: {
        fontSize: '0.875rem',
        fontWeight: 500,
        lineHeight: 1.4,
        letterSpacing: '0.025em',
        textTransform: 'uppercase',
      },
      
      cardTitle: {
        fontSize: '1.125rem',
        fontWeight: 600,
        lineHeight: 1.4,
      },
      
      tableHeader: {
        fontSize: '0.875rem',
        fontWeight: 600,
        lineHeight: 1.4,
        letterSpacing: '0.025em',
      },
      
      label: {
        fontSize: '0.75rem',
        fontWeight: 500,
        lineHeight: 1.4,
        letterSpacing: '0.05em',
        textTransform: 'uppercase',
      },
    },
  },
} as const

export type TypographySystem = typeof typography