window.SICKCHILL ||= {};

function setAllShowChecks(checked) {
    $('.allCheck, input[class*="-epcheck"]').prop('checked', checked);
}

function escapeHtml(value) {
    return $('<div>').text(value === undefined || value === null ? '' : String(value)).html();
}

window.SICKCHILL.manage = {
    init() {
        $.makeEpisodeRow = function (indexerId, season, episode, name, checked) { // eslint-disable-line max-params
            const epName = indexerId + '-' + season + 'x' + episode;
            let row = '';
            row += ' <tr class="' + $('#row_class').val() + ' show-' + indexerId + '">';
            row += '  <td class="tableleft" align="center">'
                + '<input type="checkbox" class="' + indexerId + '-epcheck" name="' + epName + '"'
                + (checked ? ' checked' : '') + '></td>';
            row += '  <td>' + season + 'x' + episode + '</td>';
            row += '  <td class="tableright" style="width: 100%">' + escapeHtml(name) + '</td>';
            row += ' </tr>';

            return row;
        };

        $.makeSubtitleRow = function (indexerId, season, episode, name, subtitles, checked) { // eslint-disable-line max-params
            const epName = indexerId + '-' + season + 'x' + episode;
            let row = '';
            row += '<tr class="good show-' + indexerId + '">';
            row += '<td class="text-center">'
                + '<input type="checkbox" class="' + indexerId + '-epcheck" name="' + epName + '"'
                + (checked ? ' checked' : '') + '></td>';
            row += '<td style="width: 2%;">' + season + 'x' + episode + '</td>';
            if (subtitles.length > 0) {
                row += '<td style="width: 8%;">';
                subtitles = subtitles.split(',');
                for (const i in subtitles) {
                    if (Object.hasOwn(subtitles, i)) {
                        row += '<img src="' + scRoot + '/images/subtitles/flags/' + subtitles[i] + '.png" width="16" height="11" alt="' + subtitles[i] + '" />&nbsp;';
                    }
                }

                row += '</td>';
            } else {
                row += '<td style="width: 8%;">None</td>';
            }

            row += '<td>' + escapeHtml(name) + '</td>';
            row += '</tr>';

            return row;
        };

        $('#config_save_button').on('click', () => {
            $('#configForm').submit();
        });
    },
    index() {
        function checkBool(item) {
            return item === 'Y' ? 'Yes' : 'No';
        }

        $('#massUpdateTable:has(tbody tr)').tablesorter({
            sortList: [[1, 0]],
            widthFixed: true,
            textExtraction: {
                2(node) { // Network
                    return ($(node).find('img').attr('alt') || 'unknown');
                },
                3(node) { // Quality
                    return $(node).find('span').text();
                },
                4(node) { // Sports
                    return checkBool($(node).find('span').attr('title'));
                },
                5(node) { // Scene
                    return checkBool($(node).find('span').attr('title'));
                },
                6(node) { // Anime
                    return checkBool($(node).find('span').attr('title'));
                },
                7(node) { // Season Folders
                    return checkBool($(node).find('span').attr('title'));
                },
                8(node) { // Paused
                    return checkBool($(node).find('span').attr('title'));
                },
                9(node) { // Subtitle
                    return checkBool($(node).find('span').attr('title'));
                },
                10(node) { // Default Episode Status
                    return $(node).text();
                },
                11(node) { // Show Status
                    return $(node).text();
                },
                12(node) { // Root dir
                    return $(node).text();
                },
            },
            widgets: ['zebra', 'filter', 'columnSelector', 'saveSort', 'stickyHeaders'],
            headers: {
                0: {sorter: false, filter: false},
                1: {sorter: 'loadingNames'},
                2: {sorter: 'network'},
                3: {sorter: 'quality'},
                4: {sorter: 'sports'},
                5: {sorter: 'scene'},
                6: {sorter: 'anime'},
                7: {sorter: 'flatfold'},
                8: {sorter: 'paused'},
                9: {sorter: 'subtitle'},
                10: {sorter: 'default_ep_status'},
                11: {sorter: 'status'},
                12: {sorter: 'roootDirs'},
                13: {sorter: false},
                14: {sorter: false},
                15: {sorter: false},
                16: {sorter: false},
                17: {sorter: false},
                18: {sorter: false},
            },
            widgetOptions: {
                columnSelector_saveColumns: true, // eslint-disable-line camelcase
                columnSelector_layout: '<label><input type="checkbox"/>{name}</label>', // eslint-disable-line camelcase
                columnSelector_mediaquery: false, // eslint-disable-line camelcase
                columnSelector_cssChecked: 'checked', // eslint-disable-line camelcase
                columnSelector_columns: { // eslint-disable-line camelcase
                    12: false,
                },
                stickyHeaders_offset: 50, // eslint-disable-line camelcase
                filter_cssFilter: 'text-center text-capitalize', // eslint-disable-line camelcase
                filter_hideFilters: false, // eslint-disable-line camelcase
                filter_ignoreCase: true, // eslint-disable-line camelcase
                filter_reset: '.resetsorting', // eslint-disable-line camelcase
            },
        });
        $('#popover').popover({
            placement: 'bottom',
            html: true, // Required if content has HTML
            content: '<div id="popover-target"></div>',
        }).on('shown.bs.popover', () => { // Bootstrap popover event triggered when the popover opens
            // call this function to copy the column selection code into the popover
            $.tablesorter.columnSelector.attachTo($('#massUpdateTable'), '#popover-target');
        });

        $('.submitMassUpdate').on('click', event => {
            event.preventDefault();

            const form = $('[name="massUpdateForm"]');
            const deleteInputs = $('.deleteCheck:checked');

            if (deleteInputs.length > 0) {
                $.confirm({
                    title: 'Delete Shows',
                    text: 'You have selected to delete ' + deleteInputs.length + ' show(s).  Are you sure you wish to continue? All files will be removed from your system.',
                    confirm() {
                        form.submit();
                    },
                    cancel() {
                        $('.deleteCheck:checked').prop('checked', false);
                        form.submit();
                    },
                });
            } else {
                form.submit();
            }
        });
    },
    backlogOverview() {
        $('#pickShow').on('change', event => {
            const showid = $(event.currentTarget).val();
            if (showid) {
                $('html,body').animate({scrollTop: $('#show-' + showid).offset().top - 25}, 'slow');
            }
        });
    },
    failedDownloads() {
        $('#failedTable:has(tbody tr)').tablesorter({
            widgets: ['zebra'],
            sortList: [[1, 0]],
            headers: {3: {sorter: false}},
        });
        $('#limit').on('change', event => {
            window.location.assign(scRoot + '/manage/failedDownloads/?limit=' + $(event.currentTarget).val());
        });

        $('#submitMassRemove').on('click', () => {
            const removeArray = [];

            $('.removeCheck').each(function () {
                if (this.checked === true) {
                    removeArray.push($(this).attr('id').split('-', 2)[1]);
                }
            });

            if (removeArray.length === 0) {
                return false;
            }

            $.post(scRoot + '/manage/failedDownloads', {remove: removeArray}, () => {
                location.reload(true);
            });
        });

        for (const name of ['.removeCheck']) {
            let lastCheck = null;

            $(name).on('click', function (event) {
                if (!lastCheck || !event.shiftKey) {
                    lastCheck = this; // eslint-disable-line unicorn/no-this-assignment
                    return;
                }

                const check = this; // eslint-disable-line unicorn/no-this-assignment
                const checks = $(name + ':visible').get();
                const start = checks.indexOf(lastCheck);
                const end = checks.indexOf(check);
                if (start === -1 || end === -1) {
                    lastCheck = check;
                    return;
                }

                const {checked} = lastCheck;
                const from = Math.min(start, end);
                const to = Math.max(start, end);
                for (let index = from; index <= to; index++) {
                    checks[index].checked = checked;
                }
            });
        }
    },
    massEdit() {
        function findDirectoryIndex(which) {
            const directoryParts = which.split('_');
            return directoryParts.at(-1);
        }

        function editRootDirectory(path, options) {
            $('#new_root_dir_' + options.whichId).val(path);
            $('#new_root_dir_' + options.whichId).change();
        }

        $('.new_root_dir').on('change', function () {
            const currentIndex = findDirectoryIndex($(this).attr('id'));
            $('#display_new_root_dir_' + currentIndex).html('<b>' + $(this).val() + '</b>');
        });

        $('.edit_root_dir').on('click', function () {
            const currentIndex = findDirectoryIndex($(this).attr('id'));
            const initialDirectory = $('#new_root_dir_' + currentIndex).val();
            $(this).nFileBrowser(editRootDirectory, {initialDirectory, whichId: currentIndex});
        });

        $('.delete_root_dir').on('click', function () {
            const currentIndex = findDirectoryIndex($(this).attr('id'));
            $('#new_root_dir_' + currentIndex).val(null);
            $('#display_new_root_dir_' + currentIndex).html('<b>' + _('DELETED') + '</b>');
        });

        SICKCHILL.common.QualityChooser.init();
    },
    episodeStatuses() {
        $('.allCheck').on('click', function () {
            const indexerId = $(this).attr('id').split('-', 2)[1];
            $('.' + indexerId + '-epcheck').prop('checked', this.checked);
        });

        $('.get_more_eps').on('click', function () {
            const currentIndexerId = $(this).attr('id');
            const checked = $('#allCheck-' + currentIndexerId).is(':checked');
            const lastRow = $('tr#' + currentIndexerId);
            const clicked = $(this).attr('data-clicked');
            const action = $(this).attr('value');

            if (!clicked) {
                $.getJSON(scRoot + '/manage/showEpisodeStatuses', {
                    indexer_id: currentIndexerId, // eslint-disable-line camelcase
                    whichStatus: $('#oldStatus').val(),
                }, data => {
                    $.each(data, (season, eps) => {
                        $.each(eps, (episode, name) => {
                            lastRow.after($.makeEpisodeRow(currentIndexerId, season, episode, name, checked));
                        });
                    });
                });
                $(this).attr('data-clicked', 1);
                $(this).prop('value', 'Collapse');
            } else if (action.toLowerCase() === 'collapse') {
                $('.show-' + currentIndexerId).hide();
                $(this).prop('value', 'Expand');
            } else if (action.toLowerCase() === 'expand') {
                $('.show-' + currentIndexerId).show();
                $(this).prop('value', 'Collapse');
            }
        });

        $('.selectAllShows').on('click', () => {
            setAllShowChecks(true);
        });
        $('.deselectAllShows').on('click', () => {
            setAllShowChecks(false);
        });
    },
    subtitleMissed() {
        $('.allCheck').on('click', function () {
            const indexerId = $(this).attr('id').split('-', 2)[1];
            $('.' + indexerId + '-epcheck').prop('checked', this.checked);
        });

        $('.get_more_eps').on('click', function () {
            const indexerId = $(this).attr('id');
            const checked = $('#allCheck-' + indexerId).is(':checked');
            const lastRow = $('tr#' + indexerId);
            const clicked = $(this).attr('data-clicked');
            const action = $(this).attr('value');

            if (!clicked) {
                $.getJSON(scRoot + '/manage/showSubtitleMissed', {
                    indexer_id: indexerId, // eslint-disable-line camelcase
                    whichSubs: $('#selectSubLang').val(),
                }, data => {
                    $.each(data, (season, eps) => {
                        $.each(eps, (episode, episodeData) => {
                            lastRow.after($.makeSubtitleRow(indexerId, season, episode, episodeData.name, episodeData.subtitles, checked));
                        });
                    });
                });
                $(this).attr('data-clicked', 1);
                $(this).prop('value', 'Collapse');
            } else if (action === 'Collapse') {
                $('.show-' + indexerId).hide();
                $(this).prop('value', 'Expand');
            } else if (action === 'Expand') {
                $('.show-' + indexerId).show();
                $(this).prop('value', 'Collapse');
            }
        });

        $('.selectAllShows').on('click', () => {
            setAllShowChecks(true);
        });
        $('.deselectAllShows').on('click', () => {
            setAllShowChecks(false);
        });
    },
};
