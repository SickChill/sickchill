$(document).ready(function () {

    $("#schedulerStatusTable").tablesorter({
        widgets: ['saveSort', 'zebra'],
        textExtraction: {
            5: function (node) {
                return $(node).data('seconds');
            },
            6: function (node) {
                return $(node).data('seconds');
            }
        },
        headers: {
            5: {sorter: 'digit'},
            6: {sorter: 'digit'}
        }
    });
    $("#queueStatusTable").tablesorter({
        widgets: ['saveSort', 'zebra'],
        sortList: [[3, 0], [4, 0], [2, 1]]
    });

});
