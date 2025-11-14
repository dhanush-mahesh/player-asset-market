/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
      },
      colors: {
        'brand': {
          'light': '#0a0a0a',
          'DEFAULT': '#000000',
          'dark': '#000000',
        },
        'highlight': {
          'light': '#262626',
          'DEFAULT': '#171717',
          'dark': '#0d0d0d',
        }
      },
      // --- ⭐️ 1. ADD THIS SECTION ---
      animation: {
        'text-shimmer': 'text-shimmer 3s ease-in-out infinite',
      },
      // --- ⭐️ 2. ADD THIS SECTION ---
      keyframes: {
        'text-shimmer': {
          '0%, 100%': { backgroundPosition: '0% 50%' },
          '50%': { backgroundPosition: '100% 50%' },
        },
      },
      // --- ⭐️ 3. ADD THIS SECTION ---
      backgroundSize: {
        '200%': '200% auto',
      },
    },
  },
  plugins: [],
}

