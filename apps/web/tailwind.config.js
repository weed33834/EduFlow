/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./src/**/*.{js,ts,jsx,tsx,mdx}'],
  theme: {
    extend: {
      colors: {
        brand: { 50: '#F2F7FF', 100: '#E5EAFF', 200: '#A9AEFF', 500: '#6F6FFF', 600: '#4B3FE3', 700: '#3C2ECA', 900: '#1A1759' },
        accent: { 400: '#27D2BF', 500: '#1BBFA9' },
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