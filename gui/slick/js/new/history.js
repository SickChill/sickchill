$(document).ready(function(){
    $("#historyTable:has(tbody tr)").tablesorter({
        widgets: ['zebra', 'filter'],
        sortList: [[0,1]],
        textExtraction: (function(){
            if(isMeta('sickbeard.HISTORY_LAYOUT', ['detailed'])){
                return {
                    0: function(node) { return $(node).find('time').attr('datetime'); },
                    4: function(node) { return $(node).find("span").text().toLowerCase(); }
                };
            } else {
                return {
                    0: function(node) { return $(node).find('time').attr('datetime'); },
                    1: function(node) { return $(node).find("span").text().toLowerCase(); },
                    2: function(node) { return $(node).attr("provider").toLowerCase(); },
                    5: function(node) { return $(node).attr("quality").toLowerCase(); }
                };
            }
        }()),
        headers: (function(){
            if(isMeta('sickbeard.HISTORY_LAYOUT', ['detailed'])){
                return {
                    0: { sorter: 'realISODate' },
                    4: { sorter: 'quality' }
                };
            } else {
                return {
                    0: { sorter: 'realISODate' },
                    4: { sorter: false },
                    5: { sorter: 'quality' }
                };
            }
        }())
    });

    $('#history_limit').on('change', function() {
        var url = srRoot + '/history/?limit=' + $(this).val();
        window.location.href = url;
    });
});
