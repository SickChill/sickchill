window.SICKCHILL ||= {};
window.SICKCHILL.home = {
    init() {
        // Reset the layout for the activated tab (when using ui tabs)
        $('#showTabs').tabs({
            activate() {
                $('.show-grid').isotope('layout');
            },
        });
    },
    index() {
        // Resets the tables sorting, needed as we only use a single call for both tables in tablesorter
        $('.resetsorting').on('click', () => {
            $('table').trigger('filterReset');
        });

        // Handle filtering in the poster layout
        $('#filterShowName').on('input', __.debounce(() => {
            $('.show-grid').isotope({
                filter() {
                    const name = $(this).find('.show-title').html().trim().toLowerCase();
                    return name.includes($('#filterShowName').val().toLowerCase());
                },
            });
        }, 500));

        function resizePosters(newSize) {
            let fontSize = 0;
            let logoWidth = 0;
            let borderRadius = 0;
            let borderWidth = 0;

            if (newSize < 125) { // Small
                borderRadius = 3;
                borderWidth = 4;
            } else if (newSize < 175) { // Medium
                fontSize = 9;
                logoWidth = 40;
                borderRadius = 4;
                borderWidth = 5;
            } else { // Large
                fontSize = 11;
                logoWidth = 50;
                borderRadius = 6;
                borderWidth = 6;
            }

            // If there's a poster popup, remove it before resizing
            $('#posterPopup').remove();

            if (fontSize === undefined) {
                $('.show-details').hide();
            } else {
                $('.show-details').show();
                $('.show-dlstats, .show-quality').css('fontSize', fontSize);
                $('.show-network-image').css('width', logoWidth);
            }

            $('.show-container').css({
                width: newSize,
                borderWidth,
                borderRadius,
            });
        }

        let posterSize;
        if (typeof (Storage) !== 'undefined') {
            posterSize = Number.parseInt(localStorage.getItem('posterSize'), 10);
        }

        if (typeof (posterSize) !== 'number' || Number.isNaN(posterSize)) {
            posterSize = 188;
        }

        resizePosters(posterSize);

        $('#posterSizeSlider').slider({
            min: 75,
            max: 250,
            value: posterSize,
            change(event, ui) {
                if (typeof (Storage) !== 'undefined') {
                    localStorage.setItem('posterSize', ui.value);
                }

                resizePosters(ui.value);
                $('.show-grid').isotope('layout');
            },
        });

        $('#rootDirSelect').on('change', () => {
            $('#rootDirForm').submit();
        });

        $('img#network').on('error', function () {
            $(this).parent().text($(this).attr('alt'));
            $(this).remove();
        });

        $('#showListTableShows:has(tbody tr), #showListTableAnime:has(tbody tr)').tablesorter({
            sortList: [[7, 1], [2, 0]],
            textExtraction: {
                0(node) {
                    return $(node).find('time').attr('datetime');
                },
                1(node) {
                    return $(node).find('time').attr('datetime');
                },
                2(node) {
                    return latinize($(node).text().normalize('NFC'));
                },
                3(node) {
                    return ($(node).find('span').prop('title') || 'zunknown').toLowerCase();
                },
                4(node) {
                    return $(node).find('span').text().toLowerCase();
                },
                5(node) {
                    const progress = $(node).find('div').attr('data-progress-percentage');
                    const progressResult = progress === undefined ? -Infinity : (progress.length > 0 && Number.parseFloat(progress)) || 0;
                    const total = $(node).find('div').attr('data-progress-total');
                    const totalTesult = total === undefined ? -Infinity : (total.length > 0 && Number.parseInt(total, 10)) || 0;
                    return (progressResult * 100 * 1000) + totalTesult;
                },
                6(node) {
                    return $(node).data('show-size');
                },
                7(node) {
                    return ($(node).find('span').attr('title') || 'No').toLowerCase();
                },
            },
            widgets: ['saveSort', 'zebra', 'stickyHeaders', 'filter', 'columnSelector'],
            headers: {
                0: {sorter: 'realISODate'},
                1: {sorter: 'realISODate'},
                2: {sorter: 'loadingNames'},
                4: {sorter: 'quality'},
                5: {sorter: 'digit'},
                6: {sorter: 'digit'},
                7: {filter: 'parsed'},
            },
            widgetOptions: {
                filter_columnFilters: true, // eslint-disable-line camelcase
                filter_hideFilters: true, // eslint-disable-line camelcase
                stickyHeaders_offset: 50, // eslint-disable-line camelcase
                filter_saveFilters: false, // eslint-disable-line camelcase
                filter_functions: { // eslint-disable-line camelcase
                    // HOWTO: https://mottie.github.io/tablesorter/docs/example-widget-filter-custom.html#notes
                    5(exact, normalized, filterInput) {
                        let isTest = false;
                        const pct = Math.floor((normalized % 1) * 1000);
                        const doCompare = {
                            '<'(a, b) {
                                return a < b;
                            },
                            '<='(a, b) {
                                return a <= b;
                            },
                            '>='(a, b) {
                                return a >= b;
                            },
                            '>'(a, b) {
                                return a > b;
                            },
                        };

                        if (filterInput === '') {
                            isTest = true;
                        } else {
                            let result = filterInput.match(/(<|<=|>=|>)\s?(\d+)/);
                            if (result) {
                                // Compare using the matched operator
                                const comp = doCompare[result[1]];
                                if (comp(pct, Number.parseInt(result[2], 10))) {
                                    isTest = true;
                                }
                            }

                            result = filterInput.match(/(\d+)\s(-|to)\s+(\d+)/i);
                            if (result && ((result[2] === '-') || (result[2] === 'to')) && (pct >= Number.parseInt(result[1], 10)) && (pct <= Number.parseInt(result[3], 10))) {
                                isTest = true;
                            }

                            result = filterInput.match(/(=)?\s?(\d+)\s?(=)?/);
                            if (result && ((result[1] === '=') || (result[3] === '=')) && Number.parseInt(result[2], 10) === pct) {
                                isTest = true;
                            }

                            if (!Number.isNaN(Number.parseFloat(filterInput)) && Number.isFinite(filterInput) && Number.parseInt(filterInput, 10) === pct) {
                                isTest = true;
                            }
                        }

                        return isTest;
                    },
                },
                columnSelector_mediaquery: false, // eslint-disable-line camelcase
            },
            sortStable: true,
            sortAppend: [[2, 0]],
        });

        {
            let sort;
            switch (getMeta('settings.POSTER_SORTBY')) {
                case 'progress': {
                    sort = ['progress', 'total', 'name'];
                    break;
                }

                case 'date': {
                    sort = ['date', 'status', 'name'];
                    break;
                }

                case 'status': {
                    sort = ['status', 'progress', 'name'];
                    break;
                }

                default: {
                    sort = getMeta('settings.POSTER_SORTBY');
                    break;
                }
            }

            $('.loading-spinner').hide();
            $('.show-grid').show().isotope({
                itemSelector: '.show-container',
                sortBy: sort,
                sortAscending: getMeta('settings.POSTER_SORTDIR'),
                layoutMode: 'masonry',
                masonry: {
                    isFitWidth: true,
                    horizontalOrder: true,
                },
                getSortData: {
                    name(itemElement) {
                        const name = $(itemElement).attr('data-name') || '';
                        const regex = new RegExp('^((?:' + getMeta('settings.GRAMMAR_ARTICLES') + String.raw`)\s)`, 'i');
                        return latinize((metaToBool('settings.SORT_ARTICLE') ? name : name.replace(regex, '')).toLowerCase().normalize('NFC'));
                    },
                    network: '[data-network]',
                    date(itemElement) {
                        const date = $(itemElement).attr('data-date');
                        return (date.length > 0 && Number.parseInt(date, 10)) || Infinity;
                    },
                    progress(itemElement) {
                        const progress = $(itemElement).attr('data-progress');
                        return (progress.length > 0 && Number.parseFloat(progress)) || 0;
                    },
                    total(itemElement) {
                        const totalEps = $(itemElement).attr('data-progress-total');
                        return (totalEps.length > 0 && Number.parseInt(totalEps, 10)) || 0;
                    },
                    status: '[data-status]',
                },
            });
            bindMasonryImageLayout($('.show-grid'));

            // When posters are small enough to not display the .show-details
            // table, display a larger poster when hovering.
            let posterHoverTimer = null;
            $('.show-container').on('mouseenter', function () {
                const poster = $(this);
                const details = poster.find('.show-network-image');
                if (details[0].style.cssText !== 'width: 0px;') {
                    return;
                }

                posterHoverTimer = setTimeout(() => {
                    posterHoverTimer = null;
                    $('#posterPopup').remove();

                    const popup = poster.clone().attr({
                        id: 'posterPopup',
                    });
                    const origLeft = poster.offset().left;
                    const origWidth = poster.width();
                    const origHeight = poster.height();
                    const origTop = poster.offset().top;
                    popup.css({
                        position: 'absolute',
                        margin: 0,
                        top: origTop,
                        left: origLeft,
                        zIndex: 9999,
                    });

                    popup.find('.show-details').show();
                    popup.on('mouseleave', function () {
                        $(this).animate({
                            height: origHeight + 8,
                            width: origWidth + 8,
                            top: origTop,
                            left: origLeft,
                        });
                    });
                    popup.appendTo('body');

                    const height = 438;
                    const width = 250;
                    let newTop = (origTop + (poster.height() / 2)) - (height / 2);
                    let newLeft = (origLeft + (poster.width() / 2)) - (width / 2);

                    // Make sure the popup isn't outside the viewport
                    const margin = 5;
                    const scrollTop = $(window).scrollTop();
                    const scrollLeft = $(window).scrollLeft();
                    const scrollBottom = scrollTop + $(window).innerHeight();
                    const scrollRight = scrollLeft + $(window).innerWidth();
                    if (newTop < scrollTop + margin) {
                        newTop = scrollTop + margin;
                    }

                    if (newLeft < scrollLeft + margin) {
                        newLeft = scrollLeft + margin;
                    }

                    if (newTop + height + margin > scrollBottom) {
                        newTop = scrollBottom - height - margin;
                    }

                    if (newLeft + width + margin > scrollRight) {
                        newLeft = scrollRight - width - margin;
                    }

                    popup.animate({
                        top: newTop,
                        left: newLeft,
                        width: 250,
                        height: 438,
                    });
                }, 300);
            }).on('mouseleave', () => {
                if (posterHoverTimer !== null) {
                    clearTimeout(posterHoverTimer);
                }
            });
        }

        $('#layout').on('change', function () {
            window.location.assign($(this).find('option:selected').val());
        });

        $('#postersort').on('change', function () {
            let sort;
            switch ($(this).val()) {
                case 'progress': {
                    sort = ['progress', 'total', 'name'];
                    break;
                }

                case 'date': {
                    sort = ['date', 'status', 'name'];
                    break;
                }

                case 'status': {
                    sort = ['status', 'progress', 'name'];
                    break;
                }

                default: {
                    sort = getMeta('settings.POSTER_SORTBY');
                    break;
                }
            }

            $('.show-grid').isotope({
                layoutMode: 'masonry',
                masonry: {
                    isFitWidth: true,
                    horizontalOrder: true,
                },
                sortBy: sort,
                getSortData: {
                    name(itemElement) {
                        const name = $(itemElement).attr('data-name') || '';
                        const regex = new RegExp('^((?:' + getMeta('settings.GRAMMAR_ARTICLES') + String.raw`)\s)`, 'i');
                        return latinize((metaToBool('settings.SORT_ARTICLE') ? name : name.replace(regex, '')).toLowerCase().normalize('NFC'));
                    },
                    network: '[data-network]',
                    date(itemElement) {
                        const date = $(itemElement).attr('data-date');
                        return (date.length > 0 && Number.parseInt(date, 10)) || Infinity;
                    },
                    progress(itemElement) {
                        const progress = $(itemElement).attr('data-progress');
                        return (progress.length > 0 && Number.parseFloat(progress)) || 0;
                    },
                    total(itemElement) {
                        const totalEps = $(itemElement).attr('data-progress-total');
                        return (totalEps.length > 0 && Number.parseInt(totalEps, 10)) || 0;
                    },
                    status: '[data-status]',
                },
            });
            $.post($(this).find('option:selected').data('sort'));
        });

        $('#postersortdirection').on('change', function () {
            $('.show-grid').isotope({
                layoutMode: 'masonry',
                masonry: {
                    isFitWidth: true,
                    horizontalOrder: true,
                },
                sortAscending: ($(this).val() === 'true'),
                getSortData: {
                    name(itemElement) {
                        const name = $(itemElement).attr('data-name') || '';
                        const regex = new RegExp('^((?:' + getMeta('settings.GRAMMAR_ARTICLES') + String.raw`)\s)`, 'i');
                        return latinize((metaToBool('settings.SORT_ARTICLE') ? name : name.replace(regex, '')).toLowerCase().normalize('NFC'));
                    },
                    network: '[data-network]',
                    date(itemElement) {
                        const date = $(itemElement).attr('data-date');
                        return (date.length > 0 && Number.parseInt(date, 10)) || Infinity;
                    },
                    progress(itemElement) {
                        const progress = $(itemElement).attr('data-progress');
                        return (progress.length > 0 && Number.parseFloat(progress)) || 0;
                    },
                    total(itemElement) {
                        const totalEps = $(itemElement).attr('data-progress-total');
                        return (totalEps.length > 0 && Number.parseInt(totalEps, 10)) || 0;
                    },
                    status: '[data-status]',
                },
            });
            $.post($(this).find('option:selected').data('sort'));
        });

        $('#popover').popover({
            placement: 'bottom',
            html: true, // Required if content has HTML
            content: '<div id="popover-target"></div>',
        }).on('shown.bs.popover', () => { // Bootstrap popover event triggered when the popover opens
            // call this function to copy the column selection code into the popover
            $.tablesorter.columnSelector.attachTo($('#showListTableShows'), '#popover-target');
            if (metaToBool('settings.ANIME_SPLIT_HOME')) {
                $.tablesorter.columnSelector.attachTo($('#showListTableAnime'), '#popover-target');
            }
        });
    },
    displayShow() {
        if (metaToBool('settings.FANART_BACKGROUND')) {
            const backgroundPath = getMeta('showBackgroundImage') || scRoot + '/cache/images/' + $('#showID').attr('value') + '.fanart.jpg';
            $.backstretch(backgroundPath);
            $('.backstretch').css('opacity', getMeta('settings.FANART_BACKGROUND_OPACITY')).fadeIn('500');
        }

        $('.displayShowTable').tablesorter({
            widgets: ['saveSort', 'stickyHeaders', 'columnSelector'],
            widgetOptions: {
                columnSelector_saveColumns: true, // eslint-disable-line camelcase
                columnSelector_layout: '<label><input type="checkbox"/>{name}</label>', // eslint-disable-line camelcase
                columnSelector_mediaquery: false, // eslint-disable-line camelcase
                columnSelector_cssChecked: 'checked', // eslint-disable-line camelcase
                stickyHeaders_offset: 50, // eslint-disable-line camelcase
            },
        });

        $('.displayShowTable').ajaxEpSearch({colorRow: true});

        function enableLink(link) {
            link.on('click.disabled', false);
            link.prop('enableClick', '1');
            link.fadeTo('fast', 1);
        }

        function disableLink(link) {
            link.off('click.disabled');
            link.prop('enableClick', '0');
            link.fadeTo('fast', 0.5);
        }

        $('.play-on-kodi').on('click', function () {
            if ($(this).prop('enableClick') === '0') {
                return false;
            }

            const selectedEpisode = $(this);
            const playModal = $('#playOnKodiModal');

            $('#playOnKodiModal .btn.btn-success').on('click', () => {
                disableLink(selectedEpisode);
                playModal.modal('hide');

                const img = selectedEpisode.children('img');
                img.hide();

                selectedEpisode.append($('<span/>').attr({class: 'loading-spinner16', title: 'Playing'}));
                const icon = selectedEpisode.children('span');

                const host = $('#kodi-play-host').val();
                $.getJSON(selectedEpisode.prop('href') + '&host=' + host, data => {
                    if (data.result.toLowerCase() === 'failure') {
                        icon.prop('class', 'displayshow-icon-disable');
                        icon.prop('title', 'Failed');
                    } else {
                        img.prop('title', 'Success');
                        img.prop('alt', 'Success');
                        icon.hide();
                        img.show();
                    }
                });
                enableLink(selectedEpisode);
                return false;
            });
            playModal.modal('show');
            return false;
        });

        $('.epSubtitlesSearch').on('click', function () {
            if ($(this).prop('enableClick') === '0') {
                return false;
            }

            const link = $(this);
            disableLink(link);

            const icon = link.children('span');
            icon.prop('class', 'loading-spinner16');
            icon.prop('title', 'Queuing');

            $.getJSON(link.attr('href'), data => {
                if (data.result.toLowerCase() === 'failure') {
                    icon.prop('class', 'displayshow-icon-disable');
                    icon.prop('title', data.errorMessage || data.result || 'Failed');
                    enableLink(link);
                    return;
                }

                // Search is queued; notification fires when the worker finishes
                let title = data.message || _('Subtitle search queued');
                if (data.queued && data.blocked_by) {
                    title = _('Queued') + ' (' + data.blocked_by + ' ' + _('search running') + ')';
                    icon.prop('class', 'displayshow-icon-clock');
                } else {
                    icon.prop('class', 'loading-spinner16');
                }

                icon.prop('title', title);
                // Keep link disabled until page reload / notification; avoid duplicate queue items
            });
            return false;
        });

        $('.epRetrySubtitlesSearch').on('click', function () {
            if ($(this).prop('enableClick') === '0') {
                return false;
            }

            const selectedEpisode = $(this);
            const subtitleModal = $('#confirmSubtitleDownloadModal');

            $('#confirmSubtitleDownloadModal .btn.btn-success').off('click.subtitleQueue').on('click.subtitleQueue', () => {
                disableLink(selectedEpisode);
                subtitleModal.modal('hide');

                const img = selectedEpisode.children('img');
                img.hide();

                selectedEpisode.append($('<span/>').attr({class: 'loading-spinner16', title: 'Queuing'}));
                const icon = selectedEpisode.children('span');

                $.getJSON(selectedEpisode.prop('href'), data => {
                    if (data.result.toLowerCase() === 'failure') {
                        icon.prop('class', 'displayshow-icon-disable');
                        icon.prop('title', data.errorMessage || 'Failed');
                        enableLink(selectedEpisode);
                        return;
                    }

                    let title = data.message || _('Subtitle search queued');
                    if (data.queued && data.blocked_by) {
                        title = _('Queued') + ' (' + data.blocked_by + ' ' + _('search running') + ')';
                        icon.prop('class', 'displayshow-icon-clock');
                    }

                    icon.prop('title', title);
                });
                return false;
            });
            subtitleModal.modal('show');
            return false;
        });

        $('#seasonJump').on('change', () => {
            const $seasonJumpOpt = $('#seasonJump option:selected');
            const id = $seasonJumpOpt.val();
            if (id && id !== 'jump') {
                const season = $seasonJumpOpt.data('season');
                $('html,body').animate({scrollTop: $('#' + id.slice(1)).offset().top - 50}, 'slow');
                $('#collapseSeason-' + season).collapse('show');
                location.hash = id;
            }

            $(this).val('jump');
        });

        $('#seasonJumpLinks a').on('click', event_ => {
            const season = $(event_.target).data('season');
            $('html,body').animate({scrollTop: $('#' + season).offset().top - 50}, 'slow');
            $('#collapseSeason-' + season).collapse('show');
            location.hash = season;
            return false;
        });

        $('#prevShow').on('click', () => {
            $('#pickShow option:selected').prev('option').prop('selected', 'selected');
            $('#pickShow').change();
        });

        $('#nextShow').on('click', () => {
            $('#pickShow option:selected').next('option').prop('selected', 'selected');
            $('#pickShow').change();
        });

        $('#changeStatus').on('click', () => {
            const epArray = [];

            $('.epCheck').each(function () {
                if (this.checked === true) {
                    epArray.push($(this).attr('id'));
                }
            });

            if (epArray.length === 0) {
                return false;
            }

            const parameters = {
                show: $('#showID').attr('value'),
                eps: epArray,
                status: $('#statusSelect').val(),
            };
            $.post(scRoot + '/home/setStatus', parameters, () => {
                location.reload(true);
            });
        });

        $('.seasonCheck').on('click', function () {
            const seasCheck = this.checked;
            const seasNo = $(this).attr('id');
            $('#collapseSeason-' + seasNo).collapse('show');
            $('.epCheck:visible[id^="' + seasNo + 'x"]').each(function () {
                this.checked = seasCheck;
            });
        });

        let lastCheck = null;
        $('.epCheck').on('click', function (event) {
            if (!lastCheck || !event.shiftKey) {
                lastCheck = this; // eslint-disable-line unicorn/no-this-assignment
                return;
            }

            const check = this; // eslint-disable-line unicorn/no-this-assignment
            let found = 0;

            $('.epCheck').each(function () {
                if (found === 2) {
                    return false;
                }

                if (found === 1) {
                    this.checked = lastCheck.checked;
                }

                if (this === check || this === lastCheck) {
                    found++;
                }
            });
        });

        // Selects all visible episode checkboxes.
        $('.seriesCheck').on('click', () => {
            $('.epCheck:visible').each(function () {
                this.checked = true;
            });
            $('.seasonCheck:visible').each(function () {
                this.checked = true;
            });
        });

        // Clears all visible episode checkboxes and the season selectors
        $('.clearAll').on('click', () => {
            $('.epCheck:visible').each(function () {
                this.checked = false;
            });
            $('.seasonCheck:visible').each(function () {
                this.checked = false;
            });
        });

        // Handle the show selection dropbox
        $('#pickShow').on('change', function () {
            const value = $(this).val();
            if (value === 0) {
                return;
            }

            window.location.assign(scRoot + '/home/displayShow?show=' + value);
        });

        // Show/hide different types of rows when the checkboxes are changed
        $('#checkboxControls input').on('change', function () {
            const whichClass = $(this).attr('id');
            $(this).showHideRows(whichClass);
        });

        // Initially show/hide all the rows according to the checkboxes
        $('#checkboxControls input').each(function () {
            const status = this.checked;
            $('tr.' + $(this).attr('id')).each(function () {
                if (status) {
                    $(this).show();
                } else {
                    $(this).hide();
                }
            });
        });

        $.fn.showHideRows = function (whichClass) {
            const status = $('#checkboxControls > input, #' + whichClass).is(':checked');
            $('tr.' + whichClass).each(function () {
                if (status) {
                    $(this).show();
                } else {
                    $(this).hide();
                }
            });

            // Hide season headers with no episodes under them
            $('div.seasonheader').each(function () {
                let numberRows = 0;
                const seasonNo = $(this).attr('data-season-id');
                $('tr.season-' + seasonNo + ' :visible').each(() => {
                    numberRows++;
                });
                if (numberRows === 0) {
                    $(this).hide();
                    $('#' + seasonNo + '-cols').hide();
                } else {
                    $(this).show();
                    $('#' + seasonNo + '-cols').show();
                }
            });
        };

        function setEpisodeSceneNumbering(forSeason, forEpisode, sceneSeason, sceneEpisode) {
            const showId = $('#showID').val();
            const indexer = $('#indexer').val();

            $.getJSON(scRoot + '/home/setSceneNumbering', {
                show: showId,
                indexer,
                forSeason,
                forEpisode,
                sceneSeason: sceneSeason === '' ? null : sceneSeason,
                sceneEpisode: sceneEpisode === '' ? null : sceneEpisode,
            }, data => {
                // Set the values we get back
                if (data.sceneSeason === null || data.sceneEpisode === null) {
                    $('#sceneSeasonXEpisode_' + showId + '_' + forSeason + '_' + forEpisode).val('');
                } else {
                    $('#sceneSeasonXEpisode_' + showId + '_' + forSeason + '_' + forEpisode).val(data.sceneSeason + 'x' + data.sceneEpisode);
                }

                if (!data.success) {
                    if (data.errorMessage) {
                        notifyModal(data.errorMessage);
                    } else {
                        notifyModal('Update failed.');
                    }
                }
            });
        }

        function setAbsoluteSceneNumbering(forAbsolute, sceneAbsolute) {
            const showId = $('#showID').val();
            const indexer = $('#indexer').val();

            $.getJSON(scRoot + '/home/setSceneNumbering', {
                show: showId,
                indexer,
                forAbsolute,
                sceneAbsolute: sceneAbsolute === '' ? null : sceneAbsolute,
            }, data => {
                // Set the values we get back
                if (data.sceneAbsolute === null) {
                    $('#sceneAbsolute_' + showId + '_' + forAbsolute).val('');
                } else {
                    $('#sceneAbsolute_' + showId + '_' + forAbsolute).val(data.sceneAbsolute);
                }

                if (!data.success) {
                    if (data.errorMessage) {
                        notifyModal(data.errorMessage);
                    } else {
                        notifyModal('Update failed.');
                    }
                }
            });
        }

        function setInputValidInvalid(valid, element) {
            if (valid) {
                $(element).css({'background-color': '#90EE90', color: '#FFF', 'font-weight': 'bold'}); // Green
                return true;
            }

            $(element).css({'background-color': '#FF0000', color: '#FFF!important', 'font-weight': 'bold'}); // Red
            return false;
        }

        $('.sceneSeasonXEpisode').on('change', function () {
            // Strip non-numeric characters
            $(this).val($(this).val().replaceAll(/[^\dx]*/gi, ''));
            const forSeason = $(this).attr('data-for-season');
            const forEpisode = $(this).attr('data-for-episode');
            const m = $(this).val().match(/^(\d+)x(\d+)$/i);
            const onlyEpisode = $(this).val().match(/^(\d+)$/);

            let sceneSeason = null;
            let sceneEpisode = null;
            let isValid;
            if (m) {
                sceneSeason = m[1];
                sceneEpisode = m[2];
                isValid = setInputValidInvalid(true, $(this));
            } else if (onlyEpisode) {
                // For example when '5' is filled in instead of '1x5', asume it's the first season
                sceneSeason = forSeason;
                sceneEpisode = onlyEpisode[1];
                isValid = setInputValidInvalid(true, $(this));
            } else {
                isValid = setInputValidInvalid(false, $(this));
            }

            // Only perform the request when there is a valid input
            if (isValid) {
                setEpisodeSceneNumbering(forSeason, forEpisode, sceneSeason, sceneEpisode);
            }
        });

        $('.sceneAbsolute').on('change', function () {
            // Strip non-numeric characters
            $(this).val($(this).val().replaceAll(/[^\dx]*/gi, ''));
            const forAbsolute = $(this).attr('data-for-absolute');

            const m = $(this).val().match(/^(\d{1,3})$/);
            const sceneAbsolute = m ? m[1] : null;

            setAbsoluteSceneNumbering(forAbsolute, sceneAbsolute);
        });

        $('.addQTip').each(function () {
            $(this).css({cursor: 'help', 'text-shadow': '0px 0px 0.5px #666'});
            $(this).qtip({
                show: {solo: true},
                position: {viewport: $(window), my: 'left center', adjust: {y: -10, x: 2}},
                style: {tip: {corner: true, method: 'polygon'}, classes: 'qtip-rounded qtip-shadow ui-tooltip-sb'},
            });
        });
        $.fn.generateStars = function () {
            return this.each((i, element) => {
                $(element).html($('<span/>').width($(element).text() * 12));
            });
        };

        $('.imdbstars').generateStars();

        $('#popover').popover({
            placement: 'bottom',
            html: true, // Required if content has HTML
            content: '<div id="popover-target"></div>',
        })
        // Bootstrap popover event triggered when the popover opens
            .on('shown.bs.popover', () => {
                $('.displayShowTable').each((index, item) => {
                    $.tablesorter.columnSelector.attachTo(item, '#popover-target');
                });
            });

        // Moved and rewritten this from displayShow. This changes the button when clicked for collapsing/expanding the
        // Season to Show Episodes or Hide Episodes.
        $(() => {
            $('.collapse.toggle').on('hide.bs.collapse', function () {
                const result = /collapseSeason-(\d+)/.exec(this.id);
                $('#showseason-' + result[1]).text(_('Show Episodes'));
            });
            $('.collapse.toggle').on('show.bs.collapse', function () {
                const result = /collapseSeason-(\d+)/.exec(this.id);
                $('#showseason-' + result[1]).text(_('Hide Episodes'));
            });
        });
    },
    editShow() {
        $('#location').fileBrowser({title: _('Select Show Location')});

        SICKCHILL.common.QualityChooser.init();

        $('#anime').on('change', () => {
            SICKCHILL.common.updateBlackWhiteList(getMeta('show.name'));
        });
        if (!$('#anime').is(':checked')) {
            $('#blackwhitelist').hide();
        }

        $('#submit').on('click', () => {
            const allExceptions = $('#exceptions_list').find('optgroup').get().map(group => {
                const season = $(group).data('season');
                const exceptions = $(group).find('option:enabled').get().map(option => {
                    const exception = $(option).val();

                    return encodeURIComponent(exception);
                }).join('|');

                return exceptions.length === 0 ? null : [season, exceptions].join(':');
            }).filter(Boolean);

            $('#exceptions').val(allExceptions);

            if ($('#anime').is(':checked')) {
                generateBlackWhiteList(); // eslint-disable-line no-undef
            }
        });

        $('#addSceneName').on('click', () => {
            const season = $('#SceneSeason').find(':selected').data('season');
            const sceneEx = $('#SceneName').val();

            const group = $('.exceptions_list optgroup[data-season="' + season + '"]').get()[0];
            const placeholder = $(group).find('option.empty');

            const exceptions = new Set($(group).find('option:not(.empty)').get().map(element => $(element).val()));

            // If we already have the exception or the field is empty return
            if (exceptions.has(sceneEx) || sceneEx.trim() === '') {
                $('#SceneName').val('');
                return;
            }

            const newException = $('<option data-season=' + season + '>').text(sceneEx).val(sceneEx);

            $(group).append(newException);
            placeholder.remove();

            $('#SceneName').val('');
        });

        $('#removeSceneName').on('click', () => {
            const option = $('#exceptions_list').find('option:selected');
            const group = option.closest('optgroup');

            if (group.find('option').length < 2) {
                const newOption = $('<option disabled class="empty">');
                newOption.text(_('None'));

                group.append(newOption);
            }

            option.remove();
        });

        $('.custom-image').imageSelector();
    },
    manual_search_show_releases() { // eslint-disable-line camelcase
        $('#manualSearchShowTable:has(tbody tr)').tablesorter({
            widgets: ['zebra', 'filter'],
            textExtraction: (function () {
                return {
                    0(node) { // Provider
                        return $(node).attr('title');
                    },
                };
            })(),
            headers: (function () {
                return {
                    3: {sorter: 'quality'},
                    4: {sorter: 'metric'},
                    7: {sorter: false, filter: false},
                };
            })(),
            widgetOptions: {
                filter_hideFilters: true, // eslint-disable-line camelcase
            },
        });
    },
    postProcess() {
        $('#episodeDir').fileBrowser({
            title: _('Select Unprocessed Episode Folder'),
            key: 'postprocessPath',
        });
    },
    status() {
        $('#schedulerStatusTable').tablesorter({
            widgets: ['saveSort', 'zebra'],
            textExtraction: {
                5(node) {
                    return $(node).data('seconds');
                },
                6(node) {
                    return $(node).data('seconds');
                },
            },
            headers: {
                5: {sorter: 'digit'},
                6: {sorter: 'digit'},
            },
        });
        $('#queueStatusTable').tablesorter({
            widgets: ['saveSort', 'zebra'],
            sortList: [[3, 0], [4, 0], [2, 1]],
        });
    },
    restart() {
        let currentPid = scPID;
        let checkIsAlive = setTimeout(() => {
            setInterval(() => {
                $.post(scRoot + '/home/is-alive/', data => {
                    if (data === undefined || data.msg !== currentPid) {
                        $('#restart_message').show();
                        $('#shut_down_loading').hide();
                        $('#shut_down_success').show();
                    }

                    if (data === undefined || data.msg === 'nope' || data.msg === currentPid) {
                        return;
                    }

                    clearInterval(checkIsAlive);
                    $('#restart_loading').hide();
                    $('#restart_success').show();
                    $('#refresh_message').show();
                    scPID = data.msg;
                    currentPid = data.msg;
                    checkIsAlive = setInterval(() => {
                        $.post(scRoot + '/home/is-alive/', () => { // eslint-disable-line max-nested-callbacks
                            clearInterval(checkIsAlive);
                            setTimeout(() => { // eslint-disable-line max-nested-callbacks
                                window.location = scRoot + '/' + scDefaultPage + '/';
                            }, 3000);
                        }, 'jsonp');
                    }, 1000);
                }, 'jsonp').fail(() => {
                    $('#restart_message').show();
                    $('#shut_down_loading').hide();
                    $('#shut_down_success').show();
                });
            }, 1000);
        }, 5000);
    },
};
