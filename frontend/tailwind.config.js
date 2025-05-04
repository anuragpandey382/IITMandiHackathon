/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        primary: '#3B82F6', // Blue shade for branding
        darkBg: '#111827', // Dark mode background
        lightBg: '#F9FAFB', // Light mode background
        darkText: '#F3F4F6', // Light text in dark mode
        lightText: '#1F2937', // Dark text in light mode
      },
    },
  },
  plugins: [],
}

