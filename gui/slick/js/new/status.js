$(document).ready(function() {
    $("#schedulerStatusTable").tablesorter({
        widgets: ['saveSort', 'zebra']
    });
    $("#queueStatusTable").tablesorter({
        widgets: ['saveSort', 'zebra'],
        sortList: [[3,0], [4,0], [2,1]]
    });
});
