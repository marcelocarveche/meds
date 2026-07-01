/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                background: "#0d1117", // GitHub Dark Dimmed
                surface: "#161b22",
                border: "#30363d",
                primary: "#2f81f7", // GitHub Blue
                text: "#c9d1d9",
                muted: "#8b949e"
            }
        },
    },
    plugins: [],
}
