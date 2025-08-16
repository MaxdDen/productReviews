/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./*.{html,js}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Montserrat', 'sans-serif'],
      },
      borderColor: {
        'sidebar': 'rgba(107,102,151,0.2)',
        'thead': 'rgba(107,99,151,0.2)'
      },
      boxShadow: {
        'custom': '0px 0px 4px 0px #00000040',
      },
    },
  },
  plugins: [
    require('@tailwindcss/line-clamp'),
  ],
}
