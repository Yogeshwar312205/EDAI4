/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: [
    './index.html',
    './src/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        // Dark Industrial Theme
        industrial: {
          950: '#0a0e14',
          900: '#0f1419',
          800: '#1a1f29',
          700: '#252b38',
          600: '#3d4556',
          500: '#5c6370',
          400: '#828997',
          300: '#abb2bf',
        },
        accent: {
          blue: '#61afef',
          cyan: '#56b6c2',
          green: '#98c379',
          yellow: '#e5c07b',
          orange: '#d19a66',
          red: '#e06c75',
          purple: '#c678dd',
        },
      },
      boxShadow: {
        'glow-blue': '0 0 20px rgba(97, 175, 239, 0.3)',
        'glow-cyan': '0 0 20px rgba(86, 182, 194, 0.3)',
      },
      keyframes: {
        'slide-in': {
          '0%': { transform: 'translateX(100%)', opacity: '0' },
          '100%': { transform: 'translateX(0)', opacity: '1' },
        },
      },
      animation: {
        'slide-in': 'slide-in 0.3s ease-out',
      },
    },
  },
  plugins: [],
}
