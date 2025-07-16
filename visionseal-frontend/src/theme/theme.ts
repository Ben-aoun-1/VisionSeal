import { createTheme } from '@mui/material/styles'
import { colors } from './colors'
import { typography } from './typography'
import { spacing } from './spacing'

declare module '@mui/material/styles' {
  interface Palette {
    tertiary: Palette['primary']
  }
  
  interface PaletteOptions {
    tertiary?: PaletteOptions['primary']
  }
}

// VisionSeal Corporate Theme
export const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: colors.primary[500],
      light: colors.primary[400],
      dark: colors.primary[600],
      contrastText: colors.text.inverse,
    },
    secondary: {
      main: colors.secondary[500],
      light: colors.secondary[400],
      dark: colors.secondary[600],
      contrastText: colors.text.inverse,
    },
    tertiary: {
      main: colors.corporate.charcoal,
      light: colors.neutral[600],
      dark: colors.neutral[800],
      contrastText: colors.text.inverse,
    },
    error: {
      main: colors.error[500],
      light: colors.error[400],
      dark: colors.error[600],
      contrastText: colors.text.inverse,
    },
    warning: {
      main: colors.warning[500],
      light: colors.warning[400],
      dark: colors.warning[600],
      contrastText: colors.text.inverse,
    },
    info: {
      main: colors.primary[500],
      light: colors.primary[400],
      dark: colors.primary[600],
      contrastText: colors.text.inverse,
    },
    success: {
      main: colors.success[500],
      light: colors.success[400],
      dark: colors.success[600],
      contrastText: colors.text.inverse,
    },
    grey: {
      50: colors.neutral[50],
      100: colors.neutral[100],
      200: colors.neutral[200],
      300: colors.neutral[300],
      400: colors.neutral[400],
      500: colors.neutral[500],
      600: colors.neutral[600],
      700: colors.neutral[700],
      800: colors.neutral[800],
      900: colors.neutral[900],
    },
    text: {
      primary: colors.text.primary,
      secondary: colors.text.secondary,
      disabled: colors.text.disabled,
    },
    background: {
      default: colors.background.secondary,
      paper: colors.background.paper,
    },
    divider: colors.border.light,
  },
  
  typography: {
    fontFamily: typography.fontFamily.primary,
    h1: {
      fontSize: typography.fontSize['4xl'],
      fontWeight: typography.fontWeight.bold,
      lineHeight: typography.lineHeight.tight,
      letterSpacing: typography.letterSpacing.tight,
      color: colors.text.primary,
    },
    h2: {
      fontSize: typography.fontSize['3xl'],
      fontWeight: typography.fontWeight.semiBold,
      lineHeight: typography.lineHeight.snug,
      letterSpacing: typography.letterSpacing.tight,
      color: colors.text.primary,
    },
    h3: {
      fontSize: typography.fontSize['2xl'],
      fontWeight: typography.fontWeight.semiBold,
      lineHeight: typography.lineHeight.normal,
      color: colors.text.primary,
    },
    h4: {
      fontSize: typography.fontSize.xl,
      fontWeight: typography.fontWeight.semiBold,
      lineHeight: typography.lineHeight.normal,
      color: colors.text.primary,
    },
    h5: {
      fontSize: typography.fontSize.lg,
      fontWeight: typography.fontWeight.semiBold,
      lineHeight: typography.lineHeight.normal,
      color: colors.text.primary,
    },
    h6: {
      fontSize: typography.fontSize.base,
      fontWeight: typography.fontWeight.semiBold,
      lineHeight: typography.lineHeight.normal,
      color: colors.text.primary,
    },
    subtitle1: {
      fontSize: typography.fontSize.lg,
      fontWeight: typography.fontWeight.medium,
      lineHeight: typography.lineHeight.normal,
      color: colors.text.secondary,
    },
    subtitle2: {
      fontSize: typography.fontSize.base,
      fontWeight: typography.fontWeight.medium,
      lineHeight: typography.lineHeight.normal,
      color: colors.text.secondary,
    },
    body1: {
      fontSize: typography.fontSize.base,
      fontWeight: typography.fontWeight.regular,
      lineHeight: typography.lineHeight.relaxed,
      color: colors.text.primary,
    },
    body2: {
      fontSize: typography.fontSize.sm,
      fontWeight: typography.fontWeight.regular,
      lineHeight: typography.lineHeight.normal,
      color: colors.text.secondary,
    },
    caption: {
      fontSize: typography.fontSize.xs,
      fontWeight: typography.fontWeight.regular,
      lineHeight: typography.lineHeight.normal,
      color: colors.text.tertiary,
    },
    overline: {
      fontSize: typography.fontSize.xs,
      fontWeight: typography.fontWeight.semiBold,
      lineHeight: typography.lineHeight.normal,
      letterSpacing: typography.letterSpacing.wider,
      textTransform: 'uppercase',
      color: colors.text.tertiary,
    },
    button: {
      fontSize: typography.fontSize.sm,
      fontWeight: typography.fontWeight.semiBold,
      lineHeight: typography.lineHeight.normal,
      letterSpacing: typography.letterSpacing.wide,
      textTransform: 'none',
    },
  },
  
  spacing: (factor: number) => `${factor * 0.25}rem`,
  
  shape: {
    borderRadius: 8,
  },
  
  shadows: [
    'none',
    '0px 1px 3px rgba(0, 0, 0, 0.1), 0px 1px 2px rgba(0, 0, 0, 0.06)',
    '0px 4px 6px rgba(0, 0, 0, 0.1), 0px 2px 4px rgba(0, 0, 0, 0.06)',
    '0px 10px 15px rgba(0, 0, 0, 0.1), 0px 4px 6px rgba(0, 0, 0, 0.05)',
    '0px 20px 25px rgba(0, 0, 0, 0.1), 0px 10px 10px rgba(0, 0, 0, 0.04)',
    '0px 25px 50px rgba(0, 0, 0, 0.25)',
    '0px 2px 4px rgba(0, 0, 0, 0.06), 0px 8px 16px rgba(0, 0, 0, 0.1)',
    '0px 4px 8px rgba(0, 0, 0, 0.1), 0px 16px 32px rgba(0, 0, 0, 0.1)',
    '0px 8px 16px rgba(0, 0, 0, 0.1), 0px 32px 64px rgba(0, 0, 0, 0.1)',
    '0px 16px 32px rgba(0, 0, 0, 0.1), 0px 64px 128px rgba(0, 0, 0, 0.1)',
    '0px 32px 64px rgba(0, 0, 0, 0.15)',
    '0px 40px 80px rgba(0, 0, 0, 0.2)',
    '0px 48px 96px rgba(0, 0, 0, 0.25)',
    '0px 56px 112px rgba(0, 0, 0, 0.3)',
    '0px 64px 128px rgba(0, 0, 0, 0.35)',
    '0px 72px 144px rgba(0, 0, 0, 0.4)',
    '0px 80px 160px rgba(0, 0, 0, 0.45)',
    '0px 88px 176px rgba(0, 0, 0, 0.5)',
    '0px 96px 192px rgba(0, 0, 0, 0.55)',
    '0px 104px 208px rgba(0, 0, 0, 0.6)',
    '0px 112px 224px rgba(0, 0, 0, 0.65)',
    '0px 120px 240px rgba(0, 0, 0, 0.7)',
    '0px 128px 256px rgba(0, 0, 0, 0.75)',
    '0px 136px 272px rgba(0, 0, 0, 0.8)',
    '0px 144px 288px rgba(0, 0, 0, 0.85)',
  ],
  
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          textTransform: 'none',
          fontSize: typography.fontSize.sm,
          fontWeight: typography.fontWeight.semiBold,
          letterSpacing: typography.letterSpacing.wide,
          padding: `${spacing.components.button.paddingY} ${spacing.components.button.paddingX}`,
          boxShadow: 'none',
          '&:hover': {
            boxShadow: '0px 4px 8px rgba(0, 0, 0, 0.1)',
          },
        },
        sizeLarge: {
          padding: spacing.components.button.paddingLarge,
          fontSize: typography.fontSize.base,
        },
        sizeSmall: {
          padding: spacing.components.button.paddingSmall,
          fontSize: typography.fontSize.xs,
        },
      },
    },
    
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 12,
          boxShadow: '0px 4px 6px rgba(0, 0, 0, 0.1), 0px 2px 4px rgba(0, 0, 0, 0.06)',
          border: `1px solid ${colors.border.light}`,
        },
      },
    },
    
    MuiCardContent: {
      styleOverrides: {
        root: {
          padding: spacing.components.card.padding,
          '&:last-child': {
            paddingBottom: spacing.components.card.padding,
          },
        },
      },
    },
    
    MuiTextField: {
      styleOverrides: {
        root: {
          '& .MuiOutlinedInput-root': {
            borderRadius: 8,
            '& fieldset': {
              borderColor: colors.border.light,
            },
            '&:hover fieldset': {
              borderColor: colors.border.medium,
            },
            '&.Mui-focused fieldset': {
              borderColor: colors.primary[500],
            },
          },
        },
      },
    },
    
    MuiAppBar: {
      styleOverrides: {
        root: {
          backgroundColor: colors.background.paper,
          boxShadow: '0px 1px 3px rgba(0, 0, 0, 0.1), 0px 1px 2px rgba(0, 0, 0, 0.06)',
          borderBottom: `1px solid ${colors.border.light}`,
        },
      },
    },
    
    MuiDrawer: {
      styleOverrides: {
        paper: {
          backgroundColor: colors.background.paper,
          borderRight: `1px solid ${colors.border.light}`,
        },
      },
    },
    
    MuiChip: {
      styleOverrides: {
        root: {
          borderRadius: 6,
          fontWeight: typography.fontWeight.medium,
          fontSize: typography.fontSize.xs,
        },
      },
    },
    
    MuiTableHead: {
      styleOverrides: {
        root: {
          backgroundColor: colors.background.tertiary,
          '& .MuiTableCell-head': {
            fontWeight: typography.fontWeight.semiBold,
            fontSize: typography.fontSize.xs,
            letterSpacing: typography.letterSpacing.wide,
            textTransform: 'uppercase',
            color: colors.text.secondary,
          },
        },
      },
    },
    
    MuiTableRow: {
      styleOverrides: {
        root: {
          '&:hover': {
            backgroundColor: colors.background.tertiary,
          },
        },
      },
    },
  },
})

export default theme