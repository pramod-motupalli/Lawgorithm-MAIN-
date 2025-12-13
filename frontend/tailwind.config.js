/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        police: {
          50: '#f4f6f8',
          100: '#e3e8ee',
          200: '#c2cdd8',
          300: '#90a4bb',
          400: '#5c7696',
          500: '#40567a',
          600: '#304261',
          700: '#27364f',
          800: '#222d41',
          900: '#1e2636',
        }
      },
      fontFamily: {
        serif: ['"Merriweather"', 'serif'],
        sans: ['"Inter"', 'sans-serif'],
      }
    },
  },
  plugins: [],
}
