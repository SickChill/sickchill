var path = require('path');
var webpack = require('webpack');

const MiniCssExtractPlugin = require("mini-css-extract-plugin");
var AssetsPlugin = require('assets-webpack-plugin');

module.exports = {
    mode: 'development',
    entry: {
        core: "./js/core.js",
        core: "./js/globals.js",
        ajaxEpSearch: "./js/ajaxEpSearch.js",
        ajaxNotifications: "./js/ajaxNotifications.js",
        apibuilder: "./js/apibuilder.js",
        blackwhite: "./js/blackwhite.js",
        browser: "./js/browser.js",
        configProviders: "./js/configProviders.js",
        globals: "./js/globals.js",
        imageSelector: "./js/imageSelector.js",
        parsers: "./js/parsers.js",
        plotTooltip: "./js/plotTooltip.js",
        ratingTooltip: "./js/ratingTooltip.js",
        rootDirs: "./js/rootDirs.js",
        testRename: "./js/testRename.js",
        formwizard: "./js/lib/formwizard.js",
        "jquery.bookmarkscroll": "./js/lib/jquery.bookmarkscroll.js",
        "jquery.form": "./js/lib/jquery.form.min.js",
        "jquery.scrolltopcontrol": "./js/lib/jquery.scrolltopcontrol-1.1.js",
        "jquery.selectboxes": "./js/lib/jquery.selectboxes.min.js"

    },
    output: {
        path: path.resolve(__dirname, 'sickchill', 'gui', 'slick', 'static'),
        publicPath: "/static/",
        // filename: '[name]-bundle-[contenthash].js'
        filename: '[name]-bundle.js'
    },
    module: {
        rules: [
            {
                test: /\.css$/i,
                use: [MiniCssExtractPlugin.loader, "css-loader"],
            },
            {
                test: /\.m?js$/,
                exclude: /node_modules/,
                use: {
                    loader: "babel-loader",
                    options: {
                        presets: ['@babel/preset-env']
                    }
                }
            },
            {
                test: require.resolve('./js/globals.js'),
                use:
                    'exports-loader?type=commonjs&exports=$,getMeta,scRoot,srDefaultPage,themeSpinner,anonURL,topImageHtml,loading,srPID',
            },
        ]
    },
    plugins: [
        new AssetsPlugin({path: path.resolve(__dirname, 'sickchill', 'gui', 'slick', 'static')}),
        new webpack.ProvidePlugin({
            $: 'jquery',
            jQuery: 'jquery',
            'window.jQuery': 'jquery',
            _map: ['lodash', 'map'],
            _: 'lodash',
        })
    ]
};


