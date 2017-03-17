module.exports = function(grunt) {
    require('load-grunt-tasks')(grunt);

    grunt.initConfig({
        clean: {
            dist: './dist/',
            'bower_components': './bower_components',
            fonts: './gui/slick/css/*.ttf',
            options: {
                force: true
            }
        },
        bower: {
            install: {
                options: {
                    copy: false
                }
            }
        },
        bower_concat: { // jshint ignore:line
            all: {
                dest: {
                    js: './dist/bower.js',
                    css: './dist/bower.css'
                },
                exclude: [],
                dependencies: {},
                mainFiles: {
                    'tablesorter': [
                        'dist/js/jquery.tablesorter.combined.js',
                        'dist/js/widgets/widget-columnSelector.min.js',
                        'dist/js/widgets/widget-stickyHeaders.min.js',
                        'dist/css/theme.blue.min.css'
                    ],
                    'bootstrap': [
                        'dist/css/bootstrap.min.css',
                        'dist/js/bootstrap.min.js'
                    ],
                    'bootstrap-formhelpers': [
                        'dist/js/bootstrap-formhelpers.min.js'
                    ],
                    'isotope': [
                        "dist/isotope.pkgd.min.js"
                    ],
                    "outlayer": [
                        "item.js",
                        "outlayer.js"
                    ],
                    "openSans": [
                        "*.ttf", "*.css"
                    ]
                },
                bowerOptions: {
                    relative: false
                }
            }
        },
        copy: {
            openSans: {
                files: [{
                    expand: true,
                    dot: true,
                    cwd: 'bower_components/openSans',
                    src: [
                        '*.ttf'
                    ],
                    dest: './gui/slick/css/'
                }]
            },
            glyphicon: {
                files: [{
                    expand: true,
                    dot: true,
                    cwd: 'bower_components/bootstrap/fonts',
                    src: [
                        '*.eot',
                        '*.svg',
                        '*.ttf',
                        '*.woff',
                        '*.woff2'
                    ],
                    dest: './gui/slick/fonts/'
                }]
            }
        },
        uglify: {
            bower: {
                files: {
                    './gui/slick/js/vender.min.js': ['./dist/bower.js']
                }
            },
            core: {
                files: {
                    './gui/slick/js/core.min.js': ['./gui/slick/js/core.js']
                }
            }
        },
        sass: {
            options: {
                sourceMap: true
            },
            core: {
                files: {
                    './dist/core.css': ['./gui/slick/scss/core.scss']
                }
            }
        },
        cssmin: {
            options: {
                shorthandCompacting: false,
                roundingPrecision: -1
            },
            bower: {
                files: {
                    './gui/slick/css/vender.min.css': ['./dist/bower.css']
                }
            },
            core: {
                files: {
                    './gui/slick/css/core.min.css': ['./dist/core.css']
                }
            }
        },
        jshint: {
            options: {
                jshintrc: './.jshintrc'
            },
            all: [
                './gui/slick/js/**/*.js',
                '!./gui/slick/js/lib/**/*.js',
                '!./gui/slick/js/ajaxNotifications.js',
                '!./gui/slick/js/**/*.min.js', // We use this because ignores doesn't seem to work :(
            ]
        },
        mocha: {
            all: {
                src: ['tests/testrunner.html'],
            },
            options: {
                run: true
            }
        },
        po2json: {
            messages: {
                options: {
                    format: 'jed',
                    singleFile: true
                },
                files: [{
                    expand: true,
                    src: './locale/*/LC_MESSAGES/messages.po',
                    dest: '',
                    ext: '' // workaround for relative files
                }]
            }
        },
        exec: {
            babel_extract: {cmd: 'python setup.py extract_messages'},
            babel_update: {cmd: 'python setup.py update_catalog'},
            crowdin_upload: {cmd: 'crowdin-cli-py upload sources'},
            crowdin_download: {cmd: 'crowdin-cli-py download'},
            babel_compile: {cmd: 'python setup.py compile_catalog'}
        }
    });

    grunt.loadNpmTasks('grunt-contrib-clean');
    grunt.loadNpmTasks('grunt-bower-task');
    grunt.loadNpmTasks('grunt-bower-concat');
    grunt.loadNpmTasks('grunt-contrib-copy');
    grunt.loadNpmTasks('grunt-contrib-uglify');
    grunt.loadNpmTasks('grunt-contrib-cssmin');
    grunt.loadNpmTasks('grunt-contrib-jshint');
    grunt.loadNpmTasks('grunt-mocha');
    grunt.loadNpmTasks('grunt-po2json');
    grunt.loadNpmTasks('grunt-exec');

    grunt.registerTask('default', [
        'clean',
        'bower',
        'bower_concat',
        'copy',
        'uglify',
        'sass',
        'cssmin',
        'jshint',
        'mocha'
    ]);
    grunt.registerTask('travis', [
        'jshint',
        'mocha'
    ]);
    grunt.registerTask('update_trans', 'Update translations. In order to sync with Crowdin, set the env-var `CROWDIN_API_KEY`.', function() {
        var tasks = [
            'exec:babel_extract',
            'exec:babel_update',
            // + crowdin
            'exec:babel_compile',
            'po2json'
        ];
        if(process.env['CROWDIN_API_KEY']) {
            tasks.splice(2, 0, 'exec:crowdin_upload', 'exec:crowdin_download'); // insert items at index 2
        } else {
            grunt.log.warn('WARNING: Env variable `CROWDIN_API_KEY` is not set, not syncing with Crowdin.');
        }

        grunt.task.run(tasks);
    });
};
