# VisionSeal Frontend

A high-end corporate React frontend for the VisionSeal tender management platform.

## 🚀 Features

- **Modern Corporate Design**: Clean, professional interface with Material-UI
- **Responsive Layout**: Mobile-first design that works on all devices
- **Real-time Data**: Live tender statistics and updates
- **Advanced Search**: Powerful filtering and search capabilities
- **Interactive Charts**: Data visualization with Recharts
- **Type Safety**: Full TypeScript support
- **Performance**: Optimized with React Query and lazy loading

## 🛠️ Tech Stack

- **React 18** - Modern React with hooks
- **TypeScript** - Type-safe development
- **Material-UI v5** - Corporate design system
- **React Query** - Server state management
- **React Router** - Client-side routing
- **Recharts** - Data visualization
- **Vite** - Fast development and build tool
- **Emotion** - CSS-in-JS styling

## 📦 Installation

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

## 🏗️ Project Structure

```
src/
├── components/          # Reusable UI components
│   ├── Layout/         # Layout components (Header, Sidebar)
│   └── Dashboard/      # Dashboard-specific components
├── pages/              # Page components
├── theme/              # Corporate design system
│   ├── colors.ts       # Color palette
│   ├── typography.ts   # Typography system
│   ├── spacing.ts      # Spacing system
│   └── theme.ts        # MUI theme configuration
├── types/              # TypeScript type definitions
├── utils/              # Utility functions and API client
└── assets/             # Static assets
```

## 🎨 Design System

### Colors
- **Primary**: Blue gradient (#0ea5e9)
- **Secondary**: Gold accent (#f59e0b)
- **Neutral**: Gray scale
- **Status**: Success, warning, error colors

### Typography
- **Primary Font**: Inter (modern, professional)
- **Font Weights**: 300-800
- **Scale**: Responsive typography scale

### Components
- **Cards**: Elevated with subtle shadows
- **Buttons**: Rounded corners, hover effects
- **Forms**: Clean inputs with focus states
- **Navigation**: Intuitive sidebar and header

## 🔧 Development

### Environment Variables
```bash
VITE_API_URL=http://localhost:8080
VITE_APP_NAME=VisionSeal
VITE_APP_VERSION=1.0.0
```

### Scripts
- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint
- `npm run type-check` - Run TypeScript checks

### Code Quality
- ESLint for code linting
- TypeScript for type safety
- Prettier for code formatting
- Pre-commit hooks for quality assurance

## 📱 Features Overview

### Dashboard
- Real-time tender statistics
- Interactive charts and graphs
- Recent tenders feed
- Quick action buttons

### Tender Management
- Advanced filtering and search
- Sortable data tables
- Export functionality
- Detailed tender views

### Analytics
- Comprehensive reporting
- Data visualization
- Performance metrics
- Trend analysis

## 🔗 API Integration

The frontend connects to the VisionSeal backend API:

- **Base URL**: `http://localhost:8080/api/v1`
- **Authentication**: JWT tokens
- **Error Handling**: Comprehensive error boundaries
- **Caching**: React Query for optimal performance

## 📊 Performance

- **Bundle Size**: Optimized with code splitting
- **Loading**: Skeleton screens and progressive loading
- **Caching**: Intelligent data caching
- **Responsive**: Mobile-first approach

## 🚀 Deployment

```bash
# Build for production
npm run build

# Deploy to static hosting
# Built files will be in the `dist/` directory
```

## 🤝 Contributing

1. Follow the established code style
2. Add TypeScript types for new features
3. Write tests for new components
4. Update documentation

## 📄 License

Copyright © 2025 VisionSeal. All rights reserved.