'use strict';

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

    grunt.registerTask('travis', 'Alias for "jshint", "mocha" tasks.', function(update) {
        if (!update) {
            grunt.task.run([
                'jshint',
                'mocha'
            ]);
        } else {
            if (process.env.TRAVIS) {
                grunt.log.writeln('Running grunt and updating translations...'.magenta);
                grunt.task.run([
                    // 'exec:git:checkout:master', // should be on 'master' branch
                    'default', // Run default task
                    'update_trans', // Update translations
                    'exec:commit_changed_files:yes', // Determine what we need to commit if needed, stop if nothing to commit.
                    'exec:git:reset --hard', // Reset unstaged changes (to allow for a rebase)
                    'exec:git:checkout:develop', 'exec:git:rebase:master', // FF develop to the updated master
                    'exec:git_push:origin:master develop' // Push master and develop
                ]);
            } else {
                grunt.fatal('This task is only for Travis-CI!');
            }
        }
    });

    grunt.registerTask('update_trans', 'Update translations', function() {
        grunt.log.writeln('Updating translations...'.magenta);
        var tasks = [
            'exec:babel_extract',
            'exec:babel_update',
            // + crowdin
            'exec:babel_compile',
            'po2json'
        ];
        if (process.env.CROWDIN_API_KEY) {
            tasks.splice(2, 0, 'exec:crowdin_upload', 'exec:crowdin_download'); // insert items at index 2
        } else {
            grunt.log.warn('Environment variable `CROWDIN_API_KEY` is not set, not syncing with Crowdin.'.bold);
        }

        grunt.task.run(tasks);
    });

    /****************************************
    *  Admin only tasks                     *
    ****************************************/
    grunt.registerTask('publish', 'ADMIN: Create a new release tag and generate new CHANGES.md', [
        'travis',
        'newrelease', // Pull and merge develop to master, create and push a new release
        'genchanges' // Update CHANGES.md
    ]);

    grunt.registerTask('newrelease', "Pull and merge develop to master, create and push a new release", [
        'exec:git:checkout:develop', 'exec:git:pull', // Pull develop
        'exec:git:checkout:master', 'exec:git:pull', // Pull master
        'exec:git:merge:develop', // Merge develop into master
        'exec:git_get_last_tag', 'exec:git_list_changes', // List changes from since last tag
        '_get_next_tag', 'exec:git_tag_new', // Create new release tag
        'exec:git_push:origin:master:tags', // Push master + tags
        'exec:git:checkout:develop' // Go back to develop
    ]);

    grunt.registerTask('genchanges', "Generate CHANGES.md file", function() {
        var file = grunt.option('file'); // --file=path/to/sickrage.github.io/sickrage-news/CHANGES.md
        if (!file) {
            file = process.env.SICKRAGE_CHANGES_FILE;
        }
        if (file && grunt.file.exists(file)) {
            grunt.config('changesmd_file', file.replace(/\\/g, '/')); // Use forward slashes only.
        } else {
            grunt.fatal('\tYou must provide a path to CHANGES.md to generate changes.\n' +
                '\t\tUse --file=path/to/sickrage.github.io/sickrage-news/CHANGES.md\n' +
                '\t\tor set the path in SICKRAGE_CHANGES_FILE (environment variable)');
        }
        grunt.task.run(['exec:git_list_tags', '_genchanges', 'exec:commit_changelog']);
    });

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
            'git': {
                cmd: function (cmd, branch) {
                    branch = branch ? ' ' + branch : '';
                    return 'git ' + cmd + branch;
                }
            },
            'commit_changed_files': { // Choose what to commit.
                cmd: function(travis) {
                    grunt.config('stop_no_changes', Boolean(travis));
                    return 'git status -s -- locale/ gui/';
                },
                stdout: false,
                callback: function(err, stdout) {
                    stdout = stdout.trim();
                    if (!stdout.length) {
                        grunt.fatal('No changes to commit.', 0);
                    }

                    var commitMsg = [];
                    var commitPaths = [];
                    if (stdout.match(/gui\/.*(vender|core)\.min\.(js|css)$/gm)) {
                        commitMsg.push('Grunt');
                        commitPaths.push('gui/**/vender.min.*');
                        commitPaths.push('gui/**/core.min.*');
                    }
                    if (stdout.match(/locale\/.*(pot|po|mo|json)$/gm)) {
                        commitMsg.push('Update translations');
                        commitPaths.push('locale/');
                    }

                    if (!commitMsg.length || !commitPaths.length) {
                        if (grunt.config('stop_no_changes')) {
                            grunt.fatal('Nothing to commit, aborting', 0);
                        } else {
                            grunt.log.ok('No extra changes to commit'.green);
                        }
                    } else {
                        commitMsg = commitMsg.join(', ');
                        if (process.env.TRAVIS_BUILD_NUMBER) {
                            commitMsg += ' (build ' + process.env.TRAVIS_BUILD_NUMBER + ') [skip ci]';
                        }
                        grunt.config('commit_msg', commitMsg);
                        grunt.config('commit_paths', commitPaths.join(' '));
                        grunt.task.run('exec:commit_combined');
                    }
                }
            },
            'commit_combined': {
                cmd: function() {
                    var message = grunt.config('commit_msg');
                    var paths = grunt.config('commit_paths');
                    if (!message || !paths) {
                        grunt.fatal('Call exec:commit_changed_files instead!');
                    }
                    return 'git add -- ' + paths;
                },
				callback: function(err) {
					if (!err) {
						grunt.task.run('exec:git:commit:-m "' + grunt.config('commit_msg') + '"');
					}
				}
            },
            'git_get_last_tag': {
                cmd: 'git for-each-ref --sort=-refname --count=1 --format "%(refname:short)" refs/tags/v20[0-9][0-9]*',
                stdout: false,
                callback: function(err, stdout) {
                    stdout = stdout.trim();
                    if (/^v\d{4}.\d{1,2}.\d{1,2}.\d+$/.test(stdout)) {
                        grunt.config('last_tag', stdout);
                    } else {
                        grunt.fatal('Could not get the last tag name. We got: ' + stdout);
                    }
                }
            },
            'git_list_changes': {
                cmd: function() { return 'git log --oneline --pretty=format:%s ' + grunt.config('last_tag') + '..HEAD'; },
                stdout: false,
                callback: function(err, stdout) {
                    var commits = stdout.trim()
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
                    var pushCmd = 'git push ' + remote + ' ' + branch;
                    if (tags) {
                        pushCmd += ' --tags';
                    }
                    if (grunt.option('no-push')) {
                        grunt.log.warn('Pushing with --dry-run ...'.magenta);
                        pushCmd += ' --dry-run';
                    }
                    return pushCmd;
                }
            },
            'git_list_tags': {
                cmd: 'git for-each-ref --sort=refname ' +
                        '--format="%(refname:short)|||%(objectname)|||%(contents)\xB6\xB6\xB6" ' +
                        'refs/tags/v20[0-9][0-9]*',
                stdout: false,
                callback: function(err, stdout) {
                    if (!stdout) {
                        grunt.fatal('Git command returned no data.');
                    }
                    if (err) {
                        grunt.fatal('Git command failed to execute.');
                    }
                    var allTags = stdout
                        .replace(/-{5}BEGIN PGP SIGNATURE-{5}(.*\n)+?-{5}END PGP SIGNATURE-{5}\n/g, '')
                        .split('\xB6\xB6\xB6');
                    var foundTags = [];
                    allTags.forEach(function(curTag) {
                        if (curTag.length) {
                            var explode = curTag.split('|||');
                            if (explode[0] && explode[1] && explode[2]) {
                                foundTags.push({
                                    tag: explode[0].trim(),
                                    hash: explode[1].trim(),
                                    message: explode[2].trim().split('\n'),
                                    previous: (foundTags.length ? foundTags.slice(-1)[0].tag : null)
                                });
                            }
                        }
                    });
                    if (foundTags.length) {
                        grunt.config('all_tags', foundTags.reverse()); // LIFO
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
                    var pushCmd = 'git push origin master';
                    if (grunt.option('no-push')) {
                        grunt.log.warn('Pushing with --dry-run ...'.magenta);
                        pushCmd += ' --dry-run';
                    }
                    return ['cd ' + path, 'git commit -asm "Update changelog"', 'git fetch origin', 'git rebase',
                        pushCmd].join(' && ');
                },
                stdout: true
            }
        }
    });

    /****************************************
    *  Internal tasks                       *
    *****************************************/
    grunt.registerTask('_get_next_tag', '(internal) do not run', function() {
        grunt.config.requires('last_tag');
        var lastTag = grunt.config('last_tag');

        var lastPatch = lastTag.match(/[0-9]+$/)[0];
        lastTag = grunt.template.date(lastTag.replace(/^v|-[0-9]*-?$/g, ''), 'yyyy.mm.dd');
        var today = grunt.template.today('yyyy.mm.dd');
        var patch = lastTag === today ? (parseInt(lastPatch) + 1).toString() : '1';

        var nextTag = 'v' + today + '-' + patch;
        grunt.log.ok(('Creating tag ' + nextTag).green);
        grunt.config('next_tag', nextTag);
    });

    grunt.registerTask('_genchanges', "(internal) do not run", function() {
        // actual generate changes
        var allTags = grunt.config('all_tags');
        if (!allTags) {
            grunt.fatal('No tags information was received.');
        }

        var file = grunt.config('changesmd_file'); // --file=path/to/sickrage.github.io/sickrage-news/CHANGES.md
        if (!file) {
            grunt.fatal('Missing file path.');
        }

        var contents = "";
        allTags.forEach(function(tag) {
            contents += '### ' + tag.tag + '\n';
            contents += '\n';
            if (tag.previous) {
                contents += '[full changelog](https://github.com/SickRage/SickRage/compare/' +
                    tag.previous + '...' + tag.tag + ')\n';
            }
            contents += '\n';
            tag.message.forEach(function (row) {
                contents += row
                    // link issue numbers, style links of issues and pull requests
                    .replace(/([\w\d\-.]+\/[\w\d\-.]+)?#(\d+)|https?:\/\/github.com\/([\w\d\-.]+\/[\w\d\-.]+)\/(issues|pull)\/(\d+)/gm,
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
                    .replace(/^\([\w\d\s,.\-+/>]+\)\s/gm, '')
                    // remove commit hashes from start
                    .replace(/^[a-f0-9]{7} /gm, '')
                    // style messages that contain lists
                    .replace(/( {3,}\*)(?!\*)/g, '\n  -')
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
