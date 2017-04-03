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
        if(process.env.CROWDIN_API_KEY) {
            tasks.splice(2, 0, 'exec:crowdin_upload', 'exec:crowdin_download'); // insert items at index 2
        } else {
            grunt.log.warn('WARNING: Env variable `CROWDIN_API_KEY` is not set, not syncing with Crowdin.');
        }

        grunt.task.run(tasks);
    });
    /****************************************
    *  Admin only                           *
    ****************************************/
    grunt.registerTask('publish', 'create a release tag and generate CHANGES.md\n(alias for newrelease and genchanges)', [
        'travis',
        // 'update_trans', // blocks git pull in newrelease
        'newrelease',
        'genchanges'
    ]);

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
        'bower_concat': {
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
                '!./gui/slick/js/**/*.min.js' // We use this because ignores doesn't seem to work :(
            ]
        },
        mocha: {
            all: {
                src: ['tests/mocha/testrunner.html']
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
            'babel_extract': {cmd: 'python setup.py extract_messages'},
            'babel_update': {cmd: 'python setup.py update_catalog'},
            'crowdin_upload': {cmd: 'crowdin-cli-py upload sources'},
            'crowdin_download': {cmd: 'crowdin-cli-py download'},
            'babel_compile': {cmd: 'python setup.py compile_catalog'},

            // Publish/Releases
            'git_checkout': {
                cmd: function (b) { return 'git checkout ' + b; }
            },
            'git_pull': {
                cmd: 'git pull'
            },
            'git_merge': {
                cmd: function (b) { return 'git merge ' + b; }
            },
            'git_get_last_tag': {
                cmd: 'git for-each-ref --sort=-refname --count=1 --format "%(refname:short)" refs/tags',
                stdout: false,
                callback: function(err, stdout) {
                    if (/v\d{4}\.\d{2}\.\d{2}-\d+/.test(stdout.trim())) {
                        grunt.config('last_tag', stdout.trim());
                    } else {
                        grunt.fatal('Could not get the last tag name. We got: ' + stdout.trim());
                    }
                }
            },
            'git_list_changes': {
                cmd: function() { return 'git log --oneline ' + grunt.config('last_tag') + '..HEAD'; },
                stdout: false,
                callback: function(err, stdout) {
                    var commits = stdout.replace(/^[a-f0-9]{9}\s/gm, '').trim()  // removes commit hashes
                        .replace(/`/gm, '').replace(/^\([\w\d\s,.\-+_/>]+\)\s/gm, '');  // removes ` and tag information
                    if (commits) {
                        grunt.config('commits', commits);
                    } else {
                        grunt.fatal('Getting new commit list failed!');
                    }
                }
            },
            'git_tag_new': {
                cmd: function (sign) {
                    sign = sign !== "true" ? '' : '-s ';
                    return 'git tag ' + sign + grunt.config('next_tag') + ' -m "' + grunt.config('commits') + '"';
                },
                stdout: false
            },
            'git_push': {
                cmd: function (remote, branch, tags) {
                    return 'git push ' + remote + ' ' + branch + (tags === 'true'?' --tags':'');
                }
            },
            'git_list_tags': {
                cmd: 'git for-each-ref --sort=refname --format="%(refname:short)|||%(objectname)|||%(contents)@@@" refs/tags',
                stdout: false,
                callback: function(err, stdout) {
                    if (!stdout) {
                        grunt.fatal('Git command returned no data.');
                    }
                    if (err) {
                        grunt.fatal('Git command failed to execute.');
                    }
                    var allTags = stdout.replace(/-{5}BEGIN PGP SIGNATURE-{5}(.*\n)+?-{5}END PGP SIGNATURE-{5}\n/g, '').split('@@@');
                    var foundTags = [];
                    for (var i = 0; i < allTags.length; i++) {
                        if (allTags[i].length) {
                            var explode = allTags[i].split('|||');
                            if (explode[0] && explode[1] && explode[2]) {
                                foundTags.push({
                                    tag: explode[0].trim(),
                                    hash: explode[1].trim(),
                                    message: explode[2].trim().split('\n'),
                                    previous: (foundTags.length ? foundTags[foundTags.length - 1].tag : null)
                                });
                            }
                        }
                    }
                    if (foundTags.length) {
                        grunt.config('all_tags', foundTags);
                    } else {
                        grunt.fatal('Could not get existing tags information');
                    }
                }
            },
            'commit_changelog': {
                cmd: function() {
                    var file = grunt.config('changesmd_file');
                    if (!file) {
                        grunt.fatal('Missing file path.');
                    }
                    var path = file.slice(0, -24); // slices 'sickrage-news/CHANGES.md' (len=24)
                    if (!path) {
                        grunt.fatal('path = "' + path + '"');
                    }
                    return 'cd ' + path + ' && git commit -asm "Update changelog"' +
                        ' && git fetch origin && git rebase && git push origin master';
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
        'exec:git_tag_new', 'exec:git_push:origin:master:true', 'exec:git_checkout:develop']);

    grunt.registerTask('genchanges', "generate CHANGES.md file", function() {
        var file = grunt.option('file'); // --file=path/to/sickrage.github.io/sickrage-news/CHANGES.md
        if (!file) {
            file = process.env.SICKRAGE_CHANGES_FILE;
        }
        if (file && grunt.file.exists(file)) {
            grunt.config('changesmd_file', file.replace(/\\/g, '/')); // Use forward slashes only.
        } else {
            grunt.fatal('\tYou must provide a path to CHANGES.md to generate changes.\n' +
                '\t\tUse --file=path/to/sickrage.github.io/sickrage-news/CHANGES.md');
        }
        grunt.task.run(['exec:git_get_last_tag', 'exec:git_list_tags', '_genchanges',
                        'exec:commit_changelog']);
    });

    /****************************************
    *  Internal tasks                       *
    *****************************************/
    grunt.registerTask('_get_next_tag', '(internal) do not run', function() {
        function leadingZeros(number) {
            return ('0' + parseInt(number)).slice(-2);
        }
        var lastTag = grunt.config('last_tag');
        if (!lastTag) {
            grunt.fatal('internal task');
        }

        lastTag = lastTag.split('v')[1].split('-');
        var lastPatch = lastTag[1];
        lastTag = lastTag[0].split('.');

        var d = new Date();
        var year = d.getFullYear().toString();
        var month = leadingZeros(d.getMonth() + 1);
        var day = leadingZeros(d.getDate());
        var patch = '1';

        if (year === lastTag[0] && month === leadingZeros(lastTag[1]) && day === leadingZeros(lastTag[2])) {
            patch = (parseInt(lastPatch) + 1).toString();
        }
        var nextTag = 'v' + year + '.' + month + '.' + day + '-' + patch;
        grunt.log.writeln('Creating tag ' + nextTag);
        grunt.config('next_tag', nextTag);
    });

    grunt.registerTask('_genchanges', "(internal) do not run", function() {
        // actual generate changes
        var currentTag = grunt.config('last_tag');
        if (!currentTag) {
            grunt.fatal('No current tag information was received.');
        }
        var allTags = grunt.config('all_tags');
        if (!allTags) {
            grunt.fatal('No tags information was received.');
        }

        var file = grunt.config('changesmd_file'); // --file=path/to/sickrage.github.io/sickrage-news/CHANGES.md
        if (!file) {
            grunt.fatal('Missing file path.');
        }

        var contents = "";
        allTags.reverse().forEach(function(tag) {
            contents += '### ' + tag.tag + '\n';
            contents += '\n';
            if (tag.previous) {
                contents += '[full changelog](https://github.com/SickRage/SickRage/compare/' +
                    tag.previous + '...' + tag.tag + ')\n';
            }
            contents += '\n';
            tag.message.forEach(function (row) {
                contents += row
                    // link issue numbers, style links it issues and pull requests
                    .replace(/([\w\d\-_.]+[/]{1}[\w\d\-_.]+)?#([0-9]+)|https?:\/\/github.com\/([\w\d\-_.]+[/]{1}[\w\d\-_.]+)\/(issues|pull)\/([0-9]+)/gm,
                        function(all, repoL, numL, repoR, typeR, numR) {
                            if (numL) { // repoL, numL = user/repo#1234 style
                                return '[' + (repoL ? repoL : '') + '#' + numL + '](https://github.com/' +
                                (repoL ? repoL : 'SickRage/SickRage') + '/issues/' + numL + ')';
                            } else if (numR) { // repoR, type, numR = https://github/user/repo/issues/1234 style
                                return '[#' + numR + ']' + '(https://github.com/' +
                                    repoR + '/' + typeR + '/' + numR + ')';
                            }
                    })
                    // shorten and link commit hashes
                    .replace(/([a-f0-9]{40}(?![a-f0-9]))/g, function(sha1) {
                        return '[' + sha1.substr(0, 7) + '](https://github.com/SickRage/SickRage/commit/' + sha1 + ')';
                    })
                    // remove tag information
                    .replace(/^\([\w\d\s,.\-+_/>]+\)\s/gm, '')
                    // remove commit hashes from start
                    .replace(/^[a-f0-9]{7} /gm, '')
                    // style messages that contain lists
                    .replace(/( {3,}\*{1})(?!\*)/g, '\n  -')
                    // style messages that contain multiple lines
                    .replace(/( {3,}\*{1})(?!\*)/g, '\n  -')
                    // escapes markdown __ tags
                    .replace(/__/gm, '\\_\\_')
                    // add * to the first line only
                    .replace(/^(\w)/, '* $1');

                contents += '\n';
            });
            contents += '\n';
        });

        if (contents) {
            grunt.file.write(file, contents);
            return true;
        } else {
            grunt.fatal('Received no contents to write to file, aborting');
        }
    });
};
