const path = require("path");

// const CopyPlugin = require("copy-webpack-plugin");
// const HtmlWebpackPlugin = require("html-webpack-plugin");
const MiniCssExtractPlugin = require("mini-css-extract-plugin");
const {GenerateSW} = require("workbox-webpack-plugin");

const stylesHandler = MiniCssExtractPlugin.loader;

const config = {
    mode: process.env.NODE_ENV || 'development',
    resolve: {
        extensions: ['.js', '.jsx', '.css']
    },
    devServer: {
        open: true,
        host: "localhost",
    },
    plugins: [
        // new HtmlWebpackPlugin({
        //     template: "shows.html",
        //     inject: false
        //
        // }),
        // new CopyPlugin({
        //     patterns: [
        //         '*.html'
        //     ]
        // }),
        new MiniCssExtractPlugin(),
    ],

    module: {
        rules: [
            {
                test: /\.(?:js|jsx)$/i,
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
                test: /\.(?:eot|svg|ttf|woff|woff2|png|jpg|gif)$/i,
                type: "asset",
            },
        ],
    },
};

let configurations = Object.assign({}, config, {
    name: 'config',
    context: path.resolve(__dirname, 'frontend', 'config', 'src', 'js'),
    entry: {
        config: ['./config.jsx'],
    },
    output: {
        path: path.resolve(__dirname, 'frontend', 'static', 'config', 'js'),
        filename: '[name].js',
        publicPath: path.resolve('static', 'config')
    },
});
let shows = Object.assign({}, config, {
    name: 'shows',
    context: path.resolve(__dirname, 'frontend', 'shows', 'src', 'js'),
    entry: {
        shows: ['./shows.jsx'],
        show: ['./show.jsx'],
    },
    output: {
        path: path.resolve(__dirname, 'frontend', 'static', 'shows', 'js'),
        filename: '[name].js',
        publicPath: path.resolve('static', 'shows')
    },
});

let movies = Object.assign({}, config, {
    name: 'movies',
    context: path.resolve(__dirname, 'frontend', 'movies', 'src', 'js'),
    entry: {
        movies: ['./movies.jsx'],
        movie: ['./movie.jsx'],
    },
    output: {
        path: path.resolve(__dirname, 'frontend', 'static', 'movies', 'js'),
        filename: '[name].js',
        publicPath: path.resolve('static', 'movies')
    },
});

module.exports = () => {
    const outputs = [configurations, shows, movies];
    for (let item of outputs) {
        if (item.mode === "production") {
            let serviceWorker = new GenerateSW();
            // noinspection JSCheckFunctionSignatures
            item.plugins.push(serviceWorker);
        }
    }
    return outputs;
};
