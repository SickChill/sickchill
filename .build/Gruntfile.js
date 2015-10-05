module.exports = function(grunt) {
    grunt.initConfig({
        bower_concat: {
            all: {
                dest: '../gui/slick/js/_bower.js',
                // cssDest: 'gui/slick/css/_bower.css',
                exclude: [
                    // 'jquery',
                    // 'modernizr'
                ],
                dependencies: {
                    // 'underscore': 'jquery',
                    // 'backbone': 'underscore',
                    // 'jquery-mousewheel': 'jquery'
                },
                bowerOptions: {
                    relative: false
                },
            }
        },
        uglify: {
            my_target: {
                files: {
                    '../gui/slick/js/_bower.min.js': ['../gui/slick/js/_bower.js']
                }
            }
        }
    });

    grunt.loadNpmTasks('grunt-bower-concat');
    grunt.loadNpmTasks('grunt-contrib-uglify');

    grunt.registerTask('default', ['bower_concat', 'uglify']);

};
