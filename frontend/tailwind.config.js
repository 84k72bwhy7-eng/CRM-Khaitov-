/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{js,jsx,ts,tsx}"],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: "#FACC15",
          hover: "#EAB308",
          foreground: "#000000"
        },
        secondary: {
          DEFAULT: "#000000",
          hover: "#171717",
          foreground: "#FFFFFF"
        },
        background: {
          DEFAULT: "#FFFFFF",
          subtle: "#F9FAFB",
          dark: "#0F172A"
        },
        text: {
          primary: "#0F172A",
          secondary: "#475569",
          muted: "#94A3B8"
        },
        border: {
          DEFAULT: "#E2E8F0",
          focus: "#000000"
        },
        status: {
          success: "#22C55E",
          warning: "#F59E0B",
          error: "#EF4444",
          info: "#3B82F6"
        }
      },
      fontFamily: {
        heading: ["Manrope", "sans-serif"],
        body: ["Inter", "sans-serif"]
      }
    }
  },
  plugins: []
}
