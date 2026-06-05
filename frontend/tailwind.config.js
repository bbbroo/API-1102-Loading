export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        hdr: {
          navy: "#182d3f",
          navy2: "#102435",
          line: "#d7dde3",
          panel: "#f7f9fb",
          green: "#0f9f6e",
          red: "#c2413a",
          amber: "#c47a13"
        }
      },
      fontFamily: {
        sans: ["Inter", "Segoe UI", "Arial", "sans-serif"]
      }
    }
  },
  plugins: []
};
