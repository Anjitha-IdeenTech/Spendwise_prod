/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
        outfit: ['Outfit', 'sans-serif'],
      },
      colors: {
        app: 'var(--bg-app)',
        surface: 'var(--bg-surface)',
        secondary: 'var(--bg-secondary)',
        borderTheme: 'var(--border-color)',
        textPrimary: 'var(--text-primary)',
        textSecondary: 'var(--text-secondary)',
        accent: {
          budget: 'var(--accent-budget)',
          savings: 'var(--accent-savings)',
          expenses: 'var(--accent-expenses)',
          approvals: 'var(--accent-approvals)',
          analytics: 'var(--accent-analytics)',
          alerts: 'var(--accent-alerts)',
        }
      }
    },
  },
  plugins: [],
}
