// Generated using webpack-cli https://github.com/webpack/webpack-cli

const path = require("path");
// const HtmlWebpackPlugin = require("html-webpack-plugin");
// const CopyPlugin = require("copy-webpack-plugin");
const MiniCssExtractPlugin = require("mini-css-extract-plugin");
const WorkboxWebpackPlugin = require("workbox-webpack-plugin");

const isProduction = process.env.NODE_ENV == "production";

const stylesHandler = MiniCssExtractPlugin.loader;

const config = {
  context:  path.resolve(__dirname, 'frontend/templates'),
  entry: {
      shows: ['./js/shows.jsx'],
      show: ['./js/show.jsx']
  },
  output: {
    path: __dirname + "/frontend/static",
    filename: '[name].js',
    publicPath: path.resolve('static')
  },
 resolve: {
  extensions: ['.js','.jsx','.css']
 },
  devServer: {
    open: true,
    host: "localhost",
  },
  plugins: [
    // new HtmlWebpackPlugin({
    //   template: "shows.html",
    //   inject: false
    //
    // }),
    // new CopyPlugin({
    //   patterns: [
    //     '*.html'
    //   ]
    // }),
    new MiniCssExtractPlugin(),

    // Add your plugins here
    // Learn more about plugins from https://webpack.js.org/configuration/plugins/
  ],
  module: {
    rules: [
      {
        test: /\.(js|jsx)$/i,
        loader: "babel-loader",
      },
      {
        test: /\.css$/i,
        use: [stylesHandler, "css-loader"],
      },
      {
        test: /\.s[ac]ss$/i,
        use: [stylesHandler, "css-loader", "sass-loader"],
      },
      {
        test: /\.(eot|svg|ttf|woff|woff2|png|jpg|gif)$/i,
        type: "asset",
      },

      // Add your rules for custom modules here
      // Learn more about loaders from https://webpack.js.org/loaders/
    ],
  },
};

module.exports = () => {
  if (isProduction) {
    config.mode = "production";

    config.plugins.push(new WorkboxWebpackPlugin.GenerateSW());
  } else {
    config.mode = "development";
  }
  return config;
};
