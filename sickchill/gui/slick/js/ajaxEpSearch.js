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
        return '';
    }

    let displayText = statusText.trim();
    let cssClass = 'unknown';
    const lower = displayText.toLowerCase();

    // === Status Class Logic ===
    if (lower === 'success' || lower === 'skipped' || lower.startsWith('skipped')) {
        cssClass = 'archived'; // Gray for Skipped
    } else if (lower.includes('downloaded')) {
        cssClass = 'downloaded';
    } else if (lower.includes('snatched')) {
        cssClass = 'snatched';
    } else if (lower.includes('wanted')) {
        cssClass = 'wanted';
    } else if (lower.includes('archived')) {
        cssClass = 'archived';
    } else if (lower.includes('failed')) {
        cssClass = 'failed';
    }

    // === Clean up status text if it already includes quality ===
    const qualityRegex = /\(([^)]+)\)/;
    const match = displayText.match(qualityRegex);
    let qualityInStatus = '';

    if (match) {
        qualityInStatus = match[1].trim(); // E.g. "1080p WEB-DL"
        displayText = displayText.replace(qualityRegex, '').trim(); // Remove quality from status text
    }

    // Use provided quality if better
    const finalQuality = quality && quality !== 'N/A' && quality !== '' ? quality : qualityInStatus;

    let html = `<span class="status pill-${cssClass}">${displayText}</span>`;

    // Add quality pill only if we have one
    if (finalQuality) {
        const qClass = finalQuality.toLowerCase().replaceAll(/\s+/g, '-');
        html += ` <span class="quality ${qClass}">${finalQuality}</span>`;
    }

    return html;
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

                // Improved row class - respect actual status
                let rowClass = ep.overview || 'wanted';
                const statusLower = (ep.status || '').toLowerCase().trim();
                if (statusLower === 'skipped' || statusLower === 'success' || statusLower.startsWith('skipped')) {
                    rowClass = 'skipped';
                }

                parent.closest('tr').prop('class', rowClass + ' season-' + ep.season + ' seasonstyle');
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

                // In the success update the status with the result
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
