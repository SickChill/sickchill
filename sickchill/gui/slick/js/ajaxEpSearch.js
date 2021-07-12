const searchStatusUrl = scRoot + '/home/getManualSearchStatus';
let failedDownload = false;
let qualityDownload = false;
let selectedEpisode = '';
PNotify.prototype.options.maxonscreen = 5;

$.fn.manualSearches = [];

function enableLink(link) {
    link.on('click.disabled', false);
    link.prop('enableClick', '1');
    link.fadeTo('fast', 1);
}

function disableLink(link) {
    link.off('click.disabled');
    link.prop('enableClick', '0');
    link.fadeTo('fast', 0.5);
}

function updateImages(data) {
    $.each(data.episodes, (name, ep) => {
        // Get td element for current ep
        const loadingClass = 'loading-spinner16';
        const queuedClass = 'displayshow-icon-clock';
        const searchClass = 'displayshow-icon-search';

        // Try to get the <a> Element
        const link = $('a[id=' + ep.show + 'x' + ep.season + 'x' + ep.episode + ']');
        if (link) {
            const icon = link.children('span');
            const parent = link.parent();

            let rSearchTerm = '';
            let htmlContent = '';

            if (ep.searchstatus.toLowerCase() === 'searching') {
                icon.prop('class', loadingClass);
                icon.prop('title', 'Searching');
                icon.prop('alt', 'Searching');

                disableLink(link);
                htmlContent = ep.searchstatus.title;
            } else if (ep.searchstatus.toLowerCase() === 'queued') {
                icon.prop('class', queuedClass);
                icon.prop('title', 'Queued');
                icon.prop('alt', 'Queued');

                disableLink(link);
                htmlContent = ep.searchstatus;
            } else if (ep.searchstatus.toLowerCase() === 'finished') {
                icon.prop('class', searchClass);
                if (ep.quality !== 'N/A') {
                    link.prop('class', 'epRetry');
                }

                icon.prop('title', 'Search');
                icon.prop('alt', 'Search');

                enableLink(link);

                // Update Status and Quality
                rSearchTerm = /(\w+)\s\((.+?)\)/;
                htmlContent = ep.status.replace(rSearchTerm, '$1 <span class="quality ' + ep.quality + '">$2</span>');
                parent.closest('tr').prop('class', ep.overview + ' season-' + ep.season + ' seasonstyle');
            }

            // Update the status column if it exists
            parent.siblings('.col-status').html(htmlContent);
            // And location
            parent.siblings('.location').html(ep.location);
            // And size
            parent.siblings('.size').html(ep.size);
            // And qtip location
            if (ep.location) {
                parent.siblings('.episode').html('<span title="' + ep.location + '" class="addQTip">' + ep.episode + '</span>');
            }
        }

        const elementCompleteEpisodes = $('a[id=forceUpdate-' + ep.show + 'x' + ep.season + 'x' + ep.episode + ']');
        const spanCompleteEpisodes = elementCompleteEpisodes.children('span');
        if (elementCompleteEpisodes) {
            if (ep.searchstatus.toLowerCase() === 'searching') {
                spanCompleteEpisodes.prop('class', loadingClass);
                spanCompleteEpisodes.prop('title', 'Searching');
                spanCompleteEpisodes.prop('alt', 'Searching');
                disableLink(elementCompleteEpisodes);
            } else if (ep.searchstatus.toLowerCase() === 'queued') {
                spanCompleteEpisodes.prop('class', queuedClass);
                spanCompleteEpisodes.prop('title', 'Queued');
                spanCompleteEpisodes.prop('alt', 'Queued');
                disableLink(elementCompleteEpisodes);
            } else if (ep.searchstatus.toLowerCase() === 'finished') {
                spanCompleteEpisodes.prop('class', searchClass);
                spanCompleteEpisodes.prop('title', 'Search');
                spanCompleteEpisodes.prop('alt', 'Search');
                if (ep.overview.toLowerCase() === 'snatched') {
                    // Find Banner or Poster
                    let actionElement = elementCompleteEpisodes.closest('div.ep_listing');
                    if (actionElement.length === 0 && elementCompleteEpisodes.closest('table.calendarTable').length === 0) {
                        actionElement = elementCompleteEpisodes.closest('tr');
                    }

                    if (actionElement.length > 0) {
                        // Remove any listing-* classes and add listing-snatched (keeping non listing-* classes)
                        actionElement.attr('class', (i, value) => value.replace(/(^|\s)listing-\S+/g, '')).addClass('listing-snatched');
                    }
                }

                enableLink(elementCompleteEpisodes);
            }
        }
    });
}

