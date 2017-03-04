var searchStatusUrl = srRoot + '/home/getManualSearchStatus';
var failedDownload = false;
var qualityDownload = false;
var selectedEpisode = '';
PNotify.prototype.options.maxonscreen = 5;

$.fn.manualSearches = [];

function enableLink(link) {
    link.on('click.disabled', false);
    link.prop('enableClick', '1');
    link.fadeTo("fast", 1);
}

function disableLink(link) {
    link.off('click.disabled');
    link.prop('enableClick', '0');
    link.fadeTo("fast", 0.5);
}

function updateImages(data) {
    $.each(data.episodes, function (name, ep) {
        // Get td element for current ep
        var loadingClass = 'loading-spinner16';
        var queuedClass = 'queued-search';
        var searchClass = 'displayshow-icon-search';

        //Try to get the <a> Element
        var link = $('a[id=' + ep.show + 'x' + ep.season + 'x' + ep.episode+']');
        if (link) {
            var icon = link.children('span');
            var parent = link.parent();

            var rSearchTerm = '';
            var htmlContent = '';

            if (ep.searchstatus.toLowerCase() === 'searching') {
                icon.prop('class', loadingClass);
                icon.prop('title','Searching');
                icon.prop('alt','Searching');

                disableLink(link);
                htmlContent = ep.searchstatus.title;

            } else if (ep.searchstatus.toLowerCase() === 'queued') {
                icon.prop('class', queuedClass );
                icon.prop('title','Queued');
                icon.prop('alt','Queued');

                disableLink(link);
                htmlContent = ep.searchstatus;

            } else if (ep.searchstatus.toLowerCase() === 'finished') {
                icon.prop('class', searchClass);
                if (ep.quality !== "N/A") {
                    link.prop('class','epRetry');
                }
                icon.prop('title','Search');
                icon.prop('alt','Search');

                enableLink(link);

                // Update Status and Quality
                rSearchTerm = /(\w+)\s\((.+?)\)/;
                htmlContent = ep.status.replace(rSearchTerm,"$1"+' <span class="quality '+ep.quality+'">'+"$2"+'</span>');
                parent.closest('tr').prop("class", ep.overview + " season-" + ep.season + " seasonstyle");
            }
            // update the status column if it exists
            parent.siblings('.col-status').html(htmlContent);
            // and location
            parent.siblings('.location').html(ep.location);
            // and size
            parent.siblings('.size').html(ep.size);
            // and qtip location
            if (ep.location) {
                parent.siblings('.episode').html('<span title="' + ep.location + '" class="addQTip">' + ep.episode + "</span>");
            }
        }
        var elementCompleteEpisodes = $('a[id=forceUpdate-' + ep.show + 'x' + ep.season + 'x' + ep.episode+']');
        var spanCompleteEpisodes = elementCompleteEpisodes.children('span');
        if (elementCompleteEpisodes) {
            if (ep.searchstatus.toLowerCase() === 'searching') {
                spanCompleteEpisodes.prop('class', loadingClass);
                spanCompleteEpisodes.prop('title','Searching');
                spanCompleteEpisodes.prop('alt','Searching');
                disableLink(elementCompleteEpisodes);
            } else if (ep.searchstatus.toLowerCase() === 'queued') {
                spanCompleteEpisodes.prop('class', queuedClass);
                spanCompleteEpisodes.prop('title','Queued');
                spanCompleteEpisodes.prop('alt','Queued');
                disableLink(elementCompleteEpisodes);
            } else if (ep.searchstatus.toLowerCase() === 'finished') {
                spanCompleteEpisodes.prop('class', searchClass);
                spanCompleteEpisodes.prop('title','Search');
                spanCompleteEpisodes.prop('alt','Search');
                if (ep.overview.toLowerCase() === 'snatched') {
                    elementCompleteEpisodes.closest('tr').remove();
                } else {
                    enableLink(elementCompleteEpisodes);
                }
            }
        }
    });
}

function checkManualSearches() {
    var pollInterval = 5000;
    var showId = $('#showID').val();
    var url = showId !== undefined ? searchStatusUrl + '?show=' + showId : searchStatusUrl ;
    $.ajax({
        url: url,
        success: function (data) {
            if (data.episodes) {
                pollInterval = 5000;
            } else {
                pollInterval = 15000;
            }
            updateImages(data);
        },
        error: function () {
            pollInterval = 30000;
        },
        type: "GET",
        dataType: "json",
        complete: function () {
            setTimeout(checkManualSearches, pollInterval);
        },
        timeout: 15000 // timeout every 15 secs
    });
}

$(document).ready(function () {
    checkManualSearches();
});

(function(){
    var stupidOptions;
    function manualSearch(){
        var parent = selectedEpisode.parent();

        // Create var for anchor
        var link = selectedEpisode;

        // Create var for img under anchor and set options for the loading gif
        var icon = selectedEpisode.children('span');
        icon.prop('title','Loading');
        icon.prop('alt','Loading');
        icon.prop('class', stupidOptions.loadingClass);

        var url = selectedEpisode.prop('href');

        if (failedDownload === false) {
            url = url.replace("retryEpisode", "searchEpisode");
        }

        url = url + "&downCurQuality=" + (qualityDownload ? '1' : '0');

        $.getJSON(url, function(data){
            var imageName, imageResult;
            // if they failed then just put the red X
            if (data.result.toLowerCase() === 'failure') {
                imageName = stupidOptions.noImage;
                imageResult = 'Failed';
            } else {
                imageName = stupidOptions.loadingImage;
                imageResult = 'Success';
                // color the row
                if (stupidOptions.colorRow) {
                    parent.parent().removeClass('skipped wanted qual good unaired').addClass('snatched');
                }
                // applying the quality class
                var rSearchTerm = /(\w+)\s\((.+?)\)/;
                var htmlContent = data.result.replace(rSearchTerm,"$1"+' <span class="quality '+data.quality+'">'+"$2"+'</span>');
                // update the status column if it exists
                parent.siblings('.col-status').html(htmlContent);
                // Only if the queuing was successful, disable the onClick event of the loading image
                disableLink(link);
            }

            // put the corresponding image as the result of queuing of the manual search
            // icon.prop('title', imageResult);
            // icon.prop('alt', imageResult);
            // icon.prop('class', imageName);
        });

        // don't follow the link
        return false;
    }

    $.ajaxEpSearch = {
        defaults: {
            size: 16,
            colorRow: false,
            loadingClass: 'loading-spinner16',
            queuedClass: 'queued-search',
            noImage: 'no16-image',
            yesImage: 'yes16-image'
        }
    };

    $.fn.ajaxEpSearch = function(options){
        stupidOptions = $.extend({}, $.ajaxEpSearch.defaults, options);

        $('.epSearch, .epRetry').on('click', function(event){
            event.preventDefault();

            // Check if we have disabled the click
            if ($(this).prop('enableClick') === '0') { return false; }

            selectedEpisode = $(this);

            if ($(this).hasClass("epRetry")){
                $("#manualSearchModalFailed").modal('show');
            }
            else if ($(this).parent().parent().children(".col-status").children(".quality").length) {
                $("#manualSearchModalQuality").modal('show');
            } else {
                manualSearch();
            }
        });

        $('#manualSearchModalFailed .btn').on('click', function(){
            failedDownload = ($(this).text().toLowerCase() === 'yes');
            $("#manualSearchModalQuality").modal('show');
        });

        $('#manualSearchModalQuality .btn').on('click', function(){
            qualityDownload = ($(this).text().toLowerCase() === 'yes');
            manualSearch();
        });
    };
})();
