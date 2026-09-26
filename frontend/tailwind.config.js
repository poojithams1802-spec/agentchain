/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        base: {
          950: '#0B0D10',
          900: '#0F1115',
          800: '#14171C',
          700: '#1B1F26',
          600: '#262B33',
          500: '#3A4048',
          400: '#5C636D',
          300: '#8A909A',
          200: '#B8BDC5',
          100: '#E4E6EA',
        },
        signal: {
          DEFAULT: '#E8A33D',
          dim: '#8A6526',
          bright: '#F5B85C',
        },
        info: '#5B8DEF',
        sev: {
          critical: '#E5484D',
          high: '#E8734D',
          medium: '#E8A33D',
          low: '#5B9E6F',
        },
      },
      fontFamily: {
        sans: ['"IBM Plex Sans"', 'system-ui', 'sans-serif'],
        mono: ['"IBM Plex Mono"', 'ui-monospace', 'monospace'],
      },
    },
  },
  plugins: [],
}
