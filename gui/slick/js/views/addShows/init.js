$(document).ready(function() {

    $('#tabs').tabs({
        collapsible: true,
        selected: (metaToBool('sickbeard.SORT_ARTICLE') ? -1 : 0)
    });

    $.initRemoteShowGrid = function () {
        // Set defaults on page load
        $('#showsort').val('original');
        $('#showsortdirection').val('asc');

        $('#showsort').on('change', function () {
            var sortCriteria;
            switch (this.value) {
                case 'original':
                    sortCriteria = 'original-order';
                    break;
                case 'rating':
                    /* randomise, else the rating_votes can already
                     * have sorted leaving this with nothing to do.
                     */
                    $('#container').isotope({sortBy: 'random'});
                    sortCriteria = 'rating';
                    break;
                case 'rating_votes':
                    sortCriteria = ['rating', 'votes'];
                    break;
                case 'votes':
                    sortCriteria = 'votes';
                    break;
                default:
                    sortCriteria = 'name';
                    break;
            }
            $('#container').isotope({
                sortBy: sortCriteria
            });
        });

        $('#showsortdirection').on('change', function () {
            $('#container').isotope({
                sortAscending: ('asc' === this.value)
            });
        });

        $('#container').isotope({
            sortBy: 'original-order',
            layoutMode: 'fitRows',
            getSortData: {
                name: function (itemElem) {
                    var name = $(itemElem).attr('data-name') || '';
                    return (metaToBool('sickbeard.SORT_ARTICLE') ? name : name.replace(/^((?:The|A|An)\s)/i, '')).toLowerCase();
                },
                rating: '[data-rating] parseInt',
                votes: '[data-votes] parseInt'
            }
        });
    };

    $.fn.loadRemoteShows = function (path, loadingTxt, errorTxt) {
        $(this).html('<img id="searchingAnim" src="' + srRoot + '/images/loading32' + themeSpinner + '.gif" height="32" width="32" />&nbsp;' + loadingTxt);
        $(this).load(srRoot + path + ' #container', function (response, status) {
            if (status === "error") {
                $(this).empty().html(errorTxt);
            } else {
                $.initRemoteShowGrid();
            }
        });
    };

});
