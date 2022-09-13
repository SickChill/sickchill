$(document).ready(() => {
    // Initialise combos for dirty page refreshes
    $('#showsort').val('original');
    $('#showsortdirection').val('asc');

    const $container = [$('#container')];
    $.each($container, function () {
        this.isotope({
            itemSelector: '.trakt_show',
            sortBy: 'original-order',
            layoutMode: 'fitRows',
            getSortData: {
                name(itemElement) {
                    const name = $(itemElement).attr('data-name') || '';
                    const regex = new RegExp('^((?:' + getMeta('settings.GRAMMAR_ARTICLES') + ')\\s)', 'i');
                    return (metaToBool('settings.SORT_ARTICLE') ? name : name.replace(regex, '')).toLowerCase();
                },
                rating: '[data-rating] parseInt',
                votes: '[data-votes] parseInt',
            },
        });
    });

    $('#showsort').on('change', function () {
        let sortCriteria;
        switch (this.value) {
            case 'original':
                sortCriteria = 'original-order';
                break;
            case 'rating':
                /* Randomise, else the rating_votes can already
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

        $('#container').isotope({sortBy: sortCriteria});
    });

    $('#showsortdirection').on('change', function () {
        $('#container').isotope({
            sortAscending: (this.value === 'asc'),
        });
    });
});
