/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        chassis: {
          950: '#07080A',
          900: '#0B0C0E',
          850: '#0F1115',
          800: '#14171E',
          750: '#1A1E26',
          700: '#212630',
        },
        surface: {
          base: '#111317',
          panel: '#161920',
          elevated: '#1C212B',
          overlay: '#222834',
        },
        border: {
          subtle: '#222732',
          DEFAULT: '#2B3240',
          focus: '#3D4659',
          bright: '#4F5B73',
        },
        metrology: {
          green: {
            DEFAULT: '#21D789',
            bright: '#28E895',
            dim: '#149A5F',
            glow: 'rgba(33, 215, 137, 0.25)',
          },
          amber: {
            DEFAULT: '#E5C07B',
            bright: '#F0D18F',
            dim: '#B89753',
          },
          blue: {
            DEFAULT: '#61AFEF',
            bright: '#79C0FF',
            dim: '#437CB8',
          },
          crimson: {
            DEFAULT: '#E06C75',
            bright: '#FF7B85',
            dim: '#A8444C',
          }
        }
      },
      fontFamily: {
        sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
        mono: ['JetBrains Mono', 'Consolas', 'Courier New', 'monospace'],
      },
      boxShadow: {
        'instrument': '0 8px 32px rgba(0, 0, 0, 0.55), inset 0 1px 0 rgba(255, 255, 255, 0.04)',
        'glow-green': '0 0 20px rgba(33, 215, 137, 0.22)',
        'glow-amber': '0 0 20px rgba(229, 192, 123, 0.22)',
        'glow-blue': '0 0 20px rgba(97, 175, 239, 0.22)',
      }
    },
  },
  plugins: [],
}

