module.exports = function(grunt) {
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
    grunt.registerTask('update_trans', 'update translations', function() {
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
    /****************************************
    *  Admin only                           *
    ****************************************/
    grunt.registerTask('publish', 'create a release tag and generate CHANGES.md\n(alias for newrelease and genchanges)',
        ['newrelease', 'genchanges']);

    /****************************************
    *  Task configurations                  *
    ****************************************/
    require('load-grunt-tasks')(grunt); // loads all grunt tasks matching the ['grunt-*', '@*/grunt-*'] patterns
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
        bower_concat: {
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
                src: ['tests/mocha/testrunner.html'],
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
            // Translations
            babel_extract: {cmd: 'python setup.py extract_messages'},
            babel_update: {cmd: 'python setup.py update_catalog'},
            crowdin_upload: {cmd: 'crowdin-cli-py upload sources'},
            crowdin_download: {cmd: 'crowdin-cli-py download'},
            babel_compile: {cmd: 'python setup.py compile_catalog'},

            // Publish/Releases
            git_checkout: {
                cmd: function (b) { return 'git checkout ' + b; },
            },
            git_pull: {
                cmd: function (b) { return 'git pull' },
            },
            git_merge: {
                cmd: function (b) { return 'git merge ' + b; },
            },
            git_get_last_tag: {
                cmd: 'git for-each-ref --sort=-refname --count=1 --format "%(refname:short)" refs/tags',
                stdout: false,
                callback: function(err, stdout, stderr) {
                    grunt.config('last_tag', stdout.trim());
                }
            },
            git_list_changes: {
                cmd: 'git log --oneline ' + grunt.config('last_tag') + '..HEAD',
                stdout: false,
                callback: function(err, stdout, stderr) {
                    grunt.config('commits', stdout.replace(/^[a-f0-9]{9}\s/gm, '').trim()); // removes commit hashes
                }
            },
            git_tag_new: {
                cmd: function (sign) {
                    sign = (sign !== "true"?'':'-s ')
                    return 'git tag ' + sign + grunt.config('next_tag') + ' -m "' + grunt.config('commits') + '"';
                },
                stdout: false
            },
            git_push: {
                cmd: function (remote, branch, tags) {
                    return 'git push ' + remote + ' ' + branch + (tags === 'true'?' --tags':'');
                },
            },
            git_list_tags: {
                cmd: 'git for-each-ref --sort=refname --format="%(refname:short)|||%(objectname)|||%(contents)\\$$\\$" refs/tags',
                stdout: false,
                callback: function(err, stdout, stderr) {
                    var all_tags = stdout.replace(/-*BEGIN PGP SIGNATURE-*(\n.*){9}\n/g, '').split('$$$');
                    all_tags.splice(all_tags.length-1, 1); // There's an empty object at the end
                    for (var i = 0; i < all_tags.length; i++) {
                        var explode = all_tags[i].split('|||');
                        all_tags[i] = {
                            tag: explode[0].trim(),
                            hash: explode[1].trim(),
                            message: explode[2].trim().split('\n'),
                            previous: (i > 0 ? all_tags[i-1].tag : null)
                        };
                    }
                    grunt.config('all_tags', all_tags);
                }
            },
            commit_changelog: {
                cmd: function() {
                    file = grunt.config('changesmd_file');
                    if (!file)
                        grunt.fatal('Missing file path.');
                    path = file.substr(0, file.lastIndexOf('/', file.length-12)); // get sickrage.github.io folder
                    return 'cd ' + path +
                           ' && git commit -asm "Update changelog"';
                },
                stdout: true
            }
        }
    });

    /****************************************
    *  Sub-tasks of publish task            *
    ****************************************/
    grunt.registerTask('newrelease', "pull and merge develop to master, create and push a new release", [
        'exec:git_checkout:develop', 'exec:git_pull',
        'exec:git_checkout:master', 'exec:git_pull', 'exec:git_merge:develop',
        'exec:git_get_last_tag', 'exec:git_list_changes', '_get_next_tag',
        'exec:git_tag_new', 'exec:git_push:origin:master:true']);

    grunt.registerTask('genchanges', "generate CHANGES.md file", function() {
        file = grunt.option('file'); // --file=path/to/sickrage.github.io/sickrage-news/CHANGES.md
        if (!file)
            grunt.fatal('\tYou must provide a path to CHANGES.md to generate changes.\n' +
                        '\t\tUse --file=path/to/sickrage.github.io/sickrage-news/CHANGES.md');
        grunt.config('changesmd_file', file);
        grunt.task.run(['exec:git_get_last_tag', 'exec:git_list_tags', '_genchanges',
                        'exec:commit_changelog', 'exec:git_push:origin:master'])
    });

    /****************************************
    *  Internal tasks                       *
    *****************************************/
    grunt.registerTask('_get_next_tag', '(internal) do not run', function() {
        function leading_zeros(number) {
            number = parseInt(number);
            number = (number < 10 ? '0' + number : number).toString();
        }

        var last_tag = grunt.config('last_tag');
        if (!last_tag)
            grunt.fatal('internal task');

        last_tag = last_tag.split('v')[1].split('-');
        var last_patch = last_tag[1];
        last_tag = last_tag[0].split('.');

        var d = new Date();
        var year = d.getFullYear().toString();
        var month = leading_zeros(d.getMonth() + 1);
        var day = leading_zeros(d.getDate());
        var patch;

        if (year === last_tag[0] && month === leading_zeros(last_tag[1]) && day === leading_zeros(last_tag[2])) {
            patch = (parseInt(last_patch) + 1).toString();
        } else {
            patch = '1';
        }
        grunt.config('next_tag', ('v' + year + '.' + month + '.' + day + '-' + patch));
    });

    grunt.registerTask('_genchanges', "(internal) do not run", function() {
        // actual generate changes
        var current_tag = grunt.config('last_tag');
        if (!current_tag)
            grunt.fatal('internal task');
        var all_tags = grunt.config('all_tags');
        if (!all_tags)
            grunt.fatal('internal task');

        file = grunt.config('changesmd_file'); // --file=path/to/sickrage.github.io/sickrage-news/CHANGES.md

        contents = "";
        all_tags.reverse().forEach(function(tag) {
            contents += '### ' + tag.tag + '\n';
            contents += '\n';
            if (tag.previous) {
                contents += '[full changelog](https://github.com/SickRage/SickRage/compare/' +
                    tag.previous + '...' + tag.tag + ')\n';
            }
            contents += '\n';
            tag.message.forEach(function (row) {
                contents += '* ' + row + '\n';
            });
            contents += '\n';
        });

        if (contents) {
            grunt.file.write(file, contents);
            return true;
        }
        return false;
    });
};
