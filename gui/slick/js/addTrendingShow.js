$(document).ready(function() {
    function loadContent() {
        $('#trendingShows').html('<img id="searchingAnim" src="' + sbRoot + '/images/loading32' + themeSpinner + '.gif" height="32" width="32" /> loading trending shows...');
        $.get(sbRoot+'/home/addShows/getTrendingShows/', function(data) {
            $('#trendingShows').html(data);
        });

    }

    loadContent();
});
