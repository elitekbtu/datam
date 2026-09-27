/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: { ink: '#111111', muted: '#6c6c70', line: '#e9e9eb', mist: '#f5f5f6' },
      fontFamily: { sans: ['Arial', 'Helvetica Neue', 'sans-serif'], display: ['Georgia', 'Times New Roman', 'serif'] },
      boxShadow: { tactile: '0 7px 18px rgba(0,0,0,.10)', panel: '0 18px 50px rgba(0,0,0,.08)' },
      maxWidth: { site: '1480px' },
    },
  },
  plugins: [],
}
