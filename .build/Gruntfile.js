module.exports = function(grunt) {
    require('load-grunt-tasks')(grunt);

    grunt.initConfig({
        clean: {
            dist: './dist/',
            bower_components: './bower_components'
        },
        bower: {
            install: {
                options: {
                    copy: false
                }
            }
        },
        bower_concat: {
            all: {
                dest: './dist/bower.js',
                cssDest: './dist/bower.css',
                exclude: [
                ],
                dependencies: {
                },
                mainFiles: {
                    'tablesorter': [
                        'dist/js/jquery.tablesorter.combined.js',
                        'dist/js/widgets/widget-columnSelector.min.js',
                        'dist/js/widgets/widget-stickyHeaders.min.js',
                        'dist/css/theme.blue.min.css'
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
                    ]
                },
                bowerOptions: {
                    relative: false
                }
            }
        },
        uglify: {
            bower: {
                files: {
                    '../gui/slick/js/vender.min.js': ['./dist/bower.js']
                }
            },
            core: {
                files: {
                    '../gui/slick/js/core.min.js': ['../gui/slick/js/core.js']
                }
            }
        },
        sass: {
            options: {
                sourceMap: true
            },
            core: {
                files: {
                    './dist/core.css': ['../gui/slick/scss/core.scss']
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
                    '../gui/slick/css/vender.min.css': ['./dist/bower.css']
                }
            },
            core: {
                files: {
                    '../gui/slick/css/core.min.css': ['./dist/core.css']
                }
            }
        },
        jshint: {
            options: {
                jshintrc: '../.jshintrc'
            },
            all: [
                '../gui/slick/js/**/*.js',
                '!../gui/slick/js/lib/**/*.js',
                '!../gui/slick/js/ajaxNotifications.js',
                '!../gui/slick/js/**/*.min.js', // We use this because ignores doesn't seem to work :(
            ]
        }
    });

    grunt.loadNpmTasks('grunt-contrib-clean');
    grunt.loadNpmTasks('grunt-bower-task');
    grunt.loadNpmTasks('grunt-bower-concat');
    grunt.loadNpmTasks('grunt-contrib-uglify');
    grunt.loadNpmTasks('grunt-contrib-cssmin');
    grunt.loadNpmTasks('grunt-contrib-jshint');

    grunt.registerTask('default', [
        'clean',
        'bower',
        'bower_concat',
        'uglify',
        'sass',
        'cssmin'
    ]);
    grunt.registerTask('travis', [
        'jshint'
    ]);
};
