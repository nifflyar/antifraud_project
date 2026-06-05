/**
 * Tailwind Configuration - Enterprise Light Theme
 * Professional design system for Antifrode platform
 */

module.exports = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        // Primary - Sky Blue (trustworthy, professional)
        primary: {
          50: '#f0f7ff',
          100: '#e0f2fe',
          200: '#bae6fd',
          300: '#7dd3fc',
          400: '#38bdf8',
          500: '#0ea5e9',
          600: '#0284c7',
          700: '#0369a1',
          800: '#075985',
          900: '#0c3d66',
        },

        // Risk colors - semantic
        risk: {
          critical: {
            50: '#fef2f2',
            100: '#fee2e2',
            200: '#fecaca',
            400: '#f87171',
            500: '#ef4444',
            600: '#dc2626',
            700: '#b91c1c',
          },
          high: {
            50: '#fff7ed',
            100: '#fed7aa',
            200: '#fdba74',
            400: '#fb923c',
            500: '#f97316',
            600: '#ea580c',
            700: '#c2410c',
          },
          medium: {
            50: '#fefce8',
            100: '#fef3c7',
            200: '#fde68a',
            400: '#facc15',
            500: '#eab308',
            600: '#ca8a04',
            700: '#a16207',
          },
          low: {
            50: '#f0fdf4',
            100: '#dcfce7',
            200: '#bbf7d0',
            400: '#4ade80',
            500: '#22c55e',
            600: '#16a34a',
            700: '#15803d',
          }
        },

        // Extended neutral palette
        neutral: {
          0: '#ffffff',
          50: '#fafafa',
          100: '#f3f4f6',
          150: '#eff0f2',
          200: '#e5e7eb',
          300: '#d1d5db',
          400: '#9ca3af',
          500: '#6b7280',
          600: '#4b5563',
          700: '#374151',
          800: '#1f2937',
          900: '#111827',
        },

        // Accent colors
        success: '#10b981',
        warning: '#f59e0b',
        info: '#3b82f6',
        error: '#ef4444',
      },

      backgroundImage: {
        'gradient-light': 'linear-gradient(135deg, #f0f7ff 0%, #f9fafb 100%)',
        'gradient-hero': 'linear-gradient(135deg, #f0f7ff 0%, #f3f4f6 50%, #fef3c7 100%)',
        'gradient-card': 'linear-gradient(135deg, #ffffff 0%, #f9fafb 100%)',
      },

      boxShadow: {
        'card': '0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1)',
        'card-lg': '0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)',
        'card-xl': '0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1)',
        'inner-light': 'inset 0 1px 2px 0 rgb(0 0 0 / 0.05)',
      },

      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['Fira Code', 'monospace'],
      },

      fontSize: {
        xs: ['0.75rem', { lineHeight: '1rem' }],
        sm: ['0.875rem', { lineHeight: '1.25rem' }],
        base: ['1rem', { lineHeight: '1.5rem' }],
        lg: ['1.125rem', { lineHeight: '1.75rem' }],
        xl: ['1.25rem', { lineHeight: '1.75rem' }],
        '2xl': ['1.5rem', { lineHeight: '2rem' }],
        '3xl': ['1.875rem', { lineHeight: '2.25rem' }],
        '4xl': ['2.25rem', { lineHeight: '2.5rem' }],
      },

      spacing: {
        '0.5': '0.125rem',
        '1.5': '0.375rem',
        '2.5': '0.625rem',
        '3.5': '0.875rem',
      },

      borderRadius: {
        'xs': '0.25rem',
        'sm': '0.375rem',
        'base': '0.5rem',
        'md': '0.75rem',
        'lg': '1rem',
        'xl': '1.25rem',
        '2xl': '1.5rem',
      },

      animation: {
        'fade-in': 'fadeIn 0.3s ease-in-out',
        'slide-in': 'slideIn 0.3s ease-out',
        'pulse-light': 'pulseLight 3s ease-in-out infinite',
      },

      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideIn: {
          '0%': { transform: 'translateY(-10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        pulseLight: {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.8' },
        },
      },

      transitionTimingFunction: {
        smooth: 'cubic-bezier(0.4, 0, 0.2, 1)',
      },

      backdropBlur: {
        xs: '2px',
      },
    },
  },

  plugins: [
    // Custom component styles
    function ({ addComponents, theme }) {
      addComponents({
        // Cards
        '.card': {
          '@apply bg-white border border-neutral-200 rounded-lg shadow-card transition-all':
            {},
        },
        '.card:hover': {
          '@apply shadow-card-lg': {},
        },

        // Buttons
        '.btn': {
          '@apply px-4 py-2 rounded-lg font-semibold text-sm transition-all duration-200':
            {},
        },
        '.btn-primary': {
          '@apply bg-primary-500 text-white hover:bg-primary-600 active:bg-primary-700':
            {},
        },
        '.btn-secondary': {
          '@apply border border-neutral-300 text-neutral-700 hover:bg-neutral-50 active:bg-neutral-100':
            {},
        },
        '.btn-danger': {
          '@apply bg-risk-critical-500 text-white hover:bg-risk-critical-600 active:bg-risk-critical-700':
            {},
        },

        // Input fields
        '.input': {
          '@apply px-3 py-2 border border-neutral-300 rounded-lg bg-white text-neutral-900 placeholder-neutral-400 transition-all':
            {},
        },
        '.input:hover': {
          '@apply border-neutral-400': {},
        },
        '.input:focus': {
          '@apply outline-none ring-2 ring-primary-500 border-transparent': {},
        },

        // Badges
        '.badge': {
          '@apply inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold':
            {},
        },
        '.badge-primary': {
          '@apply bg-primary-100 text-primary-700': {},
        },
        '.badge-success': {
          '@apply bg-green-100 text-green-700': {},
        },
        '.badge-warning': {
          '@apply bg-yellow-100 text-yellow-700': {},
        },
        '.badge-danger': {
          '@apply bg-red-100 text-red-700': {},
        },

        // Tables
        '.table-header': {
          '@apply bg-neutral-50 border-b border-neutral-200': {},
        },
        '.table-row': {
          '@apply border-b border-neutral-100 hover:bg-neutral-50 transition-colors':
            {},
        },

        // Text utilities
        '.text-caption': {
          '@apply text-xs font-semibold uppercase tracking-wider text-neutral-600': {},
        },
        '.text-body-large': {
          '@apply text-base text-neutral-700 leading-relaxed': {},
        },
        '.text-body-medium': {
          '@apply text-sm text-neutral-600 leading-relaxed': {},
        },
      });
    },
  ],
};
