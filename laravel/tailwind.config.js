/** @type {import('tailwindcss').Config} */
export default {
    content: [
        './resources/**/*.blade.php',
        './resources/**/*.js',
        './app/**/*.php',
    ],
    theme: {
        extend: {
            colors: {
                bm: {
                    black: '#111111',
                    dark: '#1F1F1F',
                    med: '#2E2E2E',
                    blue: '#1E3A8A',
                    green: '#009B3A',
                    yellow: '#FFC107',
                },
            },
            fontFamily: {
                display: ['Orbitron', 'Poppins', 'sans-serif'],
                sans: ['"Exo 2"', 'Poppins', 'sans-serif'],
            },
        },
    },
    plugins: [require('@tailwindcss/forms')],
};
