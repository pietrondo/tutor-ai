/**
 * Application Configuration
 * Centralized configuration for the Tutor AI frontend
 */

// Environment configuration
export const config = {
  // API Configuration
  api: {
    baseUrl: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
    timeout: 30000, // 30 seconds
    retryAttempts: 3,
    retryDelay: 1000, // 1 second
  },

  // Application Info
  app: {
    name: 'Tutor AI',
    version: process.env.npm_package_version || '1.0.0',
    description: 'Sistema di Apprendimento Intelligente',
    author: 'Tutor AI Team',
  },

  // Feature Flags (Local Setup - Auth Disabled)
  features: {
    auth: false, // Disabled for local setup
    analytics: process.env.NEXT_PUBLIC_ANALYTICS_ENABLED === 'true',
    social: false, // Disabled for local setup
    export: process.env.NEXT_PUBLIC_EXPORT_FEATURES === 'true',
    collaboration: false, // Disabled for local setup
    darkMode: process.env.NEXT_PUBLIC_DARK_MODE !== 'false',
    notifications: process.env.NEXT_PUBLIC_NOTIFICATIONS !== 'false',
  },

  // UI Configuration
  ui: {
    theme: {
      defaultTheme: (process.env.NEXT_PUBLIC_DEFAULT_THEME as 'light' | 'dark' | 'system') || 'system',
      primaryColor: '#3B82F6', // blue-600
      accentColor: '#10B981', // emerald-500
      grayColors: {
        50: '#F9FAFB',
        100: '#F3F4F6',
        200: '#E5E7EB',
        300: '#D1D5DB',
        400: '#9CA3AF',
        500: '#6B7280',
        600: '#4B5563',
        700: '#374151',
        800: '#1F2937',
        900: '#111827',
      },
    },
    layout: {
      sidebarWidth: 256,
      sidebarCollapsedWidth: 80,
      headerHeight: 64,
      footerHeight: 48,
      contentPadding: 24,
      borderRadius: 8,
      shadows: {
        sm: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
        md: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
        lg: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
      },
    },
    animations: {
      duration: {
        fast: 150,
        normal: 300,
        slow: 500,
      },
      easing: {
        easeIn: 'cubic-bezier(0.4, 0, 1, 1)',
        easeOut: 'cubic-bezier(0, 0, 0.2, 1)',
        easeInOut: 'cubic-bezier(0.4, 0, 0.2, 1)',
      },
    },
  },

  // Pagination
  pagination: {
    defaultPageSize: 20,
    pageSizeOptions: [10, 20, 50, 100],
    maxPages: 100,
  },

  // File Upload
  upload: {
    maxFileSize: 50 * 1024 * 1024, // 50MB
    allowedFileTypes: ['.pdf', '.docx', '.doc', '.pptx', '.ppt', '.txt'],
    maxFilesPerUpload: 10,
    chunkSize: 1024 * 1024, // 1MB chunks
    concurrentUploads: 3,
  },

  // Cache Configuration
  cache: {
    defaultTTL: 5 * 60 * 1000, // 5 minutes
    userTTL: 30 * 60 * 1000, // 30 minutes
    courseTTL: 10 * 60 * 1000, // 10 minutes
    searchTTL: 2 * 60 * 1000, // 2 minutes
  },

  // Rate Limiting (client-side)
  rateLimit: {
    search: {
      maxRequests: 10,
      windowMs: 60 * 1000, // 1 minute
    },
    chat: {
      maxRequests: 30,
      windowMs: 60 * 1000, // 1 minute
    },
    upload: {
      maxRequests: 5,
      windowMs: 60 * 1000, // 1 minute
    },
  },

  // Study Session Settings
  study: {
    defaultSessionDuration: 25 * 60, // 25 minutes (Pomodoro)
    shortBreakDuration: 5 * 60, // 5 minutes
    longBreakDuration: 15 * 60, // 15 minutes
    sessionsUntilLongBreak: 4,
    minSessionDuration: 5 * 60, // 5 minutes
    maxSessionDuration: 120 * 60, // 2 hours
  },

  // Notification Settings
  notifications: {
    enabled: process.env.NEXT_PUBLIC_NOTIFICATIONS !== 'false',
    types: {
      studyReminders: true,
      achievements: true,
      courseUpdates: true,
      systemMaintenance: true,
      newFeatures: false,
    },
    channels: {
      inApp: true,
      email: process.env.NEXT_PUBLIC_EMAIL_NOTIFICATIONS === 'true',
      push: process.env.NEXT_PUBLIC_PUSH_NOTIFICATIONS === 'true',
    },
  },

  // Analytics and Tracking
  analytics: {
    enabled: process.env.NEXT_PUBLIC_ANALYTICS_ENABLED === 'true',
    trackingId: process.env.NEXT_PUBLIC_GA_TRACKING_ID,
    apiEndpoint: process.env.NEXT_PUBLIC_ANALYTICS_ENDPOINT,
    batchSize: 10,
    flushInterval: 30 * 1000, // 30 seconds
  },

  // Development/Debug Settings
  debug: {
    enabled: process.env.NODE_ENV === 'development',
    logLevel: process.env.NEXT_PUBLIC_LOG_LEVEL || 'info',
    showPerformanceMetrics: process.env.NEXT_PUBLIC_SHOW_PERFORMANCE_METRICS === 'true',
    enableReactDevTools: process.env.NEXT_PUBLIC_ENABLE_REACT_DEVTOOLS === 'true',
  },

  // Security Settings (Local Setup - Relaxed)
  security: {
    enableCSRF: false, // Disabled for local setup
    sessionTimeout: 24 * 60 * 60 * 1000, // 24 hours
    maxLoginAttempts: 999, // Disabled for local setup
    lockoutDuration: 0, // Disabled for local setup
    passwordMinLength: 1, // Minimal for local setup
    requireEmailVerification: false, // Disabled for local setup
  },

  // External Services
  services: {
    sentry: {
      dsn: process.env.NEXT_PUBLIC_SENTRY_DSN,
      environment: process.env.NODE_ENV,
      release: process.env.npm_package_version,
    },
    support: {
      email: process.env.NEXT_PUBLIC_SUPPORT_EMAIL || 'support@tutorai.com',
      chat: process.env.NEXT_PUBLIC_SUPPORT_CHAT_URL,
      docs: process.env.NEXT_PUBLIC_DOCS_URL || 'https://docs.tutorai.com',
    },
  },
}

