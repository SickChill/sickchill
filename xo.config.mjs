import globals from 'globals';

const xoConfig = [
    {
        ignores: [
            '**/core.min.js',
            '**/vendor.min.js',
            'lib/**/*',
            'Gruntfile.js',
            'sickchill/gui/slick/js/lib/**',
            'tests/js/index.js',
            'frontend/static/**',
            'frontend/movies/static/**',
            'frontend/shows/static/**',
            'frontend/config/static/**',
            'frontend/*/src/**',
            'frontend/**/templates/**',
            'webpack.config.js',
            'sickchill/gui/slick/css/**',
            'sickchill/locale/**',
            '**/*.md',
        ],
    },
    {
        space: 4,
        rules: {
            'unicorn/filename-case': 'off',
            'unicorn/prefer-node-append': 'off',
            'unicorn/prefer-global-this': 'off',
            'unicorn/expiring-todo-comments': 'off',
            'unicorn/no-immediate-mutation': 'off',
            'unicorn/no-array-sort': 'off',
            'require-unicode-regexp': 'off',
            '@stylistic/curly-newline': 'off',
            'max-lines': 'off',
            // Numbered groups are used as match[1]/match[2] throughout the GUI JS.
            'regexp/prefer-named-capture-group': 'off',
            // Number.parseInt(x, 10) is kept: Number(x) is NaN on trailing junk.
            'unicorn/prefer-number-coercion': 'off',
            // Treats path strings and callbacks as booleans and wants is- prefixes.
            'unicorn/consistent-boolean-name': 'off',
            // Gettext shims on window._ / gt / _n, and window.location during restart.
            'unicorn/no-global-object-property-assignment': 'off',
            // Reordering && can skip later checks that have side effects.
            'unicorn/prefer-simple-condition-first': 'off',
            // Pulling _() outside a ternary breaks gettext message extraction.
            'unicorn/prefer-minimal-ternary': 'off',
            // GUI regexes run on trusted UI/status strings, not untrusted input.
            'regexp/no-super-linear-backtracking': 'off',
            'regexp/no-super-linear-move': 'off',
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
                scDefaultPage: 'readonly',
                scPID: 'writable',
                loading: 'readonly',
                configSuccess: 'readonly',
                bindMasonryImageLayout: 'readonly',
                installGettext: 'readonly',
                shouldSkipLocaleFetch: 'readonly',
                startSickchillUi: 'readonly',
                isMeta: 'readonly',
                notifyModal: 'readonly',
                shiftReturn: 'readonly',
                initConfigComponentTabs: 'readonly',
                persistConfigTabHash: 'readonly',
                SICKCHILL: 'writable',
                __: 'readonly',
            },
        },
    },
    {
        // Jed/gettext JSON uses an empty "" key for domain/plural_forms/lang metadata.
        files: '**/LC_MESSAGES/messages.json',
        rules: {
            'json/no-empty-keys': 'off',
        },
    },
    {
        files: 'package.json',
        rules: {
            // CommonJS/Grunt tree; "type": "module" would change load semantics.
            'package-json/prefer-type-module': 'off',
            'package-json/require-engines': 'off',
            'package-json/sort-properties': 'off',
            'package-json/prefer-shorthand': 'off',
            'package-json/dependency-version-range': 'off',
        },
    },
];

export default xoConfig;
