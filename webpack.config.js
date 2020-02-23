const path = require('path');
const MiniCssExtractPlugin = require('mini-css-extract-plugin');
const webpack = require('webpack');

module.exports = {
  entry: './gui/slick/js/core.js',
  output: {
    filename: 'core.min.js',
    path: path.resolve(__dirname, './gui/slick/js'),
  },
  mode: 'development',
  plugins: [
      new MiniCssExtractPlugin(),
      new webpack.ProvidePlugin({
          $: 'jquery',
          jQuery: 'jquery',
          '_': 'lodash'
      })
  ],
  module: {
      rules: [
          {
              test: /\.css$/i,
              use: [MiniCssExtractPlugin.loader, 'css-loader'],
          },
          {
              test: /jquery-plugin/,
              loader: 'imports?jQuery=jquery,$=jquery,this=>window'
          }
      ],
  }
};
