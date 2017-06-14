module.exports = function(grunt) {
    const isTravis = Boolean(process.env.TRAVIS);

    grunt.registerTask('default', [
        'clean',
        'bower',
        'bower_concat',
        'copy',
        'uglify',
        'sass',
        'cssmin'
    ]);

    grunt.registerTask('ci', 'Alias for travis tasks.', () => {
        if (isTravis) {
            grunt.log.writeln('Running grunt and updating translations...'.magenta);
            grunt.task.run([
                'exec:git:checkout:master',
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
    });

    grunt.registerTask('update_trans', 'Update translations', () => {
        grunt.log.writeln('Updating translations...'.magenta);
        const tasks = [
            'exec:babel_extract',
            'exec:babel_update',
            // + crowdin
            'exec:babel_compile',
            'po2json'
        ];
        if (process.env.CROWDIN_API_KEY) {
            tasks.splice(2, 0, 'exec:crowdin_upload', 'exec:crowdin_download'); // Insert items at index 2
        } else {
            grunt.log.warn('Environment variable `CROWDIN_API_KEY` is not set, not syncing with Crowdin.'.bold);
        }

        grunt.task.run(tasks);
    });

    /*
    *  Admin only tasks
    */
    grunt.registerTask('publish', 'ADMIN: Create a new release tag and generate new CHANGES.md', [
        'ci',
        'newrelease', // Pull and merge develop to master, create and push a new release
        'genchanges' // Update CHANGES.md
    ]);

    grunt.registerTask('newrelease', 'Pull and merge develop to master, create and push a new release', [
        'exec:git:checkout:develop', 'exec:git:pull', // Pull develop
        'exec:git:checkout:master', 'exec:git:pull', // Pull master
        'exec:git:merge:develop', // Merge develop into master
        'exec:git_get_last_tag', 'exec:git_list_changes', // List changes from since last tag
        '_get_next_tag', 'exec:git_tag_new', // Create new release tag
        'exec:git_push:origin:master:tags', // Push master + tags
        'exec:git:checkout:develop' // Go back to develop
    ]);

    grunt.registerTask('genchanges', 'Generate CHANGES.md file', () => {
        let file = grunt.option('file'); // --file=path/to/sickrage.github.io/sickrage-news/CHANGES.md
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

    /*
    *  Task configurations
    */
    require('load-grunt-tasks')(grunt); // Loads all grunt tasks matching the ['grunt-*', '@*/grunt-*'] patterns
    grunt.initConfig({
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
                    ext: '' // Workaround for relative files
                }]
            }
        },
        exec: {
            // Translations
            babel_extract: {cmd: 'python setup.py extract_messages'}, // eslint-disable-line camelcase
            babel_update: {cmd: 'python setup.py update_catalog'}, // eslint-disable-line camelcase
            crowdin_upload: {cmd: 'crowdin-cli-py upload sources'}, // eslint-disable-line camelcase
            crowdin_download: {cmd: 'crowdin-cli-py download'}, // eslint-disable-line camelcase
            babel_compile: {cmd: 'python setup.py compile_catalog'}, // eslint-disable-line camelcase

            // Publish/Releases
            git: {
                cmd(cmd, branch) {
                    branch = branch ? ' ' + branch : '';
                    return 'git ' + cmd + branch;
                }
            },

             // Choose what to commit.
            commit_changed_files: {  // eslint-disable-line camelcase
                cmd(travis) {
                    grunt.config('stop_no_changes', Boolean(travis));
                    return 'git status -s -- locale/ gui/';
                },
                stdout: false,
                callback(err, stdout) {
                    stdout = stdout.trim();
                    if (!stdout.length) {
                        grunt.fatal('No changes to commit.', 0);
                    }

                    const commitPaths = [];
                    let commitMsg = [];
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
            commit_combined: { // eslint-disable-line camelcase
                cmd() {
                    const message = grunt.config('commit_msg');
                    const paths = grunt.config('commit_paths');
                    if (!message || !paths) {
                        grunt.fatal('Call exec:commit_changed_files instead!');
                    }
                    return 'git add -- ' + paths;
                },
                callback(err) {
                    if (err) {
                        // @TODO: Add error handling
                        return;
                    }

                    // Workaround for Travis (with -m "text" the quotes are within the message)
                    if (isTravis) {
                        const msgFilePath = 'commit-msg.txt';
                        grunt.file.write(msgFilePath, grunt.config('commit_msg'));
                        grunt.task.run('exec:git:commit:-F ' + msgFilePath);
                    } else {
                        grunt.task.run('exec:git:commit:-m "' + grunt.config('commit_msg') + '"');
                    }
                }
            },
            git_get_last_tag: { // eslint-disable-line camelcase
                cmd: 'git for-each-ref --sort=-refname --count=1 --format "%(refname:short)" refs/tags/v20[0-9][0-9]*',
                stdout: false,
                callback(err, stdout) {
                    stdout = stdout.trim();
                    if (/^v\d{4}.\d{1,2}.\d{1,2}.\d+$/.test(stdout)) {
                        grunt.config('last_tag', stdout);
                    } else {
                        grunt.fatal('Could not get the last tag name. We got: ' + stdout);
                    }
                }
            },
            git_list_changes: { // eslint-disable-line camelcase
                cmd() {
                    return 'git log --oneline --pretty=format:%s ' + grunt.config('last_tag') + '..HEAD';
                },
                stdout: false,
                callback(err, stdout) {
                    // Removes ` and tag information
                    const commits = stdout.trim().replace(/`/gm, '').replace(/^\([\w\d\s,.\-+_/>]+\)\s/gm, '');
                    if (commits) {
                        grunt.config('commits', commits);
                    } else {
                        grunt.fatal('Getting new commit list failed!');
                    }
                }
            },
            git_tag_new: { // eslint-disable-line camelcase
                cmd(sign) {
                    sign = sign !== 'true' ? '' : '-s ';
                    return 'git tag ' + sign + grunt.config('next_tag') + ' -m "' + grunt.config('commits') + '"';
                },
                stdout: false
            },
            git_push: { // eslint-disable-line camelcase
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
                callback(err, stdout, stderr) {
                    grunt.log.write(stderr.replace(process.env.GH_CRED, '[censored]'));
                }
            },
            git_list_tags: { // eslint-disable-line camelcase
                cmd: 'git for-each-ref --sort=refname ' +
                        '--format="%(refname:short)|||%(objectname)|||%(contents)\xB6\xB6\xB6" ' +
                        'refs/tags/v20[0-9][0-9]*',
                stdout: false,
                callback(err, stdout) {
                    if (!stdout) {
                        grunt.fatal('Git command returned no data.');
                    }
                    if (err) {
                        grunt.fatal('Git command failed to execute.');
                    }
                    const allTags = stdout
                        .replace(/-{5}BEGIN PGP SIGNATURE-{5}(.*\n)+?-{5}END PGP SIGNATURE-{5}\n/g, '')
                        .split('\xB6\xB6\xB6');
                    const foundTags = [];
                    allTags.forEach(curTag => {
                        if (curTag.length) {
                            const explode = curTag.split('|||');
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
            commit_changelog: { // eslint-disable-line camelcase
                cmd() {
                    const file = grunt.config('changesmd_file');
                    if (!file) {
                        grunt.fatal('Missing file path.');
                    }
                    const path = file.slice(0, -24); // Slices 'sickrage-news/CHANGES.md' (len=24)
                    if (!path) {
                        grunt.fatal('path = "' + path + '"');
                    }
                    let pushCmd = 'git push origin master';
                    if (grunt.option('no-push')) {
                        grunt.log.warn('Pushing with --dry-run ...'.magenta);
                        pushCmd += ' --dry-run';
                    }
                    return ['cd ' + path, 'git commit -asm "Update changelog"', 'git fetch origin', 'git rebase', pushCmd].join(' && ');
                },
                stdout: true
            }
        }
    });

    /*
    *  Internal tasks
    */
    grunt.registerTask('_get_next_tag', '(internal) do not run', () => {
        grunt.config.requires('last_tag');
        let lastTag = grunt.config('last_tag');

        const lastPatch = lastTag.match(/[0-9]+$/)[0];
        lastTag = grunt.template.date(lastTag.replace(/^v|-[0-9]*-?$/g, ''), 'yyyy.mm.dd');
        const today = grunt.template.today('yyyy.mm.dd');
        const patch = lastTag === today ? (parseInt(lastPatch, 10) + 1).toString() : '1';

        const nextTag = `v${today}-${patch}`;
        grunt.log.ok((`Creating tag ${nextTag}`).green);
        grunt.config('next_tag', nextTag);
    });

    grunt.registerTask('_genchanges', '(internal) do not run', () => {
        // Generate changes
        const allTags = grunt.config('all_tags');
        if (!allTags) {
            grunt.fatal('No tags information was received.');
        }

        const file = grunt.config('changesmd_file'); // --file=path/to/sickrage.github.io/sickrage-news/CHANGES.md
        if (!file) {
            grunt.fatal('Missing file path.');
        }

        let contents = '';
        allTags.forEach(tag => {
            contents += '### ' + tag.tag + '\n';
            contents += '\n';
            if (tag.previous) {
                contents += '[full changelog](https://github.com/SickRage/SickRage/compare/' +
                    tag.previous + '...' + tag.tag + ')\n';
            }
            contents += '\n';

            // Link issue numbers, style links of issues and pull requests
            const reg = /([\w\d\-.]+\/[\w\d\-.]+)?#(\d+)|https?:\/\/github.com\/([\w\d\-.]+\/[\w\d\-.]+)\/(issues|pull)\/(\d+)/gm;
            tag.message.forEach(row => {
                contents += row.replace(reg, (all, repoL, numL, repoR, typeR, numR) => {
                    if (numL) { // RepoL, numL = user/repo#1234 style
                        return '[' + (repoL ? repoL : '') + '#' + numL + '](https://github.com/' +
                        (repoL ? repoL : 'SickRage/SickRage') + '/issues/' + numL + ')';
                    } else if (numR) { // RepoR, type, numR = https://github/user/repo/issues/1234 style
                        return '[#' + numR + '](https://github.com/' + repoR + '/' + typeR + '/' + numR + ')';
                    }
                })
                // Shorten and link commit hashes
                .replace(/([a-f0-9]{40}(?![a-f0-9]))/g, sha1 => {
                    return '[' + sha1.substr(0, 7) + '](https://github.com/SickRage/SickRage/commit/' + sha1 + ')';
                })
                // Remove tag information
                .replace(/^\([\w\d\s,.\-+/>]+\)\s/gm, '')
                // Remove commit hashes from start
                .replace(/^[a-f0-9]{7} /gm, '')
                // Style messages that contain lists
                .replace(/( {3,}\*)(?!\*)/g, '\n  -')
                // Escapes markdown __ tags
                .replace(/__/gm, '\\_\\_')
                // Add * to the first line only
                .replace(/^(\w)/, '* $1');

                contents += '\n';
            });
            contents += '\n';
        });

        if (contents) {
            grunt.file.write(file, contents);
            return true;
        }
        grunt.fatal('Received no contents to write to file, aborting');
    });
};
