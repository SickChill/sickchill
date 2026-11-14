window.SICKCHILL ||= {};
window.SICKCHILL.schedule = {
    init() {
        // Set webcal link for calendar subscription
        $('.btn-cal-subscribe').attr('href', document.location.href.replace(/https?/, 'webcal').replace(/schedule.*/, 'calendar'));
    },
    index() {
        if (isMeta('settings.COMING_EPS_LAYOUT', ['list'])) {
            // Columns: 0 airdate, 2 show, 4 next ep, 6 network.
            // sortAppend keeps show then episode as tiebreakers even when saveSort
            // restores a single-column airdate sort (which previously interleaved
            // same-time shows by episode number alone).
            const sortLists = {
                date: [[0, 0], [2, 0], [4, 0]],
                show: [[2, 0], [0, 0], [4, 0]],
                network: [[6, 0], [0, 0], [2, 0], [4, 0]],
            };
            const sort = getMeta('settings.COMING_EPS_SORT');
            const sortList = Object.hasOwn(sortLists, sort) ? sortLists[sort] : [[0, 0], [2, 0], [4, 0]];

            $('#showListTable:has(tbody tr)').tablesorter({
                widgets: ['stickyHeaders', 'filter', 'columnSelector', 'saveSort'],
                sortList,
                sortAppend: [[2, 0], [4, 0]],
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
                    7(node) {
                        return $(node).find('span').text().toLowerCase();
                    },
                },
                headers: {
                    0: {sorter: 'realISODate'},
                    1: {sorter: 'realISODate'},
                    2: {sorter: 'loadingNames'},
                    4: {sorter: 'loadingNames'},
                    7: {sorter: 'quality'},
                    8: {sorter: false},
                    9: {sorter: false},
                },
                widgetOptions: {
                    filter_columnFilters: true, // eslint-disable-line camelcase
                    filter_hideFilters: true, // eslint-disable-line camelcase
                    filter_saveFilters: false, // eslint-disable-line camelcase
                    columnSelector_mediaquery: false, // eslint-disable-line camelcase
                    stickyHeaders_offset: 50, // eslint-disable-line camelcase
                    filter_reset: '.resetsorting', // eslint-disable-line camelcase
                },
            });

            $(document).ajaxEpSearch();
        }

        if (isMeta('settings.COMING_EPS_LAYOUT', ['banner', 'poster'])) {
            $(document).ajaxEpSearch();
            $('.ep_summary').hide();
            $('.ep_summaryTrigger').on('click', function () {
                $(this).next('.ep_summary').slideToggle('normal', function () {
                    $(this).prev('.ep_summaryTrigger').attr('src', function (i, source) {
                        return $(this).next('.ep_summary').is(':visible') ? source.replace('plus', 'minus') : source.replace('minus', 'plus');
                    });
                });
            });
        }

        $('#popover').popover({
            placement: 'bottom',
            html: true, // Required if content has HTML
            content: '<div id="popover-target"></div>',
        }).on('shown.bs.popover', () => { // Bootstrap popover event triggered when the popover opens
            // call this function to copy the column selection code into the popover
            $.tablesorter.columnSelector.attachTo($('#showListTable'), '#popover-target');
        });

        $('#sort, #viewpaused, #viewsnatched, #layout').on('change', function () {
            window.location.assign($(this).find('option:selected').val());
        });
    },
};
