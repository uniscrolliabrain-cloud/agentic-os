/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        uniscroll: {
          black: '#0A0A0A',
          yellow: '#FFD60A',
          white: '#FFFFFF'
        }
      }
    },
  },
  plugins: [],
}
