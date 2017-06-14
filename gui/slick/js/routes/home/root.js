import {debounce} from 'underscore';

import {getMeta} from '../../utils';

export default () => {
    // Resets the tables sorting, needed as we only use a single call for both tables in tablesorter
    $('.resetsorting').on('click', () => {
        $('table').trigger('filterReset');
    });

    // Handle filtering in the poster layout
    $('#filterShowName').on('input', debounce(() => {
        $('.show-grid').isotope({
            filter() {
                const name = $(this).find('.show-title').html().trim().toLowerCase();
                return name.indexOf($('#filterShowName').val().toLowerCase()) > -1;
            }
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
            $('.show-details').hide();
        } else {
            $('.show-details').show();
            $('.show-dlstats, .show-quality').css('fontSize', fontSize);
            $('.show-network-image').css('width', logoWidth);
        }

        $('.show-container').css({
            width: newSize,
            borderWidth,
            borderRadius
        });
    }

    let posterSize;
    if (typeof (Storage) !== 'undefined') {
        posterSize = parseInt(localStorage.getItem('posterSize'), 10);
    }
    if (typeof (posterSize) !== 'number' || isNaN(posterSize)) {
        posterSize = 188;
    }
    resizePosters(posterSize);

    $('#posterSizeSlider').slider({
        min: 75,
        max: 250,
        value: posterSize,
        change(e, ui) {
            if (typeof (Storage) !== 'undefined') {
                localStorage.setItem('posterSize', ui.value);
            }
            resizePosters(ui.value);
            $('.show-grid').isotope('layout');
        }
    });

    $('#rootDirSelect').on('change', () => {
        $('#rootDirForm').submit();
    });

    // This needs to be refined to work a little faster.
    $('.progressbar').each(function() {
        const percentage = $(this).data('progress-percentage');
        const classToAdd = percentage === 100 ? 100 : percentage > 80 ? 80 : percentage > 60 ? 60 : percentage > 40 ? 40 : 20;
        $(this).progressbar({value: percentage});
        if ($(this).data('progress-text')) {
            $(this).append('<div class="progressbarText" title="' + $(this).data('progress-tip') + '">' + $(this).data('progress-text') + '</div>');
        }
        $(this).find('.ui-progressbar-value').addClass('progress-' + classToAdd);
    });

    $('img#network').on('error', function() {
        $(this).parent().text($(this).attr('alt'));
        $(this).remove();
    });

    $('#showListTableShows:has(tbody tr), #showListTableAnime:has(tbody tr)').tablesorter({
        sortList: [[7, 1], [2, 0]],
        textExtraction: {
            0(node) {
                return $(node).find('time').attr('datetime');
            },
            1(node) {
                return $(node).find('time').attr('datetime');
            },
            3(node) {
                return $(node).find('span').prop('title').toLowerCase();
            },
            4(node) {
                return $(node).find('span').text().toLowerCase();
            },
            5(node) {
                return $(node).find('span:first').text();
            },
            6(node) {
                return $(node).data('show-size');
            },
            7(node) {
                return $(node).find('span').attr('title').toLowerCase();
            }
        },
        widgets: ['saveSort', 'zebra', 'stickyHeaders', 'filter', 'columnSelector'],
        headers: {
            0: {sorter: 'realISODate'},
            1: {sorter: 'realISODate'},
            2: {sorter: 'loadingNames'},
            4: {sorter: 'quality'},
            5: {sorter: 'eps'},
            6: {sorter: 'digit'},
            7: {filter: 'parsed'}
        },
        widgetOptions: {
            filter_columnFilters: true, // eslint-disable-line camelcase
            filter_hideFilters: true, // eslint-disable-line camelcase
            stickyHeaders_offset: 50, // eslint-disable-line camelcase
            filter_saveFilters: true, // eslint-disable-line camelcase
            filter_functions: { // eslint-disable-line camelcase
                5(e, n, f) { // eslint-disable-line complexity
                    let test = false;
                    const pct = Math.floor((n % 1) * 1000);
                    if (f === '') {
                        test = true;
                    } else {
                        let result = f.match(/(<|<=|>=|>)\s+(\d+)/i);
                        if (result) {
                            if (result[1] === '<') {
                                if (pct < parseInt(result[2], 10)) {
                                    test = true;
                                }
                            } else if (result[1] === '<=') {
                                if (pct <= parseInt(result[2], 10)) {
                                    test = true;
                                }
                            } else if (result[1] === '>=') {
                                if (pct >= parseInt(result[2], 10)) {
                                    test = true;
                                }
                            } else if (result[1] === '>') {
                                if (pct > parseInt(result[2], 10)) {
                                    test = true;
                                }
                            }
                        }

                        result = f.match(/(\d+)\s(-|to)\s+(\d+)/i);
                        if (result) {
                            if ((result[2] === '-') || (result[2] === 'to')) {
                                if ((pct >= parseInt(result[1], 10)) && (pct <= parseInt(result[3], 10))) {
                                    test = true;
                                }
                            }
                        }

                        result = f.match(/(=)?\s?(\d+)\s?(=)?/i);
                        if (result) {
                            if ((result[1] === '=') || (result[3] === '=')) {
                                if (parseInt(result[2], 10) === pct) {
                                    test = true;
                                }
                            }
                        }

                        if (!isNaN(parseFloat(f)) && isFinite(f)) {
                            if (parseInt(f, 10) === pct) {
                                test = true;
                            }
                        }
                    }
                    return test;
                }
            },
            columnSelector_mediaquery: false // eslint-disable-line camelcase
        },
        sortStable: true,
        sortAppend: [[2, 0]]
    });

    $('.show-grid').imagesLoaded(() => {
        $('.loading-spinner').hide();
        $('.show-grid').show().isotope({
            itemSelector: '.show-container',
            sortBy: getMeta('sickbeard.POSTER_SORTBY'),
            sortAscending: getMeta('sickbeard.POSTER_SORTDIR'),
            layoutMode: 'masonry',
            masonry: {
                isFitWidth: true
            },
            getSortData: {
                name(itemElem) {
                    const name = $(itemElem).attr('data-name') || '';
                    return (metaToBool('sickbeard.SORT_ARTICLE') ? name : name.replace(/^((?:The|A|An)\s)/i, '')).toLowerCase();
                },
                network: '[data-network]',
                date(itemElem) {
                    const date = $(itemElem).attr('data-date');
                    return (date.length && parseInt(date, 10)) || Number.POSITIVE_INFINITY;
                },
                progress(itemElem) {
                    const progress = $(itemElem).attr('data-progress');
                    return (progress.length && parseInt(progress, 10)) || Number.NEGATIVE_INFINITY;
                }
            }
        });

        // When posters are small enough to not display the .show-details
        // table, display a larger poster when hovering.
        let posterHoverTimer = null;
        $('.show-container').on('mouseenter', function() {
            const poster = $(this);
            if (poster.find('.show-details').css('display') !== 'none') {
                return;
            }
            posterHoverTimer = setTimeout(() => {
                posterHoverTimer = null;
                $('#posterPopup').remove();
                const popup = poster.clone().attr({
                    id: 'posterPopup'
                });
                const origLeft = poster.offset().left;
                const origTop = poster.offset().top;
                popup.css({
                    position: 'absolute',
                    margin: 0,
                    top: origTop,
                    left: origLeft,
                    zIndex: 9999
                });

                popup.find('.show-details').show();
                popup.on('mouseleave', function() {
                    $(this).remove();
                });
                popup.appendTo('body');

                const height = 438;
                const width = 250;

                let newTop = ((origTop + poster.height()) / 2) - (height / 2);
                let newLeft = ((origLeft + poster.width()) / 2) - (width / 2);

                // Make sure the popup isn't outside the viewport
                const margin = 5;
                const scrollTop = $(window).scrollTop();
                const scrollLeft = $(window).scrollLeft();
                const scrollBottom = scrollTop + $(window).innerHeight();
                const scrollRight = scrollLeft + $(window).innerWidth();
                if (newTop < scrollTop + margin) {
                    newTop = scrollTop + margin;
                }
                if (newLeft < scrollLeft + margin) {
                    newLeft = scrollLeft + margin;
                }
                if (newTop + height + margin > scrollBottom) {
                    newTop = scrollBottom - height - margin;
                }
                if (newLeft + width + margin > scrollRight) {
                    newLeft = scrollRight - width - margin;
                }

                popup.animate({
                    top: newTop,
                    left: newLeft,
                    width: 250,
                    height: 438
                });
            }, 300);
        }).on('mouseleave', () => {
            if (posterHoverTimer !== null) {
                clearTimeout(posterHoverTimer);
            }
        });
    });

    $('#postersort').on('change', function() {
        $('.show-grid').isotope({sortBy: $(this).val()});
        $.post($(this).find('option[value=' + $(this).val() + ']').attr('data-sort'));
    });

    $('#postersortdirection').on('change', function() {
        $('.show-grid').isotope({sortAscending: ($(this).val() === 'true')});
        $.post($(this).find('option[value=' + $(this).val() + ']').attr('data-sort'));
    });

    $('#popover').popover({
        placement: 'bottom',
        html: true, // Required if content has HTML
        content: '<div id="popover-target"></div>'
    }).on('shown.bs.popover', () => { // Bootstrap popover event triggered when the popover opens
        // call this function to copy the column selection code into the popover
        $.tablesorter.columnSelector.attachTo($('#showListTableShows'), '#popover-target');
        if (metaToBool('sickbeard.ANIME_SPLIT_HOME')) {
            $.tablesorter.columnSelector.attachTo($('#showListTableAnime'), '#popover-target');
        }
    });
};
