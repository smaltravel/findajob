/** @type {import('tailwindcss').Config} */
const colors = require('tailwindcss/colors')

module.exports = {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Cohesive app palette
        brand: colors.indigo,
        info: colors.sky,
        success: colors.emerald,
        warning: colors.amber,
        danger: colors.rose,
        muted: colors.slate,
      },
    },
  },
  plugins: [
    require('@tailwindcss/typography'),
  ],
} 