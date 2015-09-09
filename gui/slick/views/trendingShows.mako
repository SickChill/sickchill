<%inherit file="/layouts/main.mako"/>
<%!
    import sickbeard
    import datetime
    import re
    from sickbeard.common import SKIPPED, WANTED, UNAIRED, ARCHIVED, IGNORED, SNATCHED, SNATCHED_PROPER, SNATCHED_BEST, FAILED
    from sickbeard.common import Quality, qualityPresets, qualityPresetStrings
    from sickbeard import sbdatetime
    from sickbeard.helpers import anon_url
%>
<%block name="scripts">
<script type="text/javascript">
$(document).ready(function(){
    // initialise combos for dirty page refreshes
    $('#showsort').val('original');
    $('#showsortdirection').val('asc');

    var $container = [$('#container')];
    $.each($container, function (j) {
        this.isotope({
            itemSelector: '.trakt_show',
            sortBy: 'original-order',
            layoutMode: 'fitRows',
            getSortData: {
                name: function( itemElem ) {
                    var name = $( itemElem ).attr('data-name') || '';
% if not sickbeard.SORT_ARTICLE:
                    name = name.replace(/^(The|A|An)\s/i, '');
% endif
                    return name.toLowerCase();
                },
                rating: '[data-rating] parseInt',
                votes: '[data-votes] parseInt',
            }
        });
    });

    $('#showsort').on( 'change', function() {
        var sortCriteria;
        switch (this.value) {
            case 'original':
                sortCriteria = 'original-order'
                break;
            case 'rating':
                /* randomise, else the rating_votes can already
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
                sortCriteria = 'name'
                break;
        }
        $('#container').isotope({sortBy: sortCriteria});
    });

    $('#showsortdirection').on( 'change', function() {
        $('#container').isotope({sortAscending: ('asc' == this.value)});
    });
});
</script>
</%block>
<%block name="content">
<div id="container">
% if not trending_shows:
    <div class="trakt_show" style="width:100%; margin-top:20px">
        <p class="red-text">Trakt API did not return any results, please check your config.
    </div>
% else:
% for cur_show in trending_shows:
    <% show_url = 'http://www.trakt.tv/shows/%s' % cur_show['show']['ids']['slug'] %>

    <div class="trakt_show" data-name="${cur_show['show']['title']}" data-rating="${cur_show['show']['rating']}" data-votes="${cur_show['show']['votes']}">
        <div class="traktContainer">
            <div class="trakt-image">
                <a class="trakt-image" href="${anon_url(show_url)}" target="_blank"><img alt="" class="trakt-image" src="${cur_show['show']['images']['poster']['thumb']}" /></a>
            </div>

            <div class="show-title">
                ${(cur_show['show']['title'], '<span>&nbsp;</span>')['' == cur_show['show']['title']]}
            </div>

        <div class="clearfix">
            <p>${int(cur_show['show']['rating']*10)}% <img src="${sbRoot}/images/heart.png"></p>
            <i>${cur_show['show']['votes']} votes</i>
            <div class="traktShowTitleIcons">
                <a href="${sbRoot}/home/addShows/addTraktShow?indexer_id=${cur_show['show']['ids']['tvdb']}&amp;showName=${cur_show['show']['title']}" class="btn btn-xs">Add Show</a>
                % if blacklist:
                <a href="${sbRoot}/home/addShows/addShowToBlacklist?indexer_id=${cur_show['show']['ids']['tvdb'] or cur_show['show']['ids']['tvrage']}" class="btn btn-xs">Remove Show</a>
                % endif
            </div>
        </div>
        </div>
    </div>
% endfor
% endif
</div>
</%block>
