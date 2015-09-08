<%inherit file="/layouts/main.mako"/>
<%!
    import sickbeard
%>
<%block name="scripts">
<script type="text/javascript" src="${sbRoot}/js/recommendedShows.js?${sbPID}"></script>
<script type="text/javascript" src="${sbRoot}/js/rootDirs.js?${sbPID}"></script>
<script type="text/javascript" src="${sbRoot}/js/plotTooltip.js?${sbPID}"></script>
<script type="text/javascript" charset="utf-8">
$(document).ready(function(){
    $( "#tabs" ).tabs({
        collapsible: true,
        selected: ${('0', '-1')[bool(sickbeard.ROOT_DIRS)]}
    });

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

window.setInterval('location.reload(true)', 600000); // Refresh every 10 minutes
</script>
</%block>
<%block name="content">
% if not header is UNDEFINED:
    <h1 class="header">${header}</h1>
% else:
    <h1 class="title">${title}</h1>
% endif

<div id="tabs">
    <ul>
        <li><a href="#tabs-1">Manage Directories</a></li>
        <li><a href="#tabs-2">Customize Options</a></li>
    </ul>
    <div id="tabs-1" class="existingtabs">
        <%include file="/inc_rootDirs.mako"/>
    </div>
    <div id="tabs-2" class="existingtabs">
        <%include file="/inc_addShowOptions.mako"/>
    </div>
    <br>

    <span>Sort By:</span>
    <select id="showsort" class="form-control form-control-inline input-sm">
        <option value="name">Name</option>
        <option value="original" selected="selected">Original</option>
        <option value="votes">Votes</option>
        <option value="rating">% Rating</option>
        <option value="rating_votes">% Rating > Votes</option>
    </select>

    <span style="margin-left:12px">Sort Order:</span>
    <select id="showsortdirection" class="form-control form-control-inline input-sm">
        <option value="asc" selected="selected">Asc</option>
        <option value="desc">Desc</option>
    </select>
</div>

<br />
<div id="trendingShows"></div>
<br />
</%block>
