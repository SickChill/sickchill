if($('meta[data-var="sickbeard.COMING_EPS_LAYOUT"]').data('content') == 'list'){
    $.tablesorter.addParser({
        id: 'loadingNames',
        is: function(s) {
            return false;
        },
        format: function(s) {
            if (0 === s.indexOf('Loading...')){
                return s.replace('Loading...', '000');
            } else {
                return ($('meta[data-var="sickbeard.SORT_ARTICLE"]').data('content') == 'False' ? (s || '') : (s || '').replace(/^(The|A|An)\s/i,''));
            }
        },
        type: 'text'
    });
    $.tablesorter.addParser({
        id: 'quality',
        is: function(s) {
            return false;
        },
        format: function(s) {
            return s.replace('hd1080p', 5).replace('hd720p', 4).replace('hd', 3).replace('sd', 2).replace('any', 1).replace('best', 0).replace('custom', 7);
        },
        type: 'numeric'
    });
    $.tablesorter.addParser({
        id: 'cDate',
        is: function(s) {
            return false;
        },
        format: function(s) {
            return new Date(s).getTime();
        },
        type: 'numeric'
    });
}

$(document).ready(function(){
    if($('meta[data-var="sickbeard.COMING_EPS_LAYOUT"]').data('content') == 'list'){
        var sortCodes = {'date': 0, 'show': 1, 'network': 4};
        var sort = $('meta[data-var="sickbeard.COMING_EPS_SORT"]').data('content');
        var sortList = (sort in sortCodes) ? [[sortCodes[sort], 0]] : [[0, 0]];

        $('#showListTable:has(tbody tr)').tablesorter({
            widgets: ['stickyHeaders'],
            sortList: sortList,
            textExtraction: {
                0: function(node) { return $(node).find('time').attr('datetime'); },
                5: function(node) { return $(node).find('span').text().toLowerCase(); }
            },
            headers: {
                0: { sorter: 'cDate' },
                1: { sorter: 'loadingNames' },
                2: { sorter: false },
                3: { sorter: false },
                4: { sorter: 'loadingNames' },
                5: { sorter: 'quality' },
                6: { sorter: false },
                7: { sorter: false },
                8: { sorter: false }
            }
        });

        $('#sbRoot').ajaxEpSearch();
    }
    if($('meta[data-var="sickbeard.COMING_EPS_LAYOUT"]').data('content') == 'banner' || $('meta[data-var="sickbeard.COMING_EPS_LAYOUT"]').data('content') == 'poster'){
        $('#sbRoot').ajaxEpSearch({'size': 16, 'loadingImage': 'loading16' + themeSpinner + '.gif'});
        $('.ep_summary').hide();
        $('.ep_summaryTrigger').click(function() {
            $(this).next('.ep_summary').slideToggle('normal', function() {
                $(this).prev('.ep_summaryTrigger').attr('src', function(i, src) {
                    return $(this).next('.ep_summary').is(':visible') ? src.replace('plus','minus') : src.replace('minus','plus');
                });
            });
        });
    }
});

setTimeout(function () {
    "use strict";
    location.reload(true);
}, 60000);
