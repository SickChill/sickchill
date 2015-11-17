module.exports = function(grunt) {
    grunt.initConfig({
        bower_concat: {
            all: {
                dest: './_bower.js',
                cssDest: './_bower.css',
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
            my_target: {
                files: {
                    '../gui/slick/js/vender.min.js': ['./_bower.js'],
                    '../gui/slick/js/core.min.js': ['../gui/slick/js/core.js']
                }
            }
        },
        cssmin: {
            options: {
                shorthandCompacting: false,
                roundingPrecision: -1
            },
            target: {
                files: {
                    '../gui/slick/css/vender.min.css': ['./_bower.css'],
                    // '../gui/slick/css/core.min.css': ['./gui/slick/css/core.css']
                }
            }
        },
        jshint: {
            options: {
                eqeqeq: true
            },
            uses_defaults: ['../gui/slick/js/**/*.js']
        }
    });

    grunt.loadNpmTasks('grunt-bower-concat');
    grunt.loadNpmTasks('grunt-contrib-uglify');
    grunt.loadNpmTasks('grunt-contrib-cssmin');
    grunt.loadNpmTasks('grunt-contrib-jshint');

    grunt.registerTask('default', ['bower_concat', 'uglify', 'cssmin']);
};
