const path = require('path');
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
          '$.tablesorter': 'tablesorter'
      })
  ],
  module: {
    rules: [
      {test: /\.txt$/, use: 'raw-loader' },
      {test: /\.css$/, use: ['style-loader', 'css-loader']},
      {test: /\.scss$/, use: ['style-loader', 'css-loader', 'sass-loader']},
      {
        test: /\.(woff(2)?|ttf|eot|svg)(\?v=\d+\.\d+\.\d+)?$/,
        use: [
          {
            loader: 'file-loader',
            options: {
              name: '[name].[ext]',
              outputPath: '../fonts/'
            }
          }
        ]
      },
      {
        test: /\.(png|jpe?g|gif)$/i,
        use: [
          {
            loader: 'file-loader',
            options: {
              name: '[name].[ext]',
              outputPath: '../images/'
            }
          },
        ],
      },
    ],
  },
  resolve: {
    modules: [
      'node_modules',
    ],
    descriptionFiles: ['package.json'],
    extensions: ['.js', '.jsx']
  },
};
