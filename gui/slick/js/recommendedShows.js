$(document).ready(function() {
    var trendingRequestXhr = null;

    function loadContent() {
        if (trendingRequestXhr) trendingRequestXhr.abort();

        $('#trendingShows').html('<img id="searchingAnim" src="' + sbRoot + '/images/loading32' + themeSpinner + '.gif" height="32" width="32" /> Loading Recommended Shows...');
        trendingRequestXhr = $.ajax({
            url: sbRoot + '/home/addShows/getRecommendedShows/',
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
