/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        assapp: {
          primary: "#1e40af",
          accent: "#0d9488",
          warm: "#f59e0b",
        },
      },
    },
  },
  plugins: [],
};
