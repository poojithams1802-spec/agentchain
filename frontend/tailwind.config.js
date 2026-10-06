/** @type {import('tailwindcss').Config} */
// Colors are CSS variables (see src/index.css) so the whole app switches between light and dark.
const v = (name) => `rgb(var(--${name}) / <alpha-value>)`

export default {
  darkMode: 'class',
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        base: {
          950: v('base-950'),
          900: v('base-900'),
          800: v('base-800'),
          700: v('base-700'),
          600: v('base-600'),
          500: v('base-500'),
          400: v('base-400'),
          300: v('base-300'),
          200: v('base-200'),
          100: v('base-100'),
        },
        signal: {
          DEFAULT: v('signal'),
          dim: v('signal-dim'),
          bright: v('signal-bright'),
        },
        info: v('info'),
        sev: {
          critical: v('sev-critical'),
          high: v('sev-high'),
          medium: v('sev-medium'),
          low: v('sev-low'),
        },
      },
      borderRadius: {
        DEFAULT: '0.5rem',
        md: '0.625rem',
        lg: '1rem',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['"IBM Plex Mono"', 'ui-monospace', 'monospace'],
      },
    },
  },
  plugins: [],
}
