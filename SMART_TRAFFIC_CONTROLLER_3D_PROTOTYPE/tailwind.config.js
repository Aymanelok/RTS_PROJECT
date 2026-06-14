/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui', 'Segoe UI', 'sans-serif'],
      },
      colors: {
        city: {
          950: '#020617',
          900: '#07111f',
          800: '#0b1729',
          700: '#12243a',
        },
        cyanGlow: '#22d3ee',
        safe: '#22c55e',
        danger: '#ef4444',
        warning: '#facc15',
      },
      boxShadow: {
        glow: '0 0 30px rgba(34, 211, 238, 0.22)',
        greenGlow: '0 0 30px rgba(34, 197, 94, 0.35)',
        redGlow: '0 0 30px rgba(239, 68, 68, 0.25)',
      },
      animation: {
        pulseGlow: 'pulseGlow 2.4s ease-in-out infinite',
        scan: 'scan 8s linear infinite',
        float: 'float 5s ease-in-out infinite',
      },
      keyframes: {
        pulseGlow: {
          '0%, 100%': { opacity: '0.65', filter: 'brightness(1)' },
          '50%': { opacity: '1', filter: 'brightness(1.25)' },
        },
        scan: {
          '0%': { transform: 'translateX(-25%)' },
          '100%': { transform: 'translateX(125%)' },
        },
        float: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-5px)' },
        },
      },
    },
  },
  plugins: [],
};
