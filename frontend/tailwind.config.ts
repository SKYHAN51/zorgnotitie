import type { Config } from "tailwindcss";
export default {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        sage: {
          50: "#F1F6F1",
          100: "#E1EDE1",
          200: "#C3DAC5",
          300: "#9FC3A4",
          400: "#79A981",
          500: "#5A8D64",
          600: "#46734F",
          700: "#395D40",
          800: "#2E4A34",
          900: "#253B29",
        },
        cream: {
          50: "#FBF9F5",
          100: "#F6F1E9",
        },
      },
      boxShadow: {
        soft: "0 2px 24px -6px rgba(46, 74, 52, 0.10)",
        softer: "0 1px 12px -3px rgba(46, 74, 52, 0.08)",
      },
    },
  },
  plugins: [],
} satisfies Config;