function checkManualSearches() {
    let pollInterval = 5000;
    const showId = $('#showID').val();
    const url = showId !== undefined ? searchStatusUrl + '?show=' + showId : searchStatusUrl; // eslint-disable-line no-negated-condition
    $.ajax({
        url,
        success(data) {
            pollInterval = data.episodes ? 5000 : 15000;

            updateImages(data);
        },
        error() {
            pollInterval = 30000;
        },
        type: 'GET',
        dataType: 'json',
        complete() {
            setTimeout(checkManualSearches, pollInterval);
        },
        timeout: 15000, // Timeout every 15 secs
    });
}

$(document).ready(checkManualSearches);

(function () {
    let stupidOptions;
    function manualSearch() {
        const parent = selectedEpisode.parent();

        // Create var for anchor
        const link = selectedEpisode;

        // Create var for img under anchor and set options for the loading gif
        const icon = selectedEpisode.children('span');
        icon.prop('title', _('Loading'));
        icon.prop('alt', _('Loading'));
        icon.prop('class', stupidOptions.loadingClass);

        let url = selectedEpisode.prop('href');

        if (failedDownload === false) {
            url = url.replace('retryEpisode', 'searchEpisode');
        }

        url = url + '&downCurQuality=' + (qualityDownload ? '1' : '0');

        $.getJSON(url, data => {
            let imageName = null;
            let imageResult = null;
            // If they failed then just put the red X
            if (data.result.toLowerCase() === 'failure') {
                imageName = stupidOptions.noImage;
                imageResult = _('Failed');
            } else {
                imageName = stupidOptions.loadingClass;
                imageResult = _('Success');
                // Color the row
                if (stupidOptions.colorRow) {
                    parent.parent().removeClass('skipped wanted qual good unaired').addClass('snatched');
                }

                // Applying the quality class
                const rSearchTerm = /(\w+)\s\((.+?)\)/;
                const htmlContent = data.result.replace(rSearchTerm, '$1 <span class="quality ' + data.quality + '">$2</span>');
                // Update the status column if it exists
                parent.siblings('.col-status').html(htmlContent);
                // Only if the queuing was successful, disable the onClick event of the loading image
                disableLink(link);
            }

            // Put the corresponding image as the result of queuing of the manual search
            icon.prop('title', imageResult);
            icon.prop('alt', imageResult);
            icon.prop('class', imageName);
        });

        // Don't follow the link
        return false;
    }

    $.ajaxEpSearch = {
        defaults: {
            size: 16,
            colorRow: false,
            loadingClass: 'loading-spinner16',
            queuedClass: 'displayshow-icon-clock',
            noImage: 'displayshow-icon-disable',
            yesImage: 'displayshow-icon-enable',
        },
    };

    $.fn.ajaxEpSearch = function (options) {
        stupidOptions = $.extend({}, $.ajaxEpSearch.defaults, options);

        $('.epSearch, .epRetry').on('click', function (event) {
            event.preventDefault();

            // Check if we have disabled the click
            if ($(this).prop('enableClick') === '0') {
                return false;
            }

            selectedEpisode = $(this);

            if ($(this).hasClass('epRetry')) {
                $('#manualSearchModalFailed').modal('show');
            } else if ($(this).parent().parent().children('.col-status').children('.quality').length > 0) {
                $('#manualSearchModalQuality').modal('show');
            } else {
                manualSearch();
            }
        });

        $('#manualSearchModalFailed .btn').on('click', function () {
            failedDownload = ($(this).text().toLowerCase() === 'yes');
            $('#manualSearchModalQuality').modal('show');
        });

        $('#manualSearchModalQuality .btn').on('click', function () {
            qualityDownload = ($(this).text().toLowerCase() === 'yes');
            manualSearch();
        });
    };
})();
