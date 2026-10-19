'use strict';

module.exports = function (grunt) {
    const CI = Boolean(process.env.CI);
    const bowerJsFiles = {};

    function isAlreadyMinified(filepath) {
        return /\.min\.js$/.test(filepath) || /-min\.js$/.test(filepath);
    }

    // Widgets the slick GUI actually calls, plus their 1.12 internals.
    // Dropped: datepicker, effect.js + effects/*, accordion, tooltip, spinner,
    // droppable, selectable, selectmenu, progressbar.
    const jqueryUiCustomJs = [
        'ui/version.js',
        'ui/widget.js',
        'ui/plugin.js',
        'ui/position.js',
        'ui/data.js',
        'ui/disable-selection.js',
        'ui/focusable.js',
        'ui/form.js',
        'ui/form-reset-mixin.js',
        'ui/ie.js',
        'ui/keycode.js',
        'ui/labels.js',
        'ui/jquery-1-7.js',
        'ui/safe-active-element.js',
        'ui/safe-blur.js',
        'ui/scroll-parent.js',
        'ui/tabbable.js',
        'ui/unique-id.js',
        'ui/escape-selector.js',
        'ui/widgets/mouse.js',
        'ui/widgets/draggable.js',
        'ui/widgets/resizable.js',
        'ui/widgets/controlgroup.js',
        'ui/widgets/checkboxradio.js',
        'ui/widgets/button.js',
        'ui/widgets/menu.js',
        'ui/widgets/autocomplete.js',
        'ui/widgets/dialog.js',
        'ui/widgets/slider.js',
        'ui/widgets/sortable.js',
        'ui/widgets/tabs.js',
    ];

    // Home/manage/history/schedule/addShows/movies/config. Core pages skip these.
    const vendorJsExtra = new Set([
        'isotope',
        'tablesorter',
        'qtip2',
        'imagesloaded',
    ]);

    // Copied to js/lib and loaded from the templates that call them.
    const vendorJsPage = {
        'bootstrap-formhelpers': './sickchill/gui/slick/js/lib/bootstrap-formhelpers.min.js',
        'jquery-tokeninput': './sickchill/gui/slick/js/lib/jquery.tokeninput.min.js',
        'bootstrap3-typeahead': './sickchill/gui/slick/js/lib/bootstrap3-typeahead.min.js',
        'jquery.redirect': './sickchill/gui/slick/js/lib/jquery.redirect.min.js',
    };

    function preferMinJs(filepath) {
        if (!filepath.endsWith('.js') || isAlreadyMinified(filepath)) {
            return filepath;
        }

        const minDot = filepath.replace(/\.js$/, '.min.js');
        if (grunt.file.exists(minDot)) {
            return minDot;
        }

        const minDash = filepath.replace(/\.js$/, '-min.js');
        if (grunt.file.exists(minDash)) {
            return minDash;
        }

        return filepath;
    }

    grunt.registerTask('default', [
        'clean',
        'bower',
        'bower_concat',
        'copy',
        'vendor_js_minify',
        'cssmin',
    ]);

    /****************************************
     *  Admin only tasks                     *
     ****************************************/
    grunt.registerTask('publish', 'ADMIN: Create a new release tag and generate new CHANGES.md', [
        'exec:checkReturnBranch', // Save the branch we are currently on, so we can return here

        // Make sure we have the newest remote changes locally
        'exec:git:checkout:develop', // Switch to develop
        'exec:git:pull', // Pull develop
        'exec:git:checkout:master', // Switch to master
        'exec:git:pull', // Pull master

        // Set up old and new version strings
        '_getLastVersion', // Get last tagged version
        '_getNextVersion', // Get next version to set

        // Start merging and releasing
        'exec:git:merge:develop --strategy-option theirs', // Merge develop into master
        // 'default', // Run default task, grunt
        // 'exec:updateTranslations', // Update translations
        'exec:bumpVersion', // Update version in pyproject.toml
        'exec:gitListChanges', // List changes from since last tag
        'exec:gitListTags', // Get list of tags
        '_genchanges:yes', // Generate changelog
        'exec:commitChangedFiles:yes', // Commit the changelog

        'exec:gitTagNextVersion:yes', // Create new release tag

        'exec:gitPush:origin:master:tags', // Push master + tags
        'exec:pypi', // PBuild and push wheel to pypi

        'exec:git:checkout:develop', // Go back to develop
        'exec:git:merge:master --strategy-option theirs', // Merge master back into develop
        'exec:gitPush:origin:develop:tags', // Push develop + tags

        'exec:checkReturnBranch:true', // Go back to the branch we were on
    ]);

    grunt.registerTask('genchanges', 'Generate CHANGES.md file', () => {
        grunt.task.run(['exec:gitListTags', '_genchanges']);
    });

    grunt.registerTask('reset_publishing', 'reset the repository back to clean master and develop from remote, and remove the local tag created to facilitate easier testing to the changes made here.', () => {
        if (CI) {
            grunt.fatal('This task not for CI!');
            return false;
        }

        grunt.log.writeln('Resetting the local repo back to remote heads for develop and master, and undoing any tags...'.red);
        grunt.task.run([
            'exec:checkReturnBranch', // Save the branch we are currently on, so we can return here
            'exec:git:checkout:master', // Checkout master
            'exec:git:reset --hard:origin/master', // Reset back to remote master
            'exec:git:checkout:develop', // Check out develop
            'exec:git:reset --hard:origin/develop', // Reset back to remote develop
            '_getNextVersion:true', // To set the today string in grunt.config
            'exec:deleteTodayTags', // Delete all local tags matching today's date
            'exec:git:fetch:origin --tags', // Pull tags back from remote
            'exec:checkReturnBranch:true', // Go back to the branch we were on

        ]);
    });

    /****************************************
     *  Task configurations                  *
     ****************************************/
    require('load-grunt-tasks')(grunt); // Loads all grunt tasks matching the ['grunt-*', '@*/grunt-*'] patterns
    grunt.initConfig({
        clean: {
            dist: './dist/',
            bower_components: './bower_components',
            fonts: './sickchill/gui/slick/css/fonts',
            options: {
                force: true,
            },
        },
        bower: {
            install: {
                options: {
                    copy: false,
                },
            },
        },
        bower_concat: {
            all: {
                dest: {
                    js: './dist/bower.js',
                    css: './dist/bower.css',
                },
                // isotope.pkgd.min.js already bundles these; imagesloaded.pkgd.min.js bundles ev-emitter
                exclude: [
                    'outlayer',
                    'masonry-layout',
                    'get-size',
                    'fizzy-ui-utils',
                    'desandro-matches-selector',
                    'ev-emitter',
                ],
                dependencies: {},
                mainFiles: {
                    tablesorter: [
                        'dist/js/jquery.tablesorter.combined.min.js',
                        'dist/js/parsers/parser-metric.min.js',
                        'dist/js/widgets/widget-columnSelector.min.js',
                        'dist/css/theme.blue.min.css',
                    ],
                    bootstrap: [
                        'dist/css/bootstrap.min.css',
                        'dist/js/bootstrap.min.js',
                    ],
                    'bootstrap-formhelpers': [
                        'dist/js/bootstrap-formhelpers.min.js',
                    ],
                    isotope: [
                        'dist/isotope.pkgd.min.js',
                    ],
                    'open-sans-fontface': [
                        '*.css',
                        'fonts/**/*',
                    ],
                    'jqueryui-touch-punch': [
                        'jquery.ui.touch-punch.js',
                    ],
                    jquery: [
                        'dist/jquery.min.js',
                    ],
                    'jquery-ui': jqueryUiCustomJs,
                    underscore: [
                        'underscore-min.js',
                    ],
                    qtip2: [
                        'jquery.qtip.min.js',
                    ],
                    imagesloaded: [
                        'imagesloaded.pkgd.min.js',
                    ],
                    'jquery-backstretch': [
                        'jquery.backstretch.min.js',
                    ],
                    'jquery-confirm': [
                        'jquery.confirm.min.js',
                    ],
                    'bootstrap-hover-dropdown': [
                        'bootstrap-hover-dropdown.min.js',
                    ],
                    'bootstrap3-typeahead': [
                        'bootstrap3-typeahead.min.js',
                    ],
                    'jquery-tokeninput': [
                        'build/jquery.tokeninput.min.js',
                    ],
                },
                callback(mainFiles, name) {
                    const preferred = mainFiles.map(preferMinJs);
                    bowerJsFiles[name] = preferred.filter(filepath => filepath.endsWith('.js') && grunt.file.exists(filepath));
                    return preferred;
                },
                bowerOptions: {
                    relative: false,
                },
            },
        },
        copy: {
            openSans: {
                files: [{
                    expand: true,
                    dot: true,
                    cwd: 'bower_components/open-sans-fontface',
                    src: [
                        'fonts/**/*',
                    ],
                    dest: './sickchill/gui/slick/css/',
                }],
            },
            'fork-awesome': {
                files: [{
                    expand: true,
                    dot: true,
                    cwd: 'bower_components/fork-awesome',
                    src: [
                        'fonts/**/*',
                        'css/**/*.min.css',
                        'css/**/*.css.map',
                    ],
                    dest: './sickchill/gui/slick/',
                }],
            },
            'font-awesome': {
                files: [{
                    expand: true,
                    dot: true,
                    cwd: 'bower_components/font-awesome',
                    src: [
                        'fonts/**/*',
                        'css/**/*.min.css',
                        'css/**/*.css.map',
                    ],
                    dest: './sickchill/gui/slick/',
                }],
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
                        '*.woff2',
                    ],
                    dest: './sickchill/gui/slick/fonts/',
                }],
            },
        },
        // JS vendor minify is vendor_js_minify (skips files that are already .min.js / -min.js)
        cssmin: {
            options: {
                shorthandCompacting: false,
                roundingPrecision: -1,
            },
            bower: {
                files: {
                    './sickchill/gui/slick/css/vendor.min.css': ['./dist/bower.css'],
                },
            },
            core: {
                files: {
                    './sickchill/gui/slick/css/core.min.css': ['./dist/core.css'],
                },
            },
        },
        po2json: {
            messages: {
                options: {
                    format: 'jed',
                    singleFile: true,
                },
                files: [{
                    expand: true,
                    src: 'sickchill/locale/*/LC_MESSAGES/messages.po',
                    dest: '',
                    ext: '', // Workaround for relative files
                }],
            },
        },
        exec: {
            // Translations
            updateTranslations: {cmd: 'poe update_translations'},
            checkReturnBranch: {
                cmd(checkout) {
                    let command = 'git branch --show-current';
                    if (checkout) {
                        command = 'git checkout ' + grunt.config('return_branch') + ' && ' + command;
                    }

                    return command;
                },
                stdout: false,
                callback(error, stdout) {
                    const output = stdout.trim();
                    if (output.length === 0) {
                        grunt.fatal('Could not find out what branch you were on!', 0);
                    }

                    grunt.config('return_branch', output);
                },
            },
            bumpVersion: {
                cmd() {
                    grunt.task.requires('_getNextVersion');
                    return 'poetry version ' + grunt.config('nextVersion');
                },
                callback(error, stdout) {
                    stdout = stdout.trim();
                    if (stdout.length === 0) {
                        grunt.fatal('Failed to bump version!.', 0);
                    }

                    if (!/Bumping version from \d{4}(?:\.\d{1,2}){2}(\.\d*)?/.test(stdout)) {
                        grunt.fatal('Did the version update in pyproject.toml?');
                    }
                },
            },

            // Delete tags from today
            deleteTodayTags: {
                cmd() {
                    grunt.task.requires('_getNextVersion');
                    return 'git tag -d $(git describe --match "' + grunt.config('today') + '*" --abbrev=0 --tags $(git rev-list --tags --max-count=1))';
                },
                stderr: false,
            },

            // Run tests
            test: {cmd: 'yarn run test || npm run test'},

            // Build and push to pypi
            pypi: {cmd: 'poetry publish --build'},

            // Publish/Releases
            git: {
                cmd(cmd, branch) {
                    branch = branch ? ' ' + branch : '';
                    return 'git ' + cmd + branch;
                },
            },
            commitChangedFiles: { // Choose what to commit.
                cmd(ci) {
                    grunt.config('stop_no_changes', Boolean(ci));
                    return 'git status -s -- pyproject.toml sickchill/locale/ sickchill/gui/ CHANGES.md';
                },
                stdout: true,
                callback(error, stdout) {
                    stdout = stdout.trim();
                    if (stdout.length === 0) {
                        grunt.fatal('No changes to commit.', 0);
                    }

                    let commitMessage = [];
                    const commitPaths = [];

                    const isRelease = stdout.match(/pyproject.toml/gm);

                    if (isRelease) {
                        grunt.task.requires('_getNextVersion');
                        commitMessage.push('Release version ' + grunt.config('nextVersion'));
                        commitPaths.push('pyproject.toml');
                    }

                    const changes = stdout.match(/CHANGES.md/gm);
                    if (changes) {
                        commitMessage.push('Update Changelog');
                        commitPaths.push('CHANGES.md');
                    }

                    if (/sickchill\/gui\/.*vendor(?:-core|-extra)?\.min\.(js|css)$/gm.test(stdout)) {
                        commitMessage.push('Grunt');
                        commitPaths.push('sickchill/gui/**/vendor*.min.*');
                    }

                    if (/sickchill\/locale\/.*(pot|po|mo|json)$/gm.test(stdout)) {
                        commitMessage.push('Update translations');
                        commitPaths.push('sickchill/locale/');
                    }

                    if (commitMessage.length === 0 || commitPaths.length === 0) {
                        if (grunt.config('stop_no_changes')) {
                            grunt.fatal('Nothing to commit, aborting', 0);
                        } else {
                            grunt.log.ok('No extra changes to commit'.green);
                        }
                    } else {
                        commitMessage = commitMessage.join(', ');

                        grunt.config('commit_msg', commitMessage);
                        grunt.config('commit_paths', commitPaths.join(' '));
                        grunt.task.run('exec:commitCombined');
                    }
                },
            },
            commitCombined: {
                cmd() {
                    // Grunt.task.requires('commitChangedFiles');

                    const message = grunt.config('commit_msg');
                    const paths = grunt.config('commit_paths');
                    if (!message || !paths) {
                        grunt.fatal('Call exec:commitChangedFiles instead!');
                    }

                    return 'git add -- ' + paths;
                },
                callback(error) {
                    if (!error) {
                        if (CI) { // Workaround for CI (with -m "text" the quotes are within the message)
                            const messageFilePath = 'commit-msg.txt';
                            grunt.file.write(messageFilePath, grunt.config('commit_msg'));
                            grunt.task.run('exec:git:commit:-F ' + messageFilePath);
                        } else {
                            grunt.task.run('exec:git:commit:-m "' + grunt.config('commit_msg') + '"');
                        }
                    }
                },
            },
            gitListChanges: {
                cmd() {
                    grunt.task.requires('_getLastVersion');
                    return 'git log --oneline --first-parent --pretty=format:%s ' + grunt.config('lastVersion') + '..HEAD';
                },
                stdout: false,
                callback(error, stdout) {
                    const commits = stdout.trim().replaceAll(/`/gm, '').replaceAll(/^\([\w\s,.\-+_/>]+\)\s/gm, '').replaceAll(/"/gm, '\\"'); // Removes ` and tag information
                    if (commits) {
                        grunt.config('commits', commits);
                    } else {
                        grunt.fatal('Getting new commit list failed!');
                    }
                },
            },
            gitTagNextVersion: {
                cmd(sign) {
                    grunt.task.requires('_getNextVersion');
                    grunt.task.requires('exec:gitListChanges');

                    const nextVersion = grunt.config('nextVersion');

                    grunt.log.ok(('Creating tag ' + nextVersion).green);
                    sign = sign === 'true' ? '-s ' : '';
                    return 'git tag ' + sign + nextVersion + ' -m "' + grunt.config('commits') + '"';
                },
                stdout: false,
            },
            gitPush: {
                cmd(remote, branch, tags) {
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
                callback(error, stdout, stderr) {
                    grunt.log.write(stderr.replace(process.env.GH_CRED, '[censored]'));
                },
            },
            gitListTags: {
                cmd: 'git for-each-ref --sort=refname --format="%(refname:short)|||%(objectname)|||%(contents)\u00B6\u00B6\u00B6" refs/tags/20[2-9][2-9].[0-9]*.[0-9]*',
                stdout: false,
                callback(error, stdout) {
                    if (!stdout && !error) {
                        grunt.fatal('Git command returned no data.');
                    }

                    if (error) {
                        grunt.fatal('Git command failed to execute: ' + error);
                    }

                    const allTags = stdout
                        .replaceAll(/-{5}BEGIN PGP SIGNATURE-{5}(.*\n)+?-{5}END PGP SIGNATURE-{5}\n/g, '')
                        .split('\u00B6\u00B6\u00B6');
                    const foundTags = [];
                    for (const curTag of allTags) {
                        if (curTag.length > 0) {
                            const explode = curTag.split('|||');
                            if (explode[0] && explode[1] && explode[2]) {
                                foundTags.push({
                                    tag: explode[0].trim(),
                                    hash: explode[1].trim(),
                                    message: explode[2].trim().split('\n'),
                                    previous: (foundTags.length > 0 ? foundTags.at(-1).tag : null),
                                });
                            }
                        }
                    }

                    if (foundTags.length > 0) {
                        grunt.config('all_tags', foundTags.reverse()); // LIFO
                    } else {
                        grunt.fatal('Could not get existing tags information');
                    }
                },
            },
        },
    });

    grunt.registerTask('vendor_js_minify', 'Build vendor-core.min.js and vendor-extra.min.js, skipping already-minified sources', function () {
        const done = this.async();
        const bower = require('bower');
        const UglifyJS = require('uglify-js');
        const dependencyTools = require('grunt-bower-concat/lib/dependencyTools');
        const coreDest = './sickchill/gui/slick/js/vendor-core.min.js';
        const extraDest = './sickchill/gui/slick/js/vendor-extra.min.js';
        const staleDest = './sickchill/gui/slick/js/vendor.min.js';

        function minifyFile(filepath) {
            const src = grunt.file.read(filepath);
            if (isAlreadyMinified(filepath)) {
                return {code: src, skipped: true, srcBytes: src.length, outBytes: src.length};
            }

            const result = UglifyJS.minify(src, {module: false});
            if (result.error) {
                grunt.fatal(filepath + ': ' + result.error);
            }

            return {code: result.code, skipped: false, srcBytes: src.length, outBytes: result.code.length};
        }

        function collectParts(names) {
            const parts = [];
            const used = [];
            let skippedFiles = 0;
            let skippedBytes = 0;
            let uglifiedFiles = 0;
            let uglifiedSrcBytes = 0;
            let uglifiedOutBytes = 0;

            for (const name of names) {
                const files = bowerJsFiles[name] || [];
                if (files.length === 0) {
                    continue;
                }

                used.push(name);
                for (const filepath of files) {
                    const result = minifyFile(filepath);
                    parts.push(result.code);
                    if (result.skipped) {
                        skippedFiles += 1;
                        skippedBytes += result.srcBytes;
                    } else {
                        uglifiedFiles += 1;
                        uglifiedSrcBytes += result.srcBytes;
                        uglifiedOutBytes += result.outBytes;
                    }
                }
            }

            return {parts, used, skippedFiles, skippedBytes, uglifiedFiles, uglifiedSrcBytes, uglifiedOutBytes};
        }

        function writeBundle(dest, collected) {
            if (collected.parts.length === 0) {
                grunt.fatal('vendor_js_minify: no JS files for ' + dest + '. Run bower_concat first.');
            }

            const output = collected.parts.join('\n');
            grunt.file.write(dest, output);
            grunt.log.ok(
                dest + ' (' + output.length + ' bytes, ' + collected.used.join(', ')
                + '): skipped ' + collected.skippedFiles + ' already-min files ('
                + collected.skippedBytes + ' bytes), uglified ' + collected.uglifiedFiles
                + ' files (' + collected.uglifiedSrcBytes + ' -> ' + collected.uglifiedOutBytes + ' bytes)',
            );
        }

        bower.commands.list({map: true}, {offline: true})
            .on('error', error => {
                grunt.fatal(error);
            })
            .on('end', map => {
                const graph = {};
                const resolved = [];
                const unresolved = [];
                if (map.dependencies) {
                    dependencyTools.buildDependencyGraph(undefined, map.dependencies, graph);
                    dependencyTools.resolveDependencyGraph(undefined, resolved, unresolved, graph);
                }

                const names = resolved.length > 0 ? resolved : Object.keys(bowerJsFiles);
                const coreNames = [];
                const extraNames = [];

                for (const name of names) {
                    if (Object.hasOwn(vendorJsPage, name)) {
                        const files = bowerJsFiles[name] || [];
                        const parts = [];
                        for (const filepath of files) {
                            parts.push(minifyFile(filepath).code);
                        }

                        if (parts.length === 0) {
                            grunt.fatal('vendor_js_minify: no JS files for page lib ' + name);
                        }

                        const dest = vendorJsPage[name];
                        const output = parts.join('\n');
                        grunt.file.write(dest, output);
                        grunt.log.ok(dest + ' (' + output.length + ' bytes) from ' + name);
                        continue;
                    }

                    if (vendorJsExtra.has(name)) {
                        extraNames.push(name);
                    } else if (bowerJsFiles[name] && bowerJsFiles[name].length > 0) {
                        coreNames.push(name);
                    }
                }

                writeBundle(coreDest, collectParts(coreNames));
                writeBundle(extraDest, collectParts(extraNames));

                if (grunt.file.exists(staleDest)) {
                    grunt.file.delete(staleDest);
                    grunt.log.ok('removed ' + staleDest);
                }

                done();
            });
    });

    /****************************************
    *  Internal tasks                       *
    *****************************************/
    grunt.registerTask('_getLastVersion', '(internal) do not run', () => {
        const toml = require('toml');

        const file = './pyproject.toml';
        if (!grunt.file.exists(file)) {
            grunt.fatal('Could not find pyproject.toml, cannot proceed');
        }

        const version = toml.parse(grunt.file.read(file)).tool.poetry.version;
        if (version === null) {
            grunt.fatal('Error processing pyproject.toml, cannot proceed');
        }

        grunt.config('lastVersion', version);
    });

    grunt.registerTask('_getNextVersion', '(internal) do not run', skipPost => {
        const date = new Date();
        const year = date.getFullYear();
        const day = date.getDate();
        const month = date.getMonth() + 1;
        const hours = date.getUTCHours();
        const minutes = date.getUTCMinutes();
        const seconds = date.getUTCSeconds();

        let nextVersion = year.toString() + '.' + month.toString().padStart(2 - month.length, '0') + '.' + day.toString().padStart(2 - day.length, '0');
        grunt.config('today', nextVersion); // Needed for resetting failed publishing.

        if (skipPost) {
            return;
        }

        grunt.task.requires('_getLastVersion');

        const lastVersion = grunt.config('lastVersion');

        if (nextVersion === lastVersion) {
            grunt.log.writeln('Let\'s only release once a day, or semver is broken. We can fix this when we do away with grunt');
            nextVersion += '.' + hours + minutes + seconds;
        }

        grunt.config('nextVersion', nextVersion);
    });

    grunt.registerTask('_genchanges', '(internal) do not run', isRelease => {
        // Actual generate changes
        grunt.task.requires('exec:gitListTags');

        const allTags = grunt.config('all_tags');
        if (!allTags) {
            grunt.fatal('No tags information was received.');
        }

        const file = grunt.config('changesmd_file', './CHANGES.md');
        if (!grunt.file.exists(file)) {
            grunt.fatal('Specified CHANGES file does not exist: ' + file);
        }

        function processCommit(row) {
            return row
            // Link issue n return numbers, style links of issues and pull requests

                .replaceAll(/([\w\-.]+\/[\w\-.]+)?#(\d+)|https?:\/\/github.com\/([\w\-.]+\/[\w\-.]+)\/(issues|pull)\/(\d+)/gm,
                    (all, repoL, numberL, repoR, typeR, numberR) => {
                        if (numberL) { // RepoL, numL = user/repo#1234 style
                            return '[' + (repoL ? repoL : '') + '#' + numberL + '](https://github.com/' + (repoL ? repoL : 'SickChill/SickChill') + '/issues/' + numberL + ')';
                        }

                        if (numberR) { // RepoR, type, numR = https://github/user/repo/issues/1234 style
                            return '[#' + numberR + ']' + '(https://github.com/' + repoR + '/' + typeR + '/' + numberR + ')';
                        }
                    })
                // Shorten and link commit hashes
                .replaceAll(/([a-f\d]{40}(?![a-f\d]))/g, sha1 => '[' + sha1.slice(0, 7) + '](https://github.com/SickChill/SickChill/commit/' + sha1 + ')')
                // Remove tag information
                .replaceAll(/^\([\w\s,.\-+/>]+\)\s/gm, '')
                // Remove commit hashes from start
                .replaceAll(/^[a-f\d]{7} /gm, '')
                // Style messages that contain lists
                .replaceAll(/( {3,}\*)(?!\*)/g, '\n  -')
                // Escapes markdown __ tags
                .replaceAll(/__/gm, '\\_\\_')
                // Add * to the first line only
                .replace(/^(\w)/, '* $1')
                .replaceAll(/^.*merge branch '(develop|master)'.*$/gim, '');
        }

        function processArray(array, output) {
            for (const row of new Set(array)) {
                const result = processCommit(row);
                if (result.length > 3) {
                    output += result;
                    output += '\n';
                }
            }

            if (output) {
                output += '\n';
            }

            return output;
        }

        let contents = '';

        if (isRelease) {
            grunt.task.requires('_getLastVersion');
            grunt.task.requires('_getNextVersion');
            grunt.task.requires('exec:gitListChanges');

            const lastVersion = grunt.config('lastVersion');
            const nextVersion = grunt.config('nextVersion');

            if (!nextVersion) {
                grunt.fatal('Can not generate changelog for a release without the next version information!');
            }

            if (!lastVersion) {
                grunt.fatal('Can not generate changelog for a release without the last version information!');
            }

            contents += '### ' + nextVersion + '\n';
            contents += '\n';
            contents += '[full changelog](https://github.com/SickChill/SickChill/compare/' + lastVersion + '...' + nextVersion + ')\n';
            contents += '\n';
            const commits = grunt.config('commits');

            contents = processArray(commits, contents);
        }

        for (const tag of allTags) {
            contents += '### ' + tag.tag + '\n';
            contents += '\n';
            if (tag.previous) {
                contents += '[full changelog](https://github.com/SickChill/SickChill/compare/' + tag.previous + '...' + tag.tag + ')\n';
                contents += '\n';
            }

            contents = processArray(tag.message, contents);
        }

        if (contents) {
            grunt.file.write(file, contents.replace(/\n*$/, '\n'));
            return true;
        }

        grunt.fatal('Received no contents to write to file, aborting');
    });
};
