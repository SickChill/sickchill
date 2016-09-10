$(document).ready(function () {

    $('#recommendedShows').loadRemoteShows(
        '/addShows/getRecommendedShows/',
        'Loading recommended shows...',
        'Trakt timed out, refresh page to try again'
    );

});
