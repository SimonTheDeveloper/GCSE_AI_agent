module.exports = {
  content: [
    "./frontend/*.html",
    "./frontend/**/*.js",
    "/frontend/*.html",
    "/frontend/**/*.js",
  ],
  theme: {
    extend: {
    fontFamily: {
        roboto: ['Roboto'], // Define 'roboto' as a font option
      },
    },
  },
  plugins: [],
}