window.SICKCHILL ||= {};
window.SICKCHILL.addShows = {
    init() {
        $('#tabs').tabs({
            collapsible: true,
            selected: (metaToBool('settings.SORT_ARTICLE') ? -1 : 0),
        });

        $.premiereShowPassesFilters = function (element) {
            // Isotope 2 uses this=element; Isotope 3 passes itemElem — support both
            const itemElement = (element && element.nodeType === 1) ? element : this;
            const $item = $(itemElement);

            const requireTvdb = $('#premiere-has-tvdb').is(':checked');
            if (requireTvdb && !($item.attr('data-tvdb-id') || '').trim()) {
                return false;
            }

            const languageMode = $('#premiere-language').val() || 'all';
            if (languageMode === 'english') {
                const language = ($item.attr('data-language') || '').trim().toLowerCase();
                // Missing language keeps the tile (avoid over-filtering incomplete data)
                if (language && language !== 'english') {
                    return false;
                }
            }

            const windowDays = $('#premiere-window').val() || 'all';
            if (windowDays !== 'all') {
                const airdate = ($item.attr('data-airdate') || '').trim();
                if (!airdate) {
                    return false;
                }

                // Parse as local calendar date (avoid UTC off-by-one)
                const parts = airdate.split('-').map(part => Number.parseInt(part, 10));
                if (parts.length !== 3 || parts.some(part => Number.isNaN(part))) {
                    return false;
                }

                const air = new Date(parts[0], parts[1] - 1, parts[2]);
                const start = new Date();
                start.setHours(0, 0, 0, 0);
                const end = new Date(start);
                end.setDate(end.getDate() + Number.parseInt(windowDays, 10));
                if (air < start || air > end) {
                    return false;
                }
            }

            return true;
        };

        $.applyPremiereShowsFilter = function () {
            const $container = $('#container');
            if ($container.length === 0) {
                return;
            }

            const isPremieres = ($('#tmdbList').val() || '') === 'premieres';
            const $items = $container.find('.trakt_show');
            const hasIsotope = Boolean($container.data('isotope'));

            // Mark + show/hide directly so filters work even if Isotope arrange fails
            $items.each(function () {
                const passes = !isPremieres || $.premiereShowPassesFilters(this);
                $(this).toggleClass('premiere-hide', !passes);
                $(this).toggle(passes);
            });

            if (hasIsotope) {
                try {
                    $container.isotope({
                        filter: isPremieres ? ':not(.premiere-hide)' : '*',
                    });
                } catch {
                    // Direct .toggle() above already applied the filter
                }
            }
        };

        $.initRemoteShowGrid = function () {
            const $container = $('#container');
            if ($container.length === 0) {
                return;
            }

            // Shared mapping for init and change handlers (incl. rating_votes → [rating, votes])
            const remoteShowSortCriteria = sortValue => {
                switch (sortValue) {
                    case 'original': {
                        return 'original-order';
                    }

                    case 'rating': {
                        return 'rating';
                    }

                    case 'rating_votes': {
                        return ['rating', 'votes'];
                    }

                    case 'votes': {
                        return 'votes';
                    }

                    case 'rank': {
                        return 'rank';
                    }

                    case 'year': {
                        return 'year';
                    }

                    default: {
                        return 'name';
                    }
                }
            };

            // Preserve page default when "original" is not an option (e.g. IMDb popular uses rank)
            const $showSort = $('#showsort');
            if ($showSort.find('option[value="original"]').length > 0) {
                $showSort.val('original');
            }

            const $showSortDirection = $('#showsortdirection');
            if ($showSortDirection.length > 0 && !$showSortDirection.val()) {
                $showSortDirection.val('asc');
            }

            // Avoid stacking handlers across AJAX reloads of the discovery grid
            $showSort.off('change.remoteShowGrid').on('change.remoteShowGrid', function () {
                /* Randomise first for rating, else rating_votes may already
                     * have sorted leaving this with nothing to do.
                     */
                if (this.value === 'rating') {
                    $container.isotope({sortBy: 'random'});
                }

                $container.isotope({
                    layoutMode: 'masonry',
                    masonry: {
                        isFitWidth: true,
                        horizontalOrder: true,
                    },
                    sortBy: remoteShowSortCriteria(this.value),
                });
            });

            $showSortDirection.off('change.remoteShowGrid').on('change.remoteShowGrid', function () {
                $container.isotope({
                    layoutMode: 'masonry',
                    masonry: {
                        isFitWidth: true,
                        horizontalOrder: true,
                    },
                    sortAscending: (this.value === 'asc'),
                });
            });

            // Apply premiere show/hide before layout so tiles are correct even if Isotope errors
            $.applyPremiereShowsFilter();

            // Replace any prior isotope instance on a freshly injected #container
            if ($container.data('isotope')) {
                try {
                    $container.isotope('destroy');
                } catch {
                    // Ignore destroy errors on a replaced DOM node
                }
            }

            try {
                const isPremieres = ($('#tmdbList').val() || '') === 'premieres';
                const initialSortValue = $showSort.val() || 'original';
                $container.isotope({
                    itemSelector: '.trakt_show',
                    sortBy: remoteShowSortCriteria(initialSortValue),
                    sortAscending: ($showSortDirection.val() || 'asc') === 'asc',
                    layoutMode: 'fitRows',
                    filter: isPremieres ? ':not(.premiere-hide)' : '*',
                    getSortData: {
                        name(itemElement) {
                            const name = $(itemElement).attr('data-name') || '';
                            const regex = new RegExp('^((?:' + getMeta('settings.GRAMMAR_ARTICLES') + String.raw`)\s)`, 'i');
                            return (metaToBool('settings.SORT_ARTICLE') ? name : name.replace(regex, '')).toLowerCase();
                        },
                        rating: '[data-rating] parseInt',
                        votes: '[data-votes] parseInt',
                        rank: '[data-rank] parseInt',
                        year: '[data-year] parseInt',
                    },
                });
            } catch {
                // Filters already applied via .toggle() in applyPremiereShowsFilter
            }
        };

        $.loadTraktImages = function () {
            const url = scRoot + '/addShows/getTrendingShowImage';
            let ajaxCount = 0;
            $('img.trakt-image').each(function () {
                // Only load image from indexer when there is an indexer_id present in data-src-indexer-id
                const indexerId = $(this).attr('data-src-indexer-id');
                if (indexerId) {
                    // Use setTimemout to delay lookup for each lookup
                    // if this is not done, all retrieval of cache urls (by changing the src value) will be done after all retrieval of images
                    // this because the cache urls are appended to the request queue of the browser after the ajax calls for retrieval of images
                    setTimeout(() => {
                        $.post(url, {indexerId}, data => {
                            if (data) {
                                // Replace src with cache location
                                $('img.trakt-image[data-src-indexer-id="' + data + '"]').attr('src', $('img.trakt-image[data-src-indexer-id="' + data + '"]').attr('data-src-cache'));
                            }
                        });
                    }, 300 + (300 * ajaxCount));
                    ajaxCount++;
                } else {
                    // No indexer_id present -> load it directly from cache
                    $(this).attr('src', $(this).attr('data-src-cache'));
                }
            });
        };

        $.fn.loadRemoteShows = function (path, loadingTxt, errorTxt) {
            // Abort prior in-flight load on this element and ignore stale callbacks so a
            // newer list selection cannot be overwritten by an older response.
            return this.each(function () {
                const $element = $(this);
                const previous = $element.data('remoteShowsXhr');
                if (previous && typeof previous.abort === 'function') {
                    previous.abort();
                }

                const requestId = ($element.data('remoteShowsRequestId') || 0) + 1;
                $element.data('remoteShowsRequestId', requestId);

                $element.html('<img id="searchingAnim" src="' + scRoot + '/images/loading32' + themeSpinner + '.gif" alt="loading" height="32" width="32" />&nbsp;' + loadingTxt);

                const xhr = $.ajax({
                    url: scRoot + path,
                    dataType: 'html',
                    success(html) {
                        if ($element.data('remoteShowsRequestId') !== requestId) {
                            return;
                        }

                        // Same filter as former .load(url + ' #container')
                        const $container = $('<div>').append($.parseHTML(html)).find('#container');
                        $element.html($container.length > 0 ? $container : html);
                        $.initRemoteShowGrid();
                        $.loadTraktImages();
                    },
                    error(jqXHR, textStatus) {
                        if ($element.data('remoteShowsRequestId') !== requestId || textStatus === 'abort') {
                            return;
                        }

                        $element.empty().html(errorTxt);
                    },
                    complete() {
                        if ($element.data('remoteShowsXhr') === xhr) {
                            $element.removeData('remoteShowsXhr');
                        }
                    },
                });
                $element.data('remoteShowsXhr', xhr);
            });
        };

        $('#saveDefaultsButton').on('click', function () {
            const anyQualArray = [];
            const bestQualArray = [];
            $('#anyQualities option:selected').each((i, d) => {
                anyQualArray.push($(d).val());
            });
            $('#bestQualities option:selected').each((i, d) => {
                bestQualArray.push($(d).val());
            });
            const grpwhitelistArray = [];
            const grpblacklistArray = [];
            $('#white option').each((i, d) => {
                grpwhitelistArray.push($(d).val());
            });
            $('#black option').each((i, d) => {
                grpblacklistArray.push($(d).val());
            });
            generateBlackWhiteList(); // eslint-disable-line no-undef
            $.post(scRoot + '/config/general/saveAddShowDefaults', {
                defaultStatus: $('#statusSelect').val(),
                anyQualities: anyQualArray,
                bestQualities: bestQualArray,
                defaultSeasonFolders: $('#season_folders').is(':checked'),
                subtitles: $('#subtitles').is(':checked'),
                anime: SICKCHILL.common.isAnimeFormatSelected(),
                scene: $('#scene').is(':checked'),
                defaultStatusAfter: $('#statusSelectAfter').val(),
                whitelist: grpwhitelistArray,
                blacklist: grpblacklistArray,
            });

            $(this).attr('disabled', true);
        });

        $('#statusSelect, #qualityPreset, #season_folders, #anyQualities, #bestQualities, #subtitles, #scene, #anime, #statusSelectAfter, #white, #black').on('change', () => {
            $('#saveDefaultsButton').attr('disabled', false);
        });

        SICKCHILL.common.QualityChooser.init();
    },
    index() {},
    newShow() {
        const updateSampleText = function () {
            // If something's selected then we have some behavior to figure out
            const object = {
                showName: '',
                dir: 'unknown dir.',
                sepChar: '',
            };

            // If they've picked a radio button then use that
            if ($('input:radio[name=whichSeries]:checked').length > 0) {
                object.showName = $('input:radio[name=whichSeries]:checked').val().split('|', 5)[4];
            } else if ($('input:hidden[name=whichSeries]').length > 0 && $('input:hidden[name=whichSeries]').val().length > 0) {
                // If we provided a show in the hidden field, use that
                object.showName = $('#providedName').val();
            }

            SICKCHILL.common.updateBlackWhiteList(object.showName);

            // If we have a root dir selected, figure out the path
            if ($('#rootDirs option:selected').length > 0) {
                object.dir = $('#rootDirs option:selected').val();

                if (object.dir.includes('/')) {
                    object.sepChar = '/';
                } else if (object.dir.includes('\\')) {
                    object.sepChar = '\\';
                }

                object.dir.trim(object.sepChar);
                object.dir += object.sepChar;
            } else if ($('#fullShowPath').val()) {
                object.dir = $('#fullShowPath').val();
            }

            // If we have a show name then sanitize and use it for the dir name
            if (object.showName.length > 0) {
                $.post(scRoot + '/addShows/sanitizeFileName', {name: object.showName}, data => {
                    $('#desc-show-name').text(object.showName);
                    if (object.dir === $('#fullShowPath').val()) {
                        $('#desc-directory-name').html(object.dir);
                    } else {
                        $('#desc-directory-name').html(object.dir + data + object.sepChar);
                    }
                });
            } else { // If not then it's unknown
                $('#desc-show-name').text(object.showName);
                $('#desc-directory-name').html(object.dir);
            }

            $('#desc-quality-name').text($('#qualityPreset option:selected').text());

            // If show has been selected and root dir has been set properly
            if (!($('input:radio[name=whichSeries]:checked').val() || $('input:hidden[name=whichSeries]').val())
                || !($('#rootDirs option:selected').val() || $('#fullShowPath').val())) {
                return $('#addShowButton').attr('disabled', true);
            }

            $('#addShowButton').attr('disabled', false);
        };

        const showGroupPicker = function () {
            const animeOn = SICKCHILL.common.isAnimeFormatSelected();
            $('#anime-extras, #anime-numbering').toggle(animeOn);
            $('#blackwhitelist').toggle(animeOn);
        };

        const buildTable = function (shows) {
            let table
                = '<div class="row">'
                    + '<div class="col-lg-10 col-md-12">'
                    + '<table class="sickchillTable new-show-table tablesorter">'
                    + '<thead>'
                    + '<tr>'
                    + '<th></th>'
                    + '<th>Show Name</th>'
                    + '<th>Network</th>'
                    + '<th>Premiere</th>'
                    + '<th>Score</th>'
                    + '<th>Indexer</th>'
                    + '</tr>'
                    + '</thead>'
                    + '<tbody>';

            // Do not pre-select a show; user must choose explicitly
            for (const show of shows) {
                const sourceTag = show.source === 'tvmaze'
                    ? ' <span class="label label-info" title="Resolved via TVmaze fallback">TVmaze</span>'
                    : '';
                const titleEsc = $('<div>').text(show.title || '').html();
                const networkEsc = $('<div>').text(show.network || '').html();
                const scoreInt = Number.isFinite(Number(show.score)) ? Math.round(Number(show.score)) : 0;
                table
                    += '<tr class="' + (show.inShowList ? 'in-list' : '') + '">'
                        + '<td>'
                        + '<input type="radio" class="whichSeries" name="whichSeries" value="' + show.obj + '" '
                        + (show.inShowList ? 'disabled' : '') + '/>'
                        + '</td>'
                        + '<td>'
                        + (function () {
                            let string = '<a href=';
                            string += show.inShowList ? '"/home/displayShow?show=' + show.id + '"' : '"' + show.url + '" target="_blank"';
                            string += '>' + titleEsc + '</a>' + sourceTag;
                            return string;
                        })()
                        + '</td>'
                        + '<td>' + networkEsc + '</td>'
                        + '<td>' + $('<div>').text(show.debut || '').html() + '</td>'
                        + '<td data-text="' + scoreInt + '">' + scoreInt + '</td>'
                        + '<td>' + $('<div>').text(show.indexer || '').html() + '</td>'
                        + '</tr>';
            }

            table
                += '</tbody>'
                    + '</table>'
                    + '</div>'
                    + '</div>';

            return table;
        };

        let searchRequestXhr = null;
        const searchIndexers = function () {
            if (searchRequestXhr) {
                searchRequestXhr.abort();
            }

            const displayName = ($('#show-name').val() || '').trim();
            const discoveryIndexerId = ($('#discovery-indexer-id').val() || '').trim();
            // Prefer verified TVDB id from discovery Add; keep title visible in the box
            let searchTerm = displayName;
            let exact = $('#exact-match').is(':checked') ? 1 : 0;
            if (discoveryIndexerId) {
                searchTerm = discoveryIndexerId;
                exact = 0;
                $('#discovery-indexer-id').val('');
            }

            if (!searchTerm) {
                return;
            }

            const searchingLabel = discoveryIndexerId && displayName
                ? (displayName + ' [TVDB ' + discoveryIndexerId + ']')
                : searchTerm;
            const searchingFor = _(searchingLabel + ' on ' + $('#providedIndexer option:selected').text() + ' in ' + $('#indexerLangSelect option:selected').text());
            // Build status with text nodes so displayName / ids cannot be interpreted as HTML
            const statusText = _('searching {searchingFor}...').replaceAll('{searchingFor}', () => searchingFor);
            $('#searchResults').empty().append(
                $('<img>', {
                    id: 'searchingAnim',
                    src: scRoot + '/images/loading32' + themeSpinner + '.gif',
                    alt: 'loading',
                    height: 32,
                    width: 32,
                }),
                document.createTextNode(' ' + statusText),
            );

            searchRequestXhr = $.post({
                url: scRoot + '/addShows/searchIndexersForShowName',
                data: {
                    search_term: searchTerm, // eslint-disable-line camelcase
                    exact,
                    lang: $('#indexerLangSelect').val(),
                    indexer: $('#providedIndexer').val(),
                },
                timeout: Number.parseInt($('#indexer_timeout').val(), 10) * 1000,
                dataType: 'json',
                error() {
                    $('#searchResults').empty().html(_('search timed out, try again or try another indexer'));
                    $('.next-steps').hide();
                },
                success(data) {
                    let resultString = '<legend class="legendStep">#2 Pick a Show</legend>';
                    if (data.results.length === 0) {
                        resultString += '<b>No results found, try a different search.</b>';
                        $('.next-steps').hide();
                    } else {
                        const shows = [];

                        $.each(data.results, (index, object) => {
                            let show;
                            // Prefer object results (Phase 3); keep array/tuple fallback for safety
                            if (object && !Array.isArray(object) && typeof object === 'object') {
                                const whichSeries = (object.whichSeries || [
                                    object.indexer,
                                    object.indexer_id,
                                    object.show_url,
                                    object.id,
                                    object.seriesName,
                                    object.firstAired,
                                    object.inShowList ? '1' : '0',
                                ].join('|')).replaceAll('"', '');
                                show = {
                                    obj: whichSeries,
                                    indexer: object.indexer,
                                    id: object.id,
                                    title: object.seriesName,
                                    debut: object.firstAired,
                                    inShowList: Boolean(object.inShowList),
                                    url: anonURL + (object.show_url || '') + object.id,
                                    score: object.score ?? 0,
                                    network: object.network || '',
                                    source: object.source || 'tvdb',
                                };
                            } else {
                                const whichSeries = object.join('|').replaceAll('"', '');
                                show = {
                                    obj: whichSeries,
                                    indexer: object[0],
                                    id: object[3],
                                    title: object[4],
                                    debut: object[5],
                                    inShowList: object[6],
                                    url: anonURL + object[2] + object[3],
                                    score: 0,
                                    network: '',
                                    source: 'tvdb',
                                };
                            }

                            if (data.langid) {
                                show.url += '&lid=' + data.langid;
                            }

                            shows.push(show);
                        });

                        resultString += buildTable(shows);

                        $('.next-steps').show();
                    }

                    $('#searchResults').html(resultString);
                    updateSampleText();
                    // Default sort: Score descending. Omit saveSort so a prior column choice
                    // does not override score as the default order on each search.
                    $('.new-show-table').tablesorter({
                        widgets: ['stickyHeaders', 'zebra'],
                        headers: {
                            0: {sorter: false},
                            4: {sorter: 'digit'}, // Score (0–100)
                        },
                        sortList: [[4, 1]], // Score column, descending
                    });
                },
            });
        };

        $('#search-button').on('click', searchIndexers);

        $('#addShowButton').on('click', () => {
            // Radio pick from search, or hidden id from addShowByID / provided metadata
            const whichSeries = $('input:radio[name="whichSeries"]:checked').val()
                || $('input:hidden[name="whichSeries"]').val();
            if (!whichSeries) {
                notifyModal('You must choose a show to continue');
                return false;
            }

            generateBlackWhiteList(); // eslint-disable-line no-undef
            $('#addShowForm').submit();
        });

        $('#anime').on('change', () => {
            showGroupPicker();
            updateSampleText();
        });

        $('#skipShowButton').on('click', () => {
            $('#skipShow').val('1');
            $('#addShowForm').submit();
        });

        $('#rootDirText').change(updateSampleText);
        $('#qualityPreset').change(updateSampleText);
        $('#searchResults').on('change', '.whichSeries', updateSampleText);

        $('#show-name').on('focus keyup', event => {
            if (event.keyCode === 13) { // Enter
                $('#search-button').click();
            }
        });

        if ($('#show-name').val()) {
            $('#search-button').click();
        }

        updateSampleText();
        showGroupPicker();
    },
    addExistingShow() {
        $('#tableDiv').on('click', '#checkAll', function () {
            const seasCheck = this.checked;
            $('.dirCheck').each(function () {
                this.checked = seasCheck;
            });
        });

        $('#submitShowDirs').on('click', () => {
            const submitForm = $('#addShowForm');
            let isSelectedShows = false;
            $('.dirCheck').each(function () {
                if (this.checked !== true) {
                    return;
                }

                const show = $(this).attr('id');
                const indexer = $(this).closest('tr').find('select').val();
                $('<input>', {
                    type: 'hidden',
                    name: 'shows_to_add',
                    value: indexer + '|' + show,
                }).appendTo(submitForm);
                isSelectedShows = true;
            });

            if (isSelectedShows === false) {
                return false;
            }

            $('<input>', {
                type: 'hidden',
                name: 'promptForSettings',
                value: $('#promptForSettings').is(':checked') ? 'on' : 'off',
            }).appendTo(submitForm);

            submitForm.submit();
        });

        function loadContent() {
            let url = '';
            $('.dir_check').each((i, w) => {
                if (!$(w).is(':checked')) {
                    return;
                }

                if (url.length > 0) {
                    url += '&';
                }

                url += 'rootDir=' + encodeURIComponent($(w).attr('id'));
            });

            $('#tableDiv').html('<img id="searchingAnim" src="' + scRoot + '/images/loading32.gif" alt="loading" height="32" width="32" /> ' + _('loading folders...'));
            $.post(scRoot + '/addShows/massAddTable/', url, data => {
                $('#tableDiv').html(data);
                $('#addRootDirTable').tablesorter({
                    // SortList: [[1,0]],
                    widgets: ['zebra'],
                    headers: {
                        0: {sorter: false},
                    },
                });
            });
        }

        let lastTxt = '';
        // Keep: without this, the root-dirs table may not populate on load.
        const rootDirectoriesWorkaround = function () {
            if (lastTxt === $('#rootDirText').val()) {
                return false;
            }

            lastTxt = $('#rootDirText').val();

            $('#rootDirStaticList').html('');
            $('#rootDirs option').each((i, w) => {
                const dir = $(w).val();
                const dirItem = '<li class="ui-state-default ui-corner-all">'
                    + '<input type="checkbox" class="cb dir_check" id="' + dir + '" checked=checked>'
                    + ' <label for="' + dir + '">' + dir + '</label></li>';
                $('#rootDirStaticList').append(dirItem);
            });
            loadContent();
        };

        rootDirectoriesWorkaround();

        $('#rootDirText').on('change', rootDirectoriesWorkaround);

        $('#rootDirStaticList').on('click', '.dir_check', loadContent);
    },
    recommendedShows() {
        $('#recommendedShows').loadRemoteShows(
            '/addShows/getRecommendedShows/',
            'Loading recommended shows...',
            'Trakt timed out, refresh page to try again',
        );
    },
    trendingShows() {
        const discoverySource = () => ($('#discoverySource').val() || 'tmdb');
        const listParameter = () => discoverySource() === 'trakt' ? $('#traktList').val() || 'anticipated' : $('#tmdbList').val() || 'trending';

        const listQueryParameter = () => (discoverySource() === 'trakt' ? 'traktList' : 'tmdbList');
        const syncPremiereFilters = listKey => {
            if (discoverySource() === 'tmdb' && listKey === 'premieres') {
                $('#premiereFilters').show();
            } else {
                $('#premiereFilters').hide();
            }
        };

        const loadDiscoveryShows = listKey => {
            const parameter = listQueryParameter();
            const loadingTxt = discoverySource() === 'trakt' ? 'Loading Trakt shows...' : 'Loading discovery shows...';
            const errorTxt = discoverySource() === 'trakt'
                ? 'Trakt timed out, refresh page to try again'
                : 'List request timed out, refresh page to try again';
            $('#trendingShows').loadRemoteShows(
                '/addShows/getTrendingShows/?' + parameter + '=' + listKey,
                loadingTxt,
                errorTxt,
            );
        };

        const initialListKey = listParameter();
        syncPremiereFilters(initialListKey);
        loadDiscoveryShows(initialListKey);

        $('#traktlistselection').on('change', event => {
            const listKey = event.target.value;
            const parameter = listQueryParameter();
            if (discoverySource() === 'trakt') {
                $('#traktList').val(listKey);
                $('#tmdbList').val('');
            } else {
                $('#tmdbList').val(listKey);
                $('#traktList').val('');
            }

            window.history.replaceState({}, document.title, '?' + parameter + '=' + listKey);
            syncPremiereFilters(listKey);
            loadDiscoveryShows(listKey);
        });

        $('#premiere-window, #premiere-language').on('change', () => {
            $.applyPremiereShowsFilter();
        });
        $('#premiere-has-tvdb').on('change', () => {
            $.applyPremiereShowsFilter();
        });
    },
    popularShows() {
        $.initRemoteShowGrid();
    },
};
