const searchStatusUrl = scRoot + '/home/getManualSearchStatus';
let failedDownload = false;
let qualityDownload = false;
let selectedEpisode = '';

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

// Helper function for pill styling
function buildStatusPill(statusText, quality) {
    if (!statusText) {
        return statusText || '';
    }

    let html = statusText; // Default to original text

    // If it already has quality in parentheses, wrap status part
    const match = statusText.match(/^(.+?)\s*\((.+?)\)$/);
    if (match) {
        const statusPart = match[1].trim();
        const qualityPart = match[2].trim();
        html = `<span class="status pill-${getPillClass(statusPart)}">${statusPart}</span> <span class="quality ${quality}">${qualityPart}</span>`;
    } else {
        // Plain status (like "Downloaded", "Skipped", etc.)
        html = `<span class="status pill-${getPillClass(statusText)}">${statusText}</span>`;
    }

    return html;
}

function getPillClass(status) {
    const lower = status.toLowerCase().trim();
    if (lower.includes('downloaded') || lower === 'success') {
        return 'downloaded';
    }

    if (lower.includes('snatched')) {
        return 'snatched';
    }

    if (lower.includes('skipped') || lower.includes('ignored')) {
        return 'archived';
    }

    if (lower.includes('wanted')) {
        return 'wanted';
    }

    if (lower.includes('failed')) {
        return 'failed';
    }

    return 'unknown';
}

function updateImages(data) {
    $.each(data.episodes, (name, ep) => {
        // Get td element for current ep
        const loadingClass = 'loading-spinner16';
        const queuedClass = 'displayshow-icon-clock';
        const searchClass = 'displayshow-icon-search';

        // Try to get the <a> Element
        const link = $('a[id=' + ep.show + 'x' + ep.season + 'x' + ep.episode + ']');
        if (link.length > 0) {
            const icon = link.children('span');
            const parent = link.parent();

            let htmlContent = '';

            if (ep.searchstatus.toLowerCase() === 'searching') {
                icon.prop('class', loadingClass);
                icon.prop('title', 'Searching');
                icon.prop('alt', 'Searching');

                disableLink(link);
                htmlContent = '<span class="status pill-wanted">Searching...</span>'; // Optional nice pill
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

                // Update status and quality
                htmlContent = buildStatusPill(ep.status, ep.quality);
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
    });
}

function checkManualSearches() {
    let pollInterval = 5000;
    const showId = $('#showID').val();
    const url = showId ? searchStatusUrl + '?show=' + showId : searchStatusUrl;
    $.ajax({
        url,
        success(data) {
            pollInterval = data.episodes ? 5000 : 15_000;

            updateImages(data);
        },
        error() {
            pollInterval = 30_000;
        },
        type: 'GET',
        dataType: 'json',
        complete() {
            setTimeout(checkManualSearches, pollInterval);
        },
        timeout: 15_000, // Timeout every 15 secs
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

                // With search success update the status with the result
                const htmlContent = buildStatusPill(data.result, data.quality);
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
