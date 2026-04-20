import globals from 'globals';

const xoConfig = [
    {
        ignores: [
            'core.min.js',
            'vendor.min.js',
            'lib/**/*',
            'Gruntfile.js',
            'sickchill/gui/slick/js/lib/*',
            'tests/js/index.js',
            'frontend/static/**',
            'frontend/movies/static/**',
            'frontend/shows/static/**',
            'frontend/config/static/**',
            'frontend/*/src/**',
            'webpack.config.js',
        ],
    },
    {
        space: 4,
        rules: {
            'unicorn/filename-case': 'off',
            'unicorn/prefer-node-append': 'off',
            'unicorn/prefer-global-this': 'off',
            'unicorn/expiring-todo-comments': 'off',
        },
        languageOptions: {
            globals: {
                ...globals.browser,
                _: 'readonly',
                scRoot: 'readonly',
                jQuery: 'readonly',
                $: 'readonly',
                metaToBool: 'readonly',
                getMeta: 'readonly',
                PNotify: 'readonly',
                themeSpinner: 'readonly',
                anonURL: 'readonly',
                Gettext: 'readonly',
                gt: 'readonly',
                _n: 'readonly',
                latinize: 'readonly',
            },
        },
    },
];

export default xoConfig;
