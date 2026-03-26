/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#101321",
        mist: "#eef3ff",
        dawn: "#f6f9ff",
        accent: "#0f766e",
        ember: "#b45309",
      },
      boxShadow: {
        panel: "0 10px 30px rgba(11, 28, 58, 0.12)",
      },
    },
  },
  plugins: [],
};
