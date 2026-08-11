/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./src/**/*.{js,ts,jsx,tsx,mdx}'],
  theme: {
    extend: {
      colors: {
        brand: { 50: '#EEF2FF', 100: '#E0E7FF', 200: '#C7D2FE', 300: '#A5B4FC', 400: '#818CF8', 500: '#6366F1', 600: '#4F46E5', 700: '#4338CA', 800: '#3730A3', 900: '#312E81' },
        accent: { 400: '#2DD4BF', 500: '#14B8A6', 600: '#0D9488' },
      },
      fontFamily: { sans: ['"PingFang SC"', '"Microsoft YaHei"', 'system-ui', 'sans-serif'] },
      animation: { 'fade-in': 'fadeIn 0.6s ease-out', 'slide-up': 'slideUp 0.5s ease-out' },
      keyframes: {
        fadeIn: { '0%': { opacity: '0' }, '100%': { opacity: '1' } },
        slideUp: { '0%': { opacity: '0', transform: 'translateY(20px)' }, '100%': { opacity: '1', transform: 'translateY(0)' } },
      },
    },
  },
  plugins: [],
}