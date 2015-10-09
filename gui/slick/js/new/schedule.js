$(document).ready(function(){
    if(isMeta('sickbeard.COMING_EPS_LAYOUT', ['list'])){
        var sortCodes = {'date': 0, 'show': 2, 'network': 5};
        var sort = getMeta('sickbeard.COMING_EPS_SORT');
        var sortList = (sort in sortCodes) ? [[sortCodes[sort], 0]] : [[0, 0]];

        $('#showListTable:has(tbody tr)').tablesorter({
            widgets: ['stickyHeaders', 'filter', 'columnSelector', 'saveSort'],
            sortList: sortList,
            textExtraction: {
                0: function(node) { return $(node).find('time').attr('datetime'); },
                1: function(node) { return $(node).find('time').attr('datetime'); },
                7: function(node) { return $(node).find('span').text().toLowerCase(); }
            },
            headers: {
                0: { sorter: 'realISODate' },
                1: { sorter: 'realISODate' },
                2: { sorter: 'loadingNames' },
                4: { sorter: 'loadingNames' },
                7: { sorter: 'quality' },
                8: { sorter: false },
                9: { sorter: false }
            },
            widgetOptions: (function() {
                if (metaToBool('sickbeard.FILTER_ROW')) {
                    return {
                        filter_columnFilters: true,
                        filter_hideFilters: true,
                        filter_saveFilters: true,
                        columnSelector_mediaquery: false
                    };
                } else {
                    return {
                        filter_columnFilters: false,
                        columnSelector_mediaquery: false
                    };
                }
            }())
        });

        $('#srRoot').ajaxEpSearch();
    }

    if(isMeta('sickbeard.COMING_EPS_LAYOUT', ['banner', 'poster'])){
        $('#srRoot').ajaxEpSearch({'size': 16, 'loadingImage': 'loading16' + themeSpinner + '.gif'});
        $('.ep_summary').hide();
        $('.ep_summaryTrigger').click(function() {
            $(this).next('.ep_summary').slideToggle('normal', function() {
                $(this).prev('.ep_summaryTrigger').attr('src', function(i, src) {
                    return $(this).next('.ep_summary').is(':visible') ? src.replace('plus','minus') : src.replace('minus','plus');
                });
            });
        });
    }

    $('#popover').popover({
        placement: 'bottom',
        html: true, // required if content has HTML
        content: '<div id="popover-target"></div>'
    }).on('shown.bs.popover', function () { // bootstrap popover event triggered when the popover opens
        // call this function to copy the column selection code into the popover
        $.tablesorter.columnSelector.attachTo( $('#showListTable'), '#popover-target');
    });
});
