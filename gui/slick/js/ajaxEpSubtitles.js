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
                        if (language !== "" && language !== "und") {
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
})();
