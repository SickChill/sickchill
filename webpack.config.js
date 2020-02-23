const path = require('path');
const MiniCssExtractPlugin = require('mini-css-extract-plugin');
const webpack = require('webpack');

module.exports = {
  entry: './gui/slick/js/webpack.js',
  output: {
    filename: 'core.min.js',
    path: path.resolve(__dirname, './gui/slick/js'),
  },
  mode: 'development',
  plugins: [
      new webpack.ProvidePlugin({
          $: 'jquery',
          jQuery: 'jquery',
          '_': 'lodash',
      })
  ]
};
