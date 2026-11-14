window.SICKCHILL ||= {};
window.SICKCHILL.movies = {
    init() {
        // Reset the layout for the activated tab (when using ui tabs)
        $('#movieTabs').tabs({
            activate() {
                $('.movie-grid').isotope('layout');
            },
        });
    },
    index() {
        // Resets the tables sorting, needed as we only use a single call for both tables in tablesorter
        $('.resetsorting').on('click', () => {
            $('table').trigger('filterReset');
        });

        // Handle filtering in the poster layout
        $('#filterMovieName').on('input', __.debounce(() => {
            $('.movie-grid').isotope({
                filter() {
                    const name = $(this).find('.movie-title').html().trim().toLowerCase();
                    const term = ($('#filterMovieName').val() ?? '').toLowerCase();
                    return name.includes(term);
                },
            });
        }, 500));

        function resizePosters(newSize) {
            let fontSize = 0;
            let logoWidth = 0;
            let borderRadius = 0;
            let borderWidth = 0;

            if (newSize < 125) { // Small
                borderRadius = 3;
                borderWidth = 4;
            } else if (newSize < 175) { // Medium
                fontSize = 9;
                logoWidth = 40;
                borderRadius = 4;
                borderWidth = 5;
            } else { // Large
                fontSize = 11;
                logoWidth = 50;
                borderRadius = 6;
                borderWidth = 6;
            }

            // If there's a poster popup, remove it before resizing
            $('#posterPopup').remove();

            if (fontSize === undefined) {
                $('.movie-details').hide();
            } else {
                $('.movie-details').show();
                $('.movie-dlstats, .movie-quality').css('fontSize', fontSize);
                $('.movie-network-image').css('width', logoWidth);
            }

            $('.movie-container').css({
                width: newSize,
                borderWidth,
                borderRadius,
            });
        }

        let posterSize;
        if (typeof (Storage) !== 'undefined') {
            posterSize = Number.parseInt(localStorage.getItem('posterSize'), 10);
        }

        if (typeof (posterSize) !== 'number' || Number.isNaN(posterSize)) {
            posterSize = 188;
        }

        resizePosters(posterSize);

        $('#posterSizeSlider').slider({
            min: 75,
            max: 250,
            value: posterSize,
            change(event, ui) {
                if (typeof (Storage) !== 'undefined') {
                    localStorage.setItem('posterSize', ui.value);
                }

                resizePosters(ui.value);
                $('.movie-grid').isotope('layout');
            },
        });

        $('#rootDirSelect').on('change', () => {
            $('#rootDirForm').submit();
        });

        $('img#network').on('error', function () {
            $(this).parent().text($(this).attr('alt'));
            $(this).remove();
        });
    },
    details() {
        $('.addQTip').each(function () {
            $(this).css({cursor: 'help', 'text-shadow': '0px 0px 0.5px #666'});
            $(this).qtip({
                show: {solo: true},
                position: {viewport: $(window), my: 'left center', adjust: {y: -10, x: 2}},
                style: {tip: {corner: true, method: 'polygon'}, classes: 'qtip-rounded qtip-shadow ui-tooltip-sb'},
            });
        });

        $.fn.generateStars = function () {
            return this.each((i, element) => {
                $(element).html($('<span/>').width($(element).text() * 12));
            });
        };

        $('.imdbstars').generateStars();

        $('#popover').popover({
            placement: 'bottom',
            html: true, // Required if content has HTML
            content: '<div id="popover-target"></div>',
        })
        // Bootstrap popover event triggered when the popover opens
            .on('shown.bs.popover', () => {
                $('.displayShowTable').each((index, item) => {
                    $.tablesorter.columnSelector.attachTo(item, '#popover-target');
                });
            });
    },
};