// Utility functions for working with config
export const isFeatureEnabled = (feature: keyof typeof config.features): boolean => {
  return config.features[feature]
}

export const getApiUrl = (endpoint: string): string => {
  return `${config.api.baseUrl}${endpoint}`
}

export const isDevelopment = (): boolean => {
  return config.debug.enabled
}

export const isProduction = (): boolean => {
  return process.env.NODE_ENV === 'production'
}

export const getThemeConfig = () => {
  return config.ui.theme
}

export const getUploadConfig = () => {
  return config.upload
}

export const validateConfig = (): string[] => {
  const errors: string[] = []

  // Validate required environment variables
  if (!config.api.baseUrl) {
    errors.push('API base URL is required')
  }

  if (config.features.auth && !process.env.NEXT_PUBLIC_JWT_SECRET) {
    errors.push('JWT secret is required when auth is enabled')
  }

  // Validate feature dependencies
  if (config.features.notifications && !process.env.NEXT_PUBLIC_NOTIFICATIONS_SERVICE) {
    console.warn('Notification service URL not provided, notifications will be disabled')
  }

  if (config.analytics.enabled && !config.analytics.trackingId) {
    console.warn('Analytics tracking ID not provided, analytics will be disabled')
  }

  return errors
}

// Export configuration for use in components
export default config