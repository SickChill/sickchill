$.tablesorter.addParser({
    id: 'cDate',
    is: function(s) {
        return false;
    },
    format: function(s) {
        return s;
    },
    type: 'numeric'
});

$(document).ready(function(){
    $("#historyTable:has(tbody tr)").tablesorter({
        widgets: ['zebra', 'filter'],
        sortList: [[0,1]],
        textExtraction: (function(){
            if($('meta[data-var="layout"]').data('content') == 'detailed'){
                return {
                    0: function(node) { return $(node).find("span").text().toLowerCase(); },
                    4: function(node) { return $(node).find("span").text().toLowerCase(); }
                };
            } else {
                return {
                    0: function(node) { return $(node).find("span").text().toLowerCase(); },
                    1: function(node) { return $(node).find("span").text().toLowerCase(); },
                    2: function(node) { return $(node).attr("provider").toLowerCase(); },
                    5: function(node) { return $(node).attr("quality").toLowerCase(); }
                };
            }
        }),
        headers: (function(){
            if($('meta[data-var="layout"]').data('content') == 'detailed'){
                return {
                    0: { sorter: 'cDate' },
                    4: { sorter: 'quality' }
                };
            } else {
                return {
                    0: { sorter: 'cDate' },
                    4: { sorter: false },
                    5: { sorter: 'quality' }
                };
            }
        })
    });

    $('#history_limit').on('change', function() {
        var url = sbRoot + '/history/?limit=' + $(this).val();
        window.location.href = url;
    });

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

});
