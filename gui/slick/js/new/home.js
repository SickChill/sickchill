$(document).ready(function(){
    // Resets the tables sorting, needed as we only use a single call for both tables in tablesorter
    $('.resetsorting').on('click', function(){
        $('table').trigger('filterReset');
    });

    // This needs to be refined to work a little faster.
    $('.progressbar').each(function(progressbar){
        var showId = $(this).data('show-id');
        var percentage = $(this).data('progress-percentage');
        var classToAdd = percentage === 100 ? 100 : percentage > 80 ? 80 : percentage > 60 ? 60 : percentage > 40 ? 40 : 20;
        $(this).progressbar({ value:  percentage });
        if($(this).data('progress-text')) {
            $(this).append('<div class="progressbarText" title="' + $(this).data('progress-tip') + '">' + $(this).data('progress-text') + '</div>');
        }
        $(this).find('.ui-progressbar-value').addClass('progress-' + classToAdd);
    });

    $("img#network").on('error', function(){
        $(this).parent().text($(this).attr('alt'));
        $(this).remove();
    });

    $("#showListTableShows:has(tbody tr), #showListTableAnime:has(tbody tr)").tablesorter({
        sortList: [[7,1],[2,0]],
        textExtraction: {
            0: function(node) { return $(node).find('time').attr('datetime'); },
            1: function(node) { return $(node).find('time').attr('datetime'); },
            3: function(node) { return $(node).find("span").prop("title").toLowerCase(); },
            4: function(node) { return $(node).find("span").text().toLowerCase(); },
            5: function(node) { return $(node).find("span:first").text(); },
            6: function(node) { return $(node).find("img").attr("alt"); }
        },
        widgets: ['saveSort', 'zebra', 'stickyHeaders', 'filter', 'columnSelector'],
        headers: (function(){
            if(metaToBool('sickbeard.FILTER_ROW')){
                return {
                    0: { sorter: 'realISODate' },
                    1: { sorter: 'realISODate' },
                    2: { sorter: 'loadingNames' },
                    4: { sorter: 'quality' },
                    5: { sorter: 'eps' },
                    6: { filter : 'parsed' }
                };
            } else {
                return {
                    0: { sorter: 'realISODate' },
                    1: { sorter: 'realISODate' },
                    2: { sorter: 'loadingNames' },
                    4: { sorter: 'quality' },
                    5: { sorter: 'eps' }
                };
            }
        }()),
        widgetOptions: (function(){
            if(metaToBool('sickbeard.FILTER_ROW')){
                return {
                    filter_columnFilters: true, // jshint ignore:line
                    filter_hideFilters : true, // jshint ignore:line
                    filter_saveFilters : true, // jshint ignore:line
                    filter_functions : { // jshint ignore:line
                       5:function(e, n, f, i, r, c) {
                            var test = false;
                            var pct = Math.floor((n % 1) * 1000);
                            if (f === '') {
                               test = true;
                            } else {
                                var result = f.match(/(<|<=|>=|>)\s(\d+)/i);
                                if (result) {
                                    if (result[1] === "<") {
                                        if (pct < parseInt(result[2])) {
                                            test = true;
                                        }
                                    } else if (result[1] === "<=") {
                                        if (pct <= parseInt(result[2])) {
                                            test = true;
                                        }
                                    } else if (result[1] === ">=") {
                                        if (pct >= parseInt(result[2])) {
                                            test = true;
                                        }
                                    } else if (result[1] === ">") {
                                        if (pct > parseInt(result[2])) {
                                            test = true;
                                        }
                                    }
                                }

                                result = f.match(/(\d+)\s(-|to)\s(\d+)/i);
                                if (result) {
                                    if ((result[2] === "-") || (result[2] === "to")) {
                                        if ((pct >= parseInt(result[1])) && (pct <= parseInt(result[3]))) {
                                            test = true;
                                        }
                                    }
                                }

                                result = f.match(/(=)?\s?(\d+)\s?(=)?/i);
                                if (result) {
                                    if ((result[1] === "=") || (result[3] === "=")) {
                                        if (parseInt(result[2]) === pct) {
                                            test = true;
                                        }
                                    }
                                }

                                if (!isNaN(parseFloat(f)) && isFinite(f)) {
                                    if (parseInt(f) === pct) {
                                        test = true;
                                    }
                                }
                            }
                            return test;
                        }
                    },
                    columnSelector_mediaquery: false
                };
            } else {
                return {
                    filter_columnFilters: false
                };
            }
        }()),
        sortStable: true,
        sortAppend: [[2,0]]
    });

    if ($("#showListTableShows").find("tbody").find("tr").size() > 0){
        $.tablesorter.filter.bindSearch( "#showListTableShows", $('.search') );
    }

    if(metaToBool('sickbeard.ANIME_SPLIT_HOME')){
        if($("#showListTableAnime").find("tbody").find("tr").size() > 0){
            $.tablesorter.filter.bindSearch( "#showListTableAnime", $('.search') );
        }
    }

    var $container = [$('#container'), $('#container-anime')];

    $.each($container, function (j){
        this.isotope({
            itemSelector: '.show',
            sortBy : getMeta('sickbeard.POSTER_SORTBY'),
            sortAscending: getMeta('sickbeard.POSTER_SORTDIR'),
            layoutMode: 'masonry',
            masonry: {
                columnWidth: 13,
                isFitWidth: true
            },
            getSortData: {
                name: function(itemElem){
                    var name = $(itemElem).attr('data-name');
                    return (metaToBool('sickbeard.SORT_ARTICLE') ? (name || '') : (name || '').replace(/^(The|A|An)\s/i,''));
                },
                network: '[data-network]',
                date: function(itemElem){
                    var date = $(itemElem).attr('data-date');
                    return date.length && parseInt(date, 10) || Number.POSITIVE_INFINITY;
                },
                progress: function(itemElem){
                    var progress = $(itemElem).attr('data-progress');
                    return progress.length && parseInt(progress, 10) || Number.NEGATIVE_INFINITY;
                }
            }
        });
    });

    $('#postersort').on('change', function(){
        var sortValue = this.value;
        $('#container').isotope({sortBy: sortValue});
        $('#container-anime').isotope({sortBy: sortValue});
        $.get(this.options[this.selectedIndex].getAttribute('data-sort'));
    });

    $('#postersortdirection').on('change', function(){
        var sortDirection = this.value;
        sortDirection = sortDirection == 'true';
        $('#container').isotope({sortAscending: sortDirection});
        $('#container-anime').isotope({sortAscending: sortDirection});
        $.get(this.options[this.selectedIndex].getAttribute('data-sort'));
    });

    $('#popover').popover({
        placement: 'bottom',
        html: true, // required if content has HTML
        content: '<div id="popover-target"></div>'
    }).on('shown.bs.popover', function () { // bootstrap popover event triggered when the popover opens
        // call this function to copy the column selection code into the popover
        $.tablesorter.columnSelector.attachTo( $('#showListTableShows'), '#popover-target');
        if(metaToBool('sickbeard.ANIME_SPLIT_HOME')){
            $.tablesorter.columnSelector.attachTo( $('#showListTableAnime'), '#popover-target');
        }

    });
});
