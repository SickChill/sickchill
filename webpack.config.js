const path = require('path');

module.exports = {
    devtool: '#inline-source-map',
    module: {
        loaders: [{
            loader: 'babel-loader',

            // Skip any files outside of your project's `src` directory
            include: [
                path.resolve(__dirname, 'src')
            ],

            // Only run `.js` and `.jsx` files through Babel
            test: /\.jsx?$/,

            // Options to configure babel with
            query: {
                plugins: ['transform-runtime'],
                presets: [
                    'es2015',
                    'stage-0'
                ]
            }
        }]
    },
    entry: [
        // Set up an ES6-ish environment
        'babel-polyfill',

        // Add your application's scripts below
        './gui/slick/js/index'
    ],
    output: {
        filename: 'bundle.js',
        path: path.resolve(__dirname, './gui/slick/js/dist/')
    }
};
