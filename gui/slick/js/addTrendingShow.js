$(document).ready(function() {
    var trendingRequestXhr = null;

    function loadContent() {
        if (trendingRequestXhr) trendingRequestXhr.abort();

        $('#trendingShows').html('<img id="searchingAnim" src="' + sbRoot + '/images/loading32' + themeSpinner + '.gif" height="32" width="32" /> loading trending shows...');
        trendingRequestXhr = $.ajax({
            url: sbRoot + '/home/addShows/getTrendingShows/',
            timeout: 60 * 1000,
            error: function () {
                $('#trendingShows').empty().html('Trakt timed out, refresh page to try again');
            },
            success: function (data) {
                $('#trendingShows').html(data);
            }
        });
    }

    loadContent();
});
