(function(){
    $.fn.ajaxEpSubtitlesSearch = function(){
        $('.epSubtitlesSearch').click(function(){
            var subtitlesTd = $(this).parent().siblings('.col-subtitles');
            var subtitlesSearchLink = $(this);
            // fill with the ajax loading gif
            subtitlesSearchLink.empty();
            subtitlesSearchLink.append($("<img/>").attr({"src": srRoot+"/images/loading16.gif", "alt": "", "title": "loading"}));
            $.getJSON($(this).attr('href'), function(data){
                if (data.result.toLowerCase() !== "failure" && data.result.toLowerCase() !== "no subtitles downloaded") {
                    // clear and update the subtitles column with new informations
                    var subtitles = data.subtitles.split(',');
                    subtitlesTd.empty();
                    $.each(subtitles,function(index, language){
                        if (language !== "") {
                            if (index !== subtitles.length - 1) {
                                subtitlesTd.append($("<img/>").attr({"src": srRoot+"/images/subtitles/flags/"+language+".png", "alt": language, "width": 16, "height": 11}));
                            } else {
                                subtitlesTd.append($("<img/>").attr({"src": srRoot+"/images/subtitles/flags/"+language+".png", "alt": language, "width": 16, "height": 11}));
                            }
                        }
                    });
                    // don't allow other searches
                    subtitlesSearchLink.remove();
                } else {
                    subtitlesSearchLink.remove();
                }
            });

            // don't follow the link
            return false;
        });
    };

    $.fn.ajaxEpMergeSubtitles = function(){
        $('.epMergeSubtitles').click(function(){
            var subtitlesMergeLink = $(this);
            // fill with the ajax loading gif
            subtitlesMergeLink.empty();
            subtitlesMergeLink.append($("<img/>").attr({"src": srRoot+"/images/loading16.gif", "alt": "", "title": "loading"}));
            $.getJSON($(this).attr('href'), function(){
                // don't allow other merges
                subtitlesMergeLink.remove();
            });
            // don't follow the link
            return false;
        });
    };

    $.ajaxRetrySubtitlesSearch = {
        defaults: {
            size:               11,
            loadingImage:       'loading16.gif',
            noImage:            'no16.png'
        }
    };

    $.fn.ajaxRetrySubtitlesSearch = function(options){
        options = $.extend({}, $.ajaxRetrySubtitlesSearch.defaults, options);

        function downloadSubtitles(){
            var imageName, imageResult, htmlContent;

            var parent = selectedEpisode.parent();

            // Create var for anchor
            var link = selectedEpisode;

            // Create var for img under anchor and set options for the loading gif
            var img = selectedEpisode.children('img');
            img.prop('title','loading');
            img.prop('alt','');
            img.prop('src',srRoot + '/images/' + options.loadingImage);

            var url = selectedEpisode.prop('href');
            disableLink(link);

            $.getJSON(url, function(data){

                // if they failed then just put the red X
                if (data.result.toLowerCase() === 'failure') {
                    imageName = srRoot + '/images/' + options.noImage;
                    imageResult = 'failed';
                // if the subtitle was successfully downloaded then apply the corresponding image
                } else {
                    imageName = link.children('img').data('image-url');
                    imageResult = 'success';

                }

                // put the corresponding image as the result of downloading subtitles
                img.prop('title', imageResult);
                img.prop('alt', imageResult);
                img.prop('height', options.size);
                img.prop('src', imageName);

                //Enable back the link
                enableLink(link);
            });

            // don't follow the link
            return false;
        }

        $('.epRetrySubtitlesSearch').on('click', function(event){
            event.preventDefault();

            // Check if we have disabled the click
            if ($(this).prop('enableClick') === '0') { return false; }

            selectedEpisode = $(this);

            $("#confirmSubtitleDownloadModal").modal('show');

        });

        $('#confirmSubtitleDownloadModal .btn.btn-success').on('click', function(){
            downloadSubtitles();
        });
    };

})();
