$.tablesorter.addParser({
    id: 'loadingNames',
    is: function(s) {
        return false;
    },
    format: function(s) {
        if (s.indexOf('Loading...') === 0)
          return s.replace('Loading...','000');
        else
        return ($('meta[data-var="sickbeard.SORT_ARTICLE"]').data('content') == 'True' ? (s || '') : (s || '').replace(/^(The|A|An)\s/i,''));
    },
    type: 'text'
});

$.tablesorter.addParser({
    id: 'quality',
    is: function(s) {
        return false;
    },
    format: function(s) {
        return s.replace('hd1080p',5).replace('hd720p',4).replace('hd',3).replace('sd',2).replace('any',1).replace('custom',7);
    },
    type: 'numeric'
});

$.tablesorter.addParser({
    id: 'eps',
    is: function(s) {
        return false;
    },
    format: function(s) {
        match = s.match(/^(.*)/);

        if (match === null || match[1] == "?") return -10;

        var nums = match[1].split(" / ");
        if (nums[0].indexOf("+") != -1) {
            var num_parts = nums[0].split("+");
            nums[0] = num_parts[0];
        }

        nums[0] = parseInt(nums[0]);
        nums[1] = parseInt(nums[1]);

        if (nums[0] === 0)
          return nums[1];

        var finalNum = parseInt(($('meta[data-var="max_download_count"]').data('content'))*nums[0]/nums[1]);
        var pct = Math.round((nums[0]/nums[1])*100) / 1000;
        if (finalNum > 0)
          finalNum += nums[0];

        return finalNum + pct;
    },
    type: 'numeric'
});

$(document).ready(function(){
    // Resets the tables sorting, needed as we only use a single call for both tables in tablesorter
    $('.resetsorting').on('click', function(){
        $('table').trigger('filterReset');
    });

    // This needs to be refined to work a little faster.
    $('.progressbar').each(function(progressbar){
        var showId = $(this).data('show-id');
        var percentage = $(this).data('progress-percentage');
        var classToAdd = percentage == 100 ? 100 : percentage > 80 ? 80 : percentage > 60 ? 60 : percentage > 40 ? 40 : 20;
        $(this).progressbar({ value:  percentage });
        if($(this).data('progress-text')) $(this).append('<div class="progressbarText" title="' + $(this).data('progress-tip') + '">' + $(this).data('progress-text') + '</div>');
        $(this).find('.ui-progressbar-value').addClass('progress-' + classToAdd);
    });

    $("img#network").on('error', function(){
        $(this).parent().text($(this).attr('alt'));
        $(this).remove();
    });

    $("#showListTableShows:has(tbody tr), #showListTableAnime:has(tbody tr)").tablesorter({
        sortList: [[7,1],[2,0]],
        textExtraction: {
            0: function(node) { return $(node).find("span").text().toLowerCase(); },
            1: function(node) { return $(node).find("span").text().toLowerCase(); },
            3: function(node) { return $(node).find("span").prop("title").toLowerCase(); },
            4: function(node) { return $(node).find("span").text().toLowerCase(); },
            5: function(node) { return $(node).find("span:first").text(); },
            6: function(node) { return $(node).find("img").attr("alt"); }
        },
        widgets: ['saveSort', 'zebra', 'stickyHeaders', 'filter', 'columnSelector'],
        headers: (function(){
            if($('meta[data-var="sickbeard.FILTER_ROW"]').data('content') == 'True'){
                return {
                    0: { sorter: 'isoDate' },
                    1: { columnSelector: false },
                    2: { sorter: 'loadingNames' },
                    4: { sorter: 'quality' },
                    5: { sorter: 'eps' },
                    6: { filter : 'parsed' }
                };
            } else {
                return {
                    0: { sorter: 'isoDate' },
                    1: { columnSelector: false },
                    2: { sorter: 'loadingNames' },
                    4: { sorter: 'quality' },
                    5: { sorter: 'eps' }
                };
            }
        }()),
        widgetOptions: (function(){
            if($('meta[data-var="sickbeard.FILTER_ROW"]').data('content') == 'True'){
                return {
                    filter_columnFilters: true,
                    filter_hideFilters : true,
                    filter_saveFilters : true,
                    filter_functions : {
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

    if(['True', 1].indexOf($('meta[data-var="sickbeard.ANIME_SPLIT_HOME"]').data('content')) >= 0){
        if($("#showListTableAnime").find("tbody").find("tr").size() > 0){
            $.tablesorter.filter.bindSearch( "#showListTableAnime", $('.search') );
        }
    }

    if(['True', 1].indexOf($('meta[data-var="sickbeard.FUZZY_DATING"]').data('content')) >= 0){
        $.timeago.settings.allowFuture = true;
        $.timeago.settings.strings = {
            prefixAgo: null,
            prefixFromNow: 'In ',
            suffixAgo: "ago",
            suffixFromNow: "",
            seconds: "less than a minute",
            minute: "about a minute",
            minutes: "%d minutes",
            hour: "about an hour",
            hours: "about %d hours",
            day: "a day",
            days: "%d days",
            month: "about a month",
            months: "%d months",
            year: "about a year",
            years: "%d years",
            wordSeparator: " ",
            numbers: []
        };
        $("[datetime]").timeago();
    }

    var $container = [$('#container'), $('#container-anime')];

    $.each($container, function (j) {
        this.isotope({
            itemSelector: '.show',
            sortBy : $('meta[data-var="sickbeard.POSTER_SORTBY"]').data('content'),
            sortAscending: $('meta[data-var="sickbeard.POSTER_SORTDIR"]').data('content'),
            layoutMode: 'masonry',
            masonry: {
                columnWidth: 13,
                isFitWidth: true
            },
            getSortData: {
                name: function( itemElem ) {
                    var name = $( itemElem ).attr('data-name');
                    return ($('meta[data-var="sickbeard.SORT_ARTICLE"]').data('content') == 'True' ? (name || '') : (name || '').replace(/^(The|A|An)\s/i,''));
                },
                network: '[data-network]',
                date: function( itemElem ) {
                    var date = $( itemElem ).attr('data-date');
                    return date.length && parseInt( date, 10 ) || Number.POSITIVE_INFINITY;
                },
                progress: function( itemElem ) {
                    var progress = $( itemElem ).attr('data-progress');
                    return progress.length && parseInt( progress, 10 ) || Number.NEGATIVE_INFINITY;
                }
            }
        });
    });

    $('#postersort').on( 'change', function() {
        var sortValue = this.value;
        $('#container').isotope({ sortBy: sortValue });
        $('#container-anime').isotope({ sortBy: sortValue });
        $.get(this.options[this.selectedIndex].getAttribute('data-sort'));
    });

    $('#postersortdirection').on( 'change', function() {
        var sortDirection = this.value;
        sortDirection = sortDirection == 'true';
        $('#container').isotope({ sortAscending: sortDirection });
        $('#container-anime').isotope({ sortAscending: sortDirection });
        $.get(this.options[this.selectedIndex].getAttribute('data-sort'));
    });

    $('#popover').popover({
        placement: 'bottom',
        html: true, // required if content has HTML
        content: '<div id="popover-target"></div>'
    }).on('shown.bs.popover', function () { // bootstrap popover event triggered when the popover opens
        // call this function to copy the column selection code into the popover
        $.tablesorter.columnSelector.attachTo( $('#showListTableShows'), '#popover-target');
        if(['True', 1].indexOf($('meta[data-var="sickbeard.ANIME_SPLIT_HOME"]').data('content')) >= 0){
            $.tablesorter.columnSelector.attachTo( $('#showListTableAnime'), '#popover-target');
        }

    });
});
