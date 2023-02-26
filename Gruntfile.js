'use strict';

module.exports = function(grunt) {
    const CI = Boolean(process.env.CI);

    grunt.registerTask('default', [
        'clean',
        'bower',
        'bower_concat',
        'copy',
        'uglify',
        'cssmin'
    ]);

    grunt.registerTask('auto_update_trans', 'Update translations on master and push to master & develop', function() {
        if (!CI) {
            grunt.fatal('This task is only for CI!');
            return false;
        }
        grunt.log.writeln('Running grunt and updating translations...'.magenta);
        grunt.task.run([
            'exec:git:checkout:master',
            'default', // Run default task
            'exec:update_translations', // Update translations
            'exec:commit_changed_files:yes', // Determine what we need to commit if needed, stop if nothing to commit.
            'exec:git:reset --hard', // Reset unstaged changes (to allow for a rebase)
            'exec:git:checkout:develop', // Checkout develop
            'exec:git:rebase:master', // FF develop to the updated master
            'exec:git_push:origin:master develop' // Push master and develop
        ]);
    });

    /****************************************
    *  Admin only tasks                     *
    ****************************************/
    grunt.registerTask('publish', 'ADMIN: Create a new release tag and generate new CHANGES.md', [
        // 'exec:test', // Run tests
        'newrelease', // Pull and merge develop to master, create and push a new release
        'genchanges' // Update CHANGES.md
    ]);

    grunt.registerTask('reset_publishing', 'reset the repository back to clean master and develop from remote, and remove the local tag created to facilitate easier testing to the changes made here.', function() {
        if (CI) {
            grunt.fatal('This task not for CI!');
            return false;
        }
        grunt.log.writeln('Resetting the local repo back to remote heads for develop and master, and undoing any tags...'.red);
        grunt.task.run([
            'exec:check_return_branch', // Save the branch we are currently on, so we can return here
            'exec:git:checkout:master', // Checkout master
            'exec:git:reset --hard:origin/master', // Reset back to remote master
            'exec:git:checkout:develop', // Check out develop
            'exec:git:reset --hard:origin/develop',  // Reset back to remote develop
            '_get_next_version:true', // To set the today string in grunt.config
            'exec:delete_today_tags', // Delete all local tags matching today's date
            'exec:git:fetch:origin --tags', // Pull tags back from remote
            'exec:check_return_branch:true', // Go back to the branch we were on

        ]);
    });
    grunt.registerTask('newrelease', "Pull and merge develop to master, create and push a new release", [
        // Make sure we have the newest remote changes locally
        'exec:git:checkout:develop', // Switch to develop
        'exec:git:pull', // Pull develop
        'exec:git:checkout:master', // Switch to master
        'exec:git:pull', // Pull master

        // Set up old and new version strings
        '_get_last_version', // Get last tagged version
        '_get_next_version', // Get next version to set

        // Start merging and releasing
        'exec:git:merge:develop --strategy-option theirs', // Merge develop into master
        'exec:bump_version', // Update version in pyproject.toml
        'exec:commit_changed_files:yes', // Commit the new changed version
        'exec:git_list_changes', // List changes from since last tag
        'exec:git_tag_next_version', // Create new release tag
        'exec:git_push:origin:master:tags', // Push master + tags
        'exec:git:checkout:develop', // Go back to develop
        'exec:git:merge:master --strategy-option theirs', // Merge master back into develop
        'exec:git_push:origin:develop:tags', // Push develop + tags
    ]);

    grunt.registerTask('genchanges', "Generate CHANGES.md file", function() {
        let file = grunt.option('file'); // --file=path/to/sickchill.github.io/sickchill-news/CHANGES.md
        if (!file) {
            file = process.env.SICKCHILL_CHANGES_FILE;
        }
        if (file && grunt.file.exists(file)) {
            grunt.config('changesmd_file', file.replace(/\\/g, '/')); // Use forward slashes only.
        } else {
            grunt.fatal('\tYou must provide a path to CHANGES.md to generate changes.\n' +
                '\t\tUse --file=path/to/sickchill.github.io/sickchill-news/CHANGES.md\n' +
                '\t\tor set the path in SICKCHILL_CHANGES_FILE (environment variable)');
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
            fonts: './sickchill/gui/slick/css/fonts',
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
                        'dist/js/jquery.tablesorter.combined.min.js',
                        'dist/js/parsers/parser-metric.min.js',
                        'dist/js/widgets/widget-columnSelector.min.js',
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
                    "open-sans-fontface": [
                        "*.css",
                        "fonts/**/*"
                    ],
                    "jqueryui-touch-punch": [
                        "jquery.ui.touch-punch.min.js"
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
                    cwd: 'bower_components/open-sans-fontface',
                    src: [
                        'fonts/**/*'
                    ],
                    dest: './sickchill/gui/slick/css/'
                }]
            },
            'fork-awesome': {
                files: [{
                    expand: true,
                    dot: true,
                    cwd: 'bower_components/fork-awesome',
                    src: [
                        'fonts/**/*',
                        'css/**/*.min.css',
                        'css/**/*.css.map'
                    ],
                    dest: './sickchill/gui/slick/'
                }]
            },
            'font-awesome': {
                files: [{
                    expand: true,
                    dot: true,
                    cwd: 'bower_components/font-awesome',
                    src: [
                        'fonts/**/*',
                        'css/**/*.min.css',
                        'css/**/*.css.map'
                    ],
                    dest: './sickchill/gui/slick/'
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
                    dest: './sickchill/gui/slick/fonts/'
                }]
            }
        },
        uglify: {
            bower: {
                files: {
                    './sickchill/gui/slick/js/vendor.min.js': ['./dist/bower.js']
                }
            },
            core: {
                files: {
                    './sickchill/gui/slick/js/core.min.js': ['./sickchill/gui/slick/js/core.js']
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
                    './sickchill/gui/slick/css/vendor.min.css': ['./dist/bower.css']
                }
            },
            core: {
                files: {
                    './sickchill/gui/slick/css/core.min.css': ['./dist/core.css']
                }
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
                    src: 'sickchill/locale/*/LC_MESSAGES/messages.po',
                    dest: '',
                    ext: '' // workaround for relative files
                }]
            }
        },
        exec: {
            // Translations
            'update_translations': {cmd: 'poe update_translations'},
            'check_return_branch': {
                cmd: function (go_back) {
                    let command = 'git branch --show-current'
                    if (Boolean(go_back)) {
                         command = 'git checkout ' + grunt.config('return_branch') + ' && ' + command;
                    }
                    return command;
                },
                stdout: false,
                callback: function(err, stdout) {
                    stdout = stdout.trim();
                    if (!stdout.length) {
                        grunt.fatal('Could not find out what branch you were on!', 0);
                    }
                    grunt.config('return_branch', stdout);
                },
            },
            'bump_version': {
                cmd: function () {
                    return 'poetry version ' + grunt.config('next_version');
                },
                callback: function(err, stdout) {
                    stdout = stdout.trim();
                    if (!stdout.length) {
                        grunt.fatal('No changes to commit.', 0);
                    }
                    if (!stdout.match(/Bumping version from \d{4}\.\d{1,2}\.\d{1,2}(\.\d*)?/)) {
                        grunt.fatal('Did the version update in pyproject.toml?')
                    }
                }
            },

            // delete tags from today
            'delete_today_tags': {
                cmd: function () {
                    return 'git tag -d $(git describe --match "' + grunt.config('today') + '*" --abbrev=0 --tags $(git rev-list --tags --max-count=1))'
                },
                stderr: false
            },

            // Run tests
            'test': {cmd: 'yarn run test || npm run test'},

            // Publish/Releases
            'git': {
                cmd: function (cmd, branch) {
                    branch = branch ? ' ' + branch : '';
                    return 'git ' + cmd + branch;
                }
            },
            'commit_changed_files': { // Choose what to commit.
                cmd: function(ci) {
                    grunt.config('stop_no_changes', Boolean(ci));
                    return 'git status -s -- pyproject.toml sickchill/locale/ sickchill/gui/';
                },
                stdout: false,
                callback: function(err, stdout) {
                    stdout = stdout.trim();
                    if (!stdout.length) {
                        grunt.fatal('No changes to commit.', 0);
                    }

                    let commitMsg = [];
                    let commitPaths = [];

                    let isRelease = stdout.match(/pyproject.toml/gm)

                    if (isRelease) {
                        commitMsg.push('Release version ' + grunt.config('next_version'));
                        commitPaths.push('pyproject.toml');
                    }
                    if (stdout.match(/sickchill\/gui\/.*(vendor|core)\.min\.(js|css)$/gm)) {
                        if (!isRelease) {
                            commitMsg.push('Grunt');
                        }
                        commitPaths.push('sickchill/gui/**/vendor.min.*');
                        commitPaths.push('sickchill/gui/**/core.min.*');
                    }
                    if (stdout.match(/sickchill\/locale\/.*(pot|po|mo|json)$/gm)) {
                        if (!isRelease) {
                            commitMsg.push('Update translations');
                        }
                        commitPaths.push('sickchill/locale/');
                    }

                    if (!commitMsg.length || !commitPaths.length) {
                        if (grunt.config('stop_no_changes')) {
                            grunt.fatal('Nothing to commit, aborting', 0);
                        } else {
                            grunt.log.ok('No extra changes to commit'.green);
                        }
                    } else {
                        commitMsg = commitMsg.join(', ');
                        if (process.env.GITHUB_RUN_ID && !isRelease) {
                            commitMsg += ' (build ' + process.env.GITHUB_RUN_ID + ') [skip ci]';
                        }

                        grunt.config('commit_msg', commitMsg);
                        grunt.config('commit_paths', commitPaths.join(' '));
                        grunt.task.run('exec:commit_combined');
                    }
                }
            },
            'commit_combined': {
                cmd: function() {
                    const message = grunt.config('commit_msg');
                    const paths = grunt.config('commit_paths');
                    if (!message || !paths) {
                        grunt.fatal('Call exec:commit_changed_files instead!');
                    }
                    return 'git add -- ' + paths;
                },
                callback: function(err) {
                    if (!err) {
                        if (!CI) {
                            grunt.task.run('exec:git:commit:-m "' + grunt.config('commit_msg') + '"');
                        } else { // Workaround for CI (with -m "text" the quotes are within the message)
                            const msgFilePath = 'commit-msg.txt';
                            grunt.file.write(msgFilePath, grunt.config('commit_msg'));
                            grunt.task.run('exec:git:commit:-F ' + msgFilePath);
                        }
                    }
                }
            },
            'git_list_changes': {
                cmd: function() { return 'git log --oneline --first-parent --pretty=format:%s ' + grunt.config('last_version') + '..HEAD'; },
                stdout: false,
                callback: function(err, stdout) {
                    let commits = stdout.trim()
                        .replace(/`/gm, '').replace(/^\([\w\s,.\-+_/>]+\)\s/gm, '').replace(/"/gm, '\\"');  // removes ` and tag information
                    if (commits) {
                        grunt.config('commits', commits);
                    } else {
                        grunt.fatal('Getting new commit list failed!');
                    }
                }
            },
            'git_tag_next_version': {
                cmd: function (sign) {
                    const next_version = grunt.config('next_version');
                    grunt.log.ok(('Creating tag ' + next_version).green);
                    sign = sign !== "true" ? '' : '-s ';
                    return 'git tag ' + sign + next_version + ' -m "' + grunt.config('commits') + '"';
                },
                stdout: false
            },
            'git_push': {
                cmd: function (remote, branch, tags) {
                    let pushCmd = 'git push ' + remote + ' ' + branch;
                    if (tags) {
                        pushCmd += ' --tags';
                    }
                    if (grunt.option('no-push')) {
                        grunt.log.warn('Pushing with --dry-run ...'.magenta);
                        pushCmd += ' --dry-run';
                    }
                    return pushCmd;
                },
                stderr: false,
                callback: function(err, stdout, stderr) {
                    grunt.log.write(stderr.replace(process.env.GH_CRED, '[censored]'));
                }
            },
            'git_list_tags': {
                cmd: 'git for-each-ref --sort=refname --format="%(refname:short)|||%(objectname)|||%(contents)\xB6\xB6\xB6" refs/tags/20[0-9][0-9].[0-9][0-9].[0-9][0-9]*',
                stdout: false,
                callback: function(err, stdout) {
                    if (!stdout) {
                        grunt.fatal('Git command returned no data.');
                    }
                    if (err) {
                        grunt.fatal('Git command failed to execute.');
                    }
                    let allTags = stdout
                        .replace(/-{5}BEGIN PGP SIGNATURE-{5}(.*\n)+?-{5}END PGP SIGNATURE-{5}\n/g, '')
                        .split('\xB6\xB6\xB6');
                    let foundTags = [];
                    allTags.forEach(function(curTag) {
                        if (curTag.length) {
                            let explode = curTag.split('|||');
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
                    const file = grunt.config('changesmd_file');
                    if (!file) {
                        grunt.fatal('Missing file path.');
                    }
                    let path = file.slice(0, -25); // slices 'sickchill-news/CHANGES.md' (len=25)
                    if (!path) {
                        grunt.fatal('path = "' + path + '"');
                    }
                    let pushCmd = 'git push origin master';
                    if (grunt.option('no-push')) {
                        grunt.log.warn('Pushing with --dry-run ...'.magenta);
                        pushCmd += ' --dry-run';
                    }
                    return ['cd ' + path, 'git commit -asm "Update changelog"', 'git fetch origin', 'git rebase',
                        pushCmd].join(' && ');
                },
                stdout: true
            },
        }
    });

    /****************************************
    *  Internal tasks                       *
    *****************************************/
    grunt.registerTask('_get_last_version', '(internal) do not run', function() {
        const toml = require('toml');

        const file = './pyproject.toml';
        if (!grunt.file.exists(file)) {
            grunt.fatal("Could not find pyproject.toml, cannot proceed");
        }

        const version = toml.parse(grunt.file.read(file)).tool.poetry.version;
        if (version === null) {
            grunt.fatal("Error processing pyproject.toml, cannot proceed")
        }
        grunt.config('last_version', version)
    });

    grunt.registerTask('_get_next_version', '(internal) do not run', function(skip_post) {
        const date_object = new Date();
        const year = date_object.getFullYear();
        const day = date_object.getDate();
        const month = date_object.getMonth() + 1;
        const hours = date_object.getUTCHours();
        const minutes = date_object.getUTCMinutes();
        const seconds = date_object.getUTCSeconds();

        let next_version = year.toString() + '.' + month.toString().padStart(2-month.length, "0") + '.' + day.toString().padStart(2-day.length, "0")
        grunt.config('today', next_version); // Needed for resetting failed publishing.

        if (Boolean(skip_post)) {
            return
        }

        const last_version = grunt.config('last_version');
        if (last_version === undefined || !last_version.length) {
            grunt.fatal('Must call _get_last_version first!');
        }

        if (next_version === last_version) {
            grunt.fatal('Let\'s only release once a day, or semver is broken. We can fix this when we do away with grunt')
            next_version += '.' + hours + minutes + seconds
        }

        grunt.config('next_version', next_version);
    });

    grunt.registerTask('_genchanges', "(internal) do not run", function() {
        // actual generate changes
        const allTags = grunt.config('all_tags');
        if (!allTags) {
            grunt.fatal('No tags information was received.');
        }

        const file = grunt.config('changesmd_file'); // --file=path/to/sickchill.github.io/sickchill-news/CHANGES.md
        if (!file) {
            grunt.fatal('Missing file path.');
        }

        let contents = "";
        allTags.forEach(function(tag) {
            contents += '### ' + tag.tag + '\n';
            contents += '\n';
            if (tag.previous) {
                contents += '[full changelog](https://github.com/SickChill/SickChill/compare/' +
                    tag.previous + '...' + tag.tag + ')\n';
            }
            contents += '\n';
            tag.message.forEach(function (row) {
                contents += row
                    // link issue n return 'git tag ' + grunt.config('next_version') + ' -sm "' + grunt.config('commits') + '"';umbers, style links of issues and pull requests
                    .replace(/([\w\-.]+\/[\w\-.]+)?#(\d+)|https?:\/\/github.com\/([\w\-.]+\/[\w\-.]+)\/(issues|pull)\/(\d+)/gm,
                        function(all, repoL, numL, repoR, typeR, numR) {
                            if (numL) { // repoL, numL = user/repo#1234 style
                                return '[' + (repoL ? repoL : '') + '#' + numL + '](https://github.com/' +
                                (repoL ? repoL : 'SickChill/SickChill') + '/issues/' + numL + ')';
                            } else if (numR) { // repoR, type, numR = https://github/user/repo/issues/1234 style
                                return '[#' + numR + ']' + '(https://github.com/' +
                                    repoR + '/' + typeR + '/' + numR + ')';
                            }
                    })
                    // shorten and link commit hashes
                    .replace(/([a-f\d]{40}(?![a-f\d]))/g, function(sha1) {
                        return '[' + sha1.substring(0, 7) + '](https://github.com/SickChill/SickChill/commit/' + sha1 + ')';
                    })
                    // remove tag information
                    .replace(/^\([\w\s,.\-+/>]+\)\s/gm, '')
                    // remove commit hashes from start
                    .replace(/^[a-f\d]{7} /gm, '')
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
