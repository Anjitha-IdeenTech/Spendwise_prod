/** @type {import('tailwindcss').Config} */

// Every theme color is a CSS var holding raw RGB channels; wrapping with
// rgb(var(--x) / <alpha-value>) lets opacity modifiers (bg-brand/10) work.
const ch = (v) => `rgb(var(${v}) / <alpha-value>)`;

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
        // neutral canvas
        app:         ch('--bg-app'),
        surface:     ch('--bg-surface'),
        secondary:   ch('--bg-secondary'),
        raised:      ch('--bg-raised'),
        borderTheme: ch('--border-color'),
        line2:       ch('--border-strong'),
        // text
        textPrimary:   ch('--text-primary'),
        textSecondary: ch('--text-secondary'),
        textFaint:     ch('--text-faint'),
        onbrand:       ch('--onbrand'),
        // brand + semantic aliases (map onto the accent vars)
        brand: ch('--accent-budget'),
        gold:  ch('--accent-approvals'),
        pos:   ch('--accent-savings'),
        neg:   ch('--accent-expenses'),
        info:  ch('--accent-analytics'),
        // original per-domain accent scale (kept for Scene 1 + charts)
        accent: {
          budget:    ch('--accent-budget'),
          savings:   ch('--accent-savings'),
          expenses:  ch('--accent-expenses'),
          approvals: ch('--accent-approvals'),
          analytics: ch('--accent-analytics'),
          alerts:    ch('--accent-alerts'),
        },
      },
    },
  },
  plugins: [],
}
