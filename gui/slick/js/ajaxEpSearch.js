var searchStatusUrl = srRoot + '/home/getManualSearchStatus';
var failedDownload = false;
var qualityDownload = false;
var selectedEpisode = '';
PNotify.prototype.options.maxonscreen = 5;

$.fn.manualSearches = [];

function enableLink(el) {
    el.on('click.disabled', false);
    el.prop('enableClick', '1');
    el.fadeTo("fast", 1);
}

function disableLink(el) {
    el.off('click.disabled');
    el.prop('enableClick', '0');
    el.fadeTo("fast", 0.5);
}

function updateImages(data) {
    $.each(data.episodes, function (name, ep) {
        // Get td element for current ep
        var loadingImage = 'loading16.gif';
        var queuedImage = 'queued.png';
        var searchImage = 'search16.png';
        var htmlContent = '';
        //Try to get the <a> Element
        var el = $('a[id=' + ep.show + 'x' + ep.season + 'x' + ep.episode+']');
        var img = el.children('img');
        var parent = el.parent();
        if (el) {
            var rSearchTerm = '';
            if (ep.searchstatus.toLowerCase() === 'searching') {
                //el=$('td#' + ep.season + 'x' + ep.episode + '.search img');
                img.prop('title','Searching');
                img.prop('alt','Searching');
                img.prop('src',srRoot+'/images/' + loadingImage);
                disableLink(el);
                // Update Status and Quality
                rSearchTerm = /(\w+)\s\((.+?)\)/;
                htmlContent = ep.searchstatus;

            } else if (ep.searchstatus.toLowerCase() === 'queued') {
                //el=$('td#' + ep.season + 'x' + ep.episode + '.search img');
                img.prop('title','Queued');
                img.prop('alt','queued');
                img.prop('src',srRoot+'/images/' + queuedImage );
                disableLink(el);
                htmlContent = ep.searchstatus;
            } else if (ep.searchstatus.toLowerCase() === 'finished') {
                //el=$('td#' + ep.season + 'x' + ep.episode + '.search img');
                img.prop('title','Searching');
                img.prop('alt','searching');
                img.parent().prop('class','epRetry');
                img.prop('src',srRoot+'/images/' + searchImage);
                enableLink(el);

                // Update Status and Quality
                rSearchTerm = /(\w+)\s\((.+?)\)/;
                htmlContent = ep.status.replace(rSearchTerm,"$1"+' <span class="quality '+ep.quality+'">'+"$2"+'</span>');
                parent.closest('tr').prop("class", ep.overview + " season-" + ep.season + " seasonstyle");
            }
            // update the status column if it exists
            parent.siblings('.col-status').html(htmlContent);

        }
        var elementCompleteEpisodes = $('a[id=forceUpdate-' + ep.show + 'x' + ep.season + 'x' + ep.episode+']');
        var imageCompleteEpisodes = elementCompleteEpisodes.children('img');
        if (elementCompleteEpisodes) {
            if (ep.searchstatus.toLowerCase() === 'searching') {
                imageCompleteEpisodes.prop('title','Searching');
                imageCompleteEpisodes.prop('alt','Searching');
                imageCompleteEpisodes.prop('src',srRoot+'/images/' + loadingImage);
                disableLink(elementCompleteEpisodes);
            } else if (ep.searchstatus.toLowerCase() === 'queued') {
                imageCompleteEpisodes.prop('title','Queued');
                imageCompleteEpisodes.prop('alt','queued');
                imageCompleteEpisodes.prop('src',srRoot+'/images/' + queuedImage );
            } else if (ep.searchstatus.toLowerCase() === 'finished') {
                imageCompleteEpisodes.prop('title','Manual Search');
                imageCompleteEpisodes.prop('alt','[search]');
                imageCompleteEpisodes.prop('src',srRoot+'/images/' + searchImage);
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
            //cleanupManualSearches(data);
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
    $.ajaxEpSearch = {
        defaults: {
            size:				16,
            colorRow:         	false,
            loadingImage:		'loading16.gif',
            queuedImage:		'queued.png',
            noImage:			'no16.png',
            yesImage:			'yes16.png'
        }
    };

    $.fn.ajaxEpSearch = function(options){
        options = $.extend({}, $.ajaxEpSearch.defaults, options);

        $('.epRetry').click(function(event){
            event.preventDefault();

            // Check if we have disabled the click
            if($(this).prop('enableClick') === '0') { return false; }

            selectedEpisode = $(this);

            $("#manualSearchModalFailed").modal('show');
        });

        $('.epSearch').click(function(event){
            event.preventDefault();

            // Check if we have disabled the click
            if ($(this).prop('enableClick') === '0') { return false; }

            selectedEpisode = $(this);

            if ($(this).parent().parent().children(".col-status").children(".quality").length) {
                $("#manualSearchModalQuality").modal('show');
            } else {
                manualSearch();
            }
        });

        $('#manualSearchModalFailed .btn').click(function(){
            failedDownload = ($(this).text().toLowerCase() === 'yes');
            $("#manualSearchModalQuality").modal('show');
        });

        $('#manualSearchModalQuality .btn').click(function(){
            qualityDownload = ($(this).text().toLowerCase() === 'yes');
            manualSearch();
        });

        function manualSearch(){
            var imageName, imageResult, htmlContent;

            var parent = selectedEpisode.parent();

            // Create var for anchor
            var link = selectedEpisode;

            // Create var for img under anchor and set options for the loading gif
            var img = selectedEpisode.children('img');
            img.prop('title','loading');
            img.prop('alt','');
            img.prop('src',srRoot+'/images/' + options.loadingImage);

            var url = selectedEpisode.prop('href');

            if (failedDownload === false) {
                url = url.replace("retryEpisode", "searchEpisode");
            }

            url = url + "&downCurQuality=" + (qualityDownload ? '1' : '0');

            $.getJSON(url, function(data){

                // if they failed then just put the red X
                if (data.result.toLowerCase() === 'failure') {
                    imageName = options.noImage;
                    imageResult = 'failed';

                // if the snatch was successful then apply the corresponding class and fill in the row appropriately
                } else {
                    imageName = options.loadingImage;
                    imageResult = 'success';
                    // color the row
                    if (options.colorRow) {
                        parent.parent().removeClass('skipped wanted qual good unaired').addClass('snatched');
                    }
                    // applying the quality class
                    var rSearchTerm = /(\w+)\s\((.+?)\)/;
                        htmlContent = data.result.replace(rSearchTerm,"$1"+' <span class="quality '+data.quality+'">'+"$2"+'</span>');
                    // update the status column if it exists
                    parent.siblings('.col-status').html(htmlContent);
                    // Only if the queuing was successful, disable the onClick event of the loading image
                    disableLink(link);
                }

                // put the corresponding image as the result of queuing of the manual search
                img.prop('title', imageResult);
                img.prop('alt', imageResult);
                img.prop('height', options.size);
                img.prop('src', srRoot+"/images/" + imageName);
            });

            // don't follow the link
            return false;
        }
    };
})();
