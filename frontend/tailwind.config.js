/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Poppins', 'Inter', 'sans-serif'],
        serif: ['Playfair Display', 'serif'],
        display: ['Montserrat', 'sans-serif'],
      },
      colors: {
        primary: {
          50: "#E6EFFA",
          100: "#CCDFF5",
          200: "#99BFEB",
          300: "#669FE0",
          400: "#337FD6",
          500: "#2563EB", // Main primary
          600: "#1E4FBC",
          700: "#183B8D",
          800: "#12275E",
          900: "#09132F",
        },
        secondary: {
          50: "#F0E5FA",
          100: "#E1CCF5",
          200: "#C399EB",
          300: "#A566E0",
          400: "#8833D6",
          500: "#7C2FEB", // Main secondary
          600: "#6226BC",
          700: "#491C8D",
          800: "#31135E",
          900: "#18092F",
        },
        accent: {
          50: "#FFEEE5",
          100: "#FFDDCC",
          200: "#FFBB99",
          300: "#FF9966",
          400: "#FF7733",
          500: "#FF5500", // Main accent
          600: "#CC4400",
          700: "#993300",
          800: "#662200",
          900: "#331100",
        },
        pastel: {
          pink: "#FFD6E0",
          yellow: "#FFF1D6",
          green: "#D6FFED",
          blue: "#D6E6FF",
          purple: "#E0D6FF",
        },
        fashion: {
          beige: "#F5F0E6",
          caramel: "#C19A6B",
          navy: "#1A2B4C",
          emerald: "#148960",
          burgundy: "#722F37",
        },
      },
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
        'gradient-conic': 'conic-gradient(from 180deg at 50% 50%, var(--tw-gradient-stops))',
        'gradient-diagonal': 'linear-gradient(to bottom right, var(--tw-gradient-stops))',
        'texture-paper': "url('/textures/paper.png')",
        'texture-fabric': "url('/textures/fabric.png')",
      },
      animation: {
        'float': 'float 6s ease-in-out infinite',
        'shimmer': 'shimmer 3s linear infinite',
        'spin-slow': 'spin 8s linear infinite',
        'fade-in-down': 'fadeInDown 0.7s ease-out',
        'fade-in-up': 'fadeInUp 0.7s ease-out',
        'bounce-slow': 'bounce 3s ease-in-out infinite',
        'pulse-subtle': 'pulseSubtle 4s ease-in-out infinite',
        'gradient-x': 'gradientX 3s ease infinite',
        'gradient-y': 'gradientY 3s ease infinite',
        'gradient-xy': 'gradientXY 3s ease infinite',
        'scale-in': 'scaleIn 0.5s ease-out',
        'slide-in-right': 'slideInRight 0.5s ease-out',
        'slide-in-left': 'slideInLeft 0.5s ease-out',
        'rotate-slow': 'rotateSlow 10s linear infinite',
        'rotate-reverse': 'rotateReverse 10s linear infinite',
        'ping-slow': 'pingSlow 2s cubic-bezier(0, 0, 0.2, 1) infinite',
        'wiggle': 'wiggle 1s ease-in-out infinite',
      },
      keyframes: {
        float: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-10px)' },
        },
        shimmer: {
          '0%': { backgroundPosition: '-1000px 0' },
          '100%': { backgroundPosition: '1000px 0' },
        },
        fadeInDown: {
          '0%': { opacity: '0', transform: 'translateY(-20px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        fadeInUp: {
          '0%': { opacity: '0', transform: 'translateY(20px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        pulseSubtle: {
          '0%, 100%': { opacity: 1 },
          '50%': { opacity: 0.85 },
        },
        gradientX: {
          '0%, 100%': {
            'background-size': '200% 200%',
            'background-position': 'left center'
          },
          '50%': {
            'background-size': '200% 200%',
            'background-position': 'right center'
          }
        },
        gradientY: {
          '0%, 100%': {
            'background-size': '200% 200%',
            'background-position': 'center top'
          },
          '50%': {
            'background-size': '200% 200%',
            'background-position': 'center bottom'
          }
        },
        gradientXY: {
          '0%, 100%': {
            'background-size': '200% 200%',
            'background-position': 'left top'
          },
          '50%': {
            'background-size': '200% 200%',
            'background-position': 'right bottom'
          }
        },
        scaleIn: {
          '0%': { transform: 'scale(0.9)', opacity: 0 },
          '100%': { transform: 'scale(1)', opacity: 1 }
        },
        slideInRight: {
          '0%': { transform: 'translateX(100%)', opacity: 0 },
          '100%': { transform: 'translateX(0)', opacity: 1 }
        },
        slideInLeft: {
          '0%': { transform: 'translateX(-100%)', opacity: 0 },
          '100%': { transform: 'translateX(0)', opacity: 1 }
        },
        rotateSlow: {
          '0%': { transform: 'rotate(0deg)' },
          '100%': { transform: 'rotate(360deg)' }
        },
        rotateReverse: {
          '0%': { transform: 'rotate(0deg)' },
          '100%': { transform: 'rotate(-360deg)' }
        },
        pingSlow: {
          '0%': { transform: 'scale(1)', opacity: 1 },
          '75%, 100%': { transform: 'scale(2)', opacity: 0 }
        },
        wiggle: {
          '0%, 100%': { transform: 'rotate(-3deg)' },
          '50%': { transform: 'rotate(3deg)' }
        },
      },
      boxShadow: {
        'inner-light': 'inset 0 2px 4px 0 rgba(255, 255, 255, 0.05)',
        'glass': '0 8px 32px 0 rgba(31, 38, 135, 0.17)',
        'neon': '0 0 10px rgba(67, 220, 252, 0.7), 0 0 20px rgba(67, 220, 252, 0.4)',
        'fashion': '0 10px 25px -5px rgba(44, 62, 80, 0.1), 0 5px 10px -5px rgba(44, 62, 80, 0.04)',
        'colorful': '0 0 15px rgba(124, 47, 235, 0.3)',
        'glow': '0 0 15px rgba(255, 255, 255, 0.5), 0 0 30px rgba(255, 255, 255, 0.3)',
        'float': '0 10px 20px -5px rgba(0, 0, 0, 0.1), 0 5px 10px -7.5px rgba(0, 0, 0, 0.05)',
        'float-lg': '0 20px 40px -10px rgba(0, 0, 0, 0.1), 0 10px 20px -10px rgba(0, 0, 0, 0.04)',
      },
      transitionProperty: {
        'height': 'height',
        'spacing': 'margin, padding',
        'width': 'width',
        'size': 'height, width',
      },
      // Add backdrop filters
      backdropFilter: {
        'none': 'none',
        'blur': 'blur(4px)',
        'blur-md': 'blur(8px)',
        'blur-lg': 'blur(16px)',
        'blur-xl': 'blur(24px)',
      },
    },
  },
  plugins: [],
} 