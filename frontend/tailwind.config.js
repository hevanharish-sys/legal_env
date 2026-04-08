/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        schibsted: ["Schibsted Grotesk", "Inter", "system-ui", "sans-serif"],
        inter: ["Inter", "system-ui", "sans-serif"],
        noto: ["Noto Sans", "system-ui", "sans-serif"],
        fustat: ["Fustat", "Inter", "system-ui", "sans-serif"],
      },
      colors: {
        ink: "#000000",
        mid: "#505050",
        lightBg: "#f8f8f8",
        badgeDark: "#0e1311",
      },
      boxShadow: {
        soft: "0 10px 40px rgba(0,0,0,0.12)",
      },
    },
  },
  plugins: [],
};

