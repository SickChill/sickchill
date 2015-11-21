$.fn.loadContent = function(path, loadingTxt, errorTxt) {
    $(this).html('<img id="searchingAnim" src="' + srRoot + '/images/loading32' + themeSpinner + '.gif" height="32" width="32" />&nbsp;' + loadingTxt);
    $(this).load(srRoot + path + ' #container', function(response, status, xhr) {
        if (status == "error") $(this).empty().html(errorTxt);
    });
};

$(document).ready(function() {
    $('#trendingShows').loadContent('/home/addShows/getTrendingShows/', 'Loading trending shows...', 'Trakt timed out, refresh page to try again');
    $('#container').isotope({
        itemSelector: '.trakt_show',
        layoutMode: 'fitRows'
    });
});
