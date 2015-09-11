<%inherit file="/layouts/main.mako"/>
<%!
    import sickbeard
    import calendar
    from sickbeard.common import SKIPPED, WANTED, UNAIRED, ARCHIVED, IGNORED, SNATCHED, SNATCHED_PROPER, SNATCHED_BEST, FAILED
    from sickbeard.common import Quality, qualityPresets, qualityPresetStrings
    from sickbeard import db, sbdatetime, network_timezones
    import datetime
    import re

    myDB = db.DBConnection()
    today = str(datetime.date.today().toordinal())
    layout = sickbeard.HOME_LAYOUT
    fuzzydate = 'airdate'

    status_quality  = '(' + ','.join([str(x) for x in Quality.SNATCHED + Quality.SNATCHED_PROPER]) + ')'
    status_download = '(' + ','.join([str(x) for x in Quality.DOWNLOADED + [ARCHIVED]]) + ')'

    sql_statement  = 'SELECT showid, '

    sql_statement += '(SELECT COUNT(*) FROM tv_episodes WHERE showid=tv_eps.showid AND season > 0 AND episode > 0 AND airdate > 1 AND status IN ' + status_quality + ') AS ep_snatched, '
    sql_statement += '(SELECT COUNT(*) FROM tv_episodes WHERE showid=tv_eps.showid AND season > 0 AND episode > 0 AND airdate > 1 AND status IN ' + status_download + ') AS ep_downloaded, '
    sql_statement += '(SELECT COUNT(*) FROM tv_episodes WHERE showid=tv_eps.showid AND season > 0 AND episode > 0 AND airdate > 1 '
    sql_statement += ' AND ((airdate <= ' + today + ' AND (status = ' + str(SKIPPED) + ' OR status = ' + str(WANTED) + ' OR status = ' + str(FAILED) + ')) '
    sql_statement += ' OR (status IN ' + status_quality + ') OR (status IN ' + status_download + '))) AS ep_total, '

    sql_statement += ' (SELECT airdate FROM tv_episodes WHERE showid=tv_eps.showid AND airdate >= ' + today + ' AND (status = ' + str(UNAIRED) + ' OR status = ' + str(WANTED) + ') ORDER BY airdate ASC LIMIT 1) AS ep_airs_next, '
    sql_statement += ' (SELECT airdate FROM tv_episodes WHERE showid=tv_eps.showid AND airdate > 1 AND status <> ' + str(UNAIRED) + ' ORDER BY airdate DESC LIMIT 1) AS ep_airs_prev '
    sql_statement += ' FROM tv_episodes tv_eps GROUP BY showid'

    sql_result = myDB.select(sql_statement)

    show_stat = {}
    max_download_count = 1000

    for cur_result in sql_result:
        show_stat[cur_result['showid']] = cur_result
        if cur_result['ep_total'] > max_download_count:
            max_download_count = cur_result['ep_total']

    max_download_count = max_download_count * 100
%>
<%block name="scripts">
<script type="text/javascript" charset="utf-8">
$.tablesorter.addParser({
    id: 'loadingNames',
    is: function(s) {
        return false;
    },
    format: function(s) {
        if (s.indexOf('Loading...') == 0)
          return s.replace('Loading...','000');
        else
        % if not sickbeard.SORT_ARTICLE:
            return (s || '').replace(/^(The|A|An)\s/i,'');
        % else:
            return (s || '');
        % endif
    },
    type: 'text'
});

$.tablesorter.addParser({
    id: 'quality',
    is: function(s) {
        return false;
    },
    format: function(s) {
        return s.replace('hd1080p',5).replace('hd720p',4).replace('hd',3).replace('sd',2).replace('any',1).replace('custom',7);
    },
    type: 'numeric'
});

$.tablesorter.addParser({
    id: 'eps',
    is: function(s) {
        return false;
    },
    format: function(s) {
        match = s.match(/^(.*)/);

        if (match == null || match[1] == "?")
          return -10;

        var nums = match[1].split(" / ");
        if (nums[0].indexOf("+") != -1) {
            var num_parts = nums[0].split("+");
            nums[0] = num_parts[0];
        }

        nums[0] = parseInt(nums[0])
        nums[1] = parseInt(nums[1])

        if (nums[0] === 0)
          return nums[1];

        var finalNum = parseInt(${max_download_count}*nums[0]/nums[1]);
        var pct = Math.round((nums[0]/nums[1])*100) / 1000
        if (finalNum > 0)
          finalNum += nums[0];

        return finalNum + pct;
    },
    type: 'numeric'
});

$(document).ready(function(){
    // This needs to be refined to work a little faster.
    $('.progressbar').each(function(progressbar){
        var showId = $(this).data('show-id');
        var percentage = $(this).data('progress-percentage');
        var classToAdd = percentage == 100 ? 100 : percentage > 80 ? 80 : percentage > 60 ? 60 : percentage > 40 ? 40 : 20;
        $(this).progressbar({ value:  percentage });
        $(this).data('progress-text') ? $(this).append('<div class="progressbarText" title="' + $(this).data('progress-tip') + '">' + $(this).data('progress-text') + '</div>') : '';
        $(this).find('.ui-progressbar-value').addClass('progress-' + classToAdd);
    });

    $("img#network").on('error', function(){
        $(this).parent().text($(this).attr('alt'));
        $(this).remove();
    });

    $("#showListTableShows:has(tbody tr)").tablesorter({
        sortList: [[7,1],[2,0]],
        textExtraction: {
            0: function(node) { return $(node).find("span").text().toLowerCase(); },
            1: function(node) { return $(node).find("span").text().toLowerCase(); },
            3: function(node) { return $(node).find("span").prop("title").toLowerCase(); },
            4: function(node) { return $(node).find("span").text().toLowerCase(); },
            5: function(node) { return $(node).find("span:first").text(); },
            6: function(node) { return $(node).data('show-size'); },
            7: function(node) { return $(node).find("img").attr("alt"); }
        },
        widgets: ['saveSort', 'zebra', 'stickyHeaders', 'filter', 'columnSelector'],
        headers: {
            0: { sorter: 'isoDate' },
            1: { columnSelector: false },
            2: { sorter: 'loadingNames' },
            4: { sorter: 'quality' },
            5: { sorter: 'eps' },
            % if sickbeard.FILTER_ROW:
                7: { filter : 'parsed' }
            % endif
        },
        widgetOptions : {
            % if sickbeard.FILTER_ROW:
                filter_columnFilters: true,
                filter_hideFilters : true,
                filter_saveFilters : true,
                filter_functions : {
                   5:function(e, n, f, i, r, c) {
                        var test = false;
                        var pct = Math.floor((n % 1) * 1000);
                        if (f === '') {
                           test = true;
                        } else {
                            var result = f.match(/(<|<=|>=|>)\s(\d+)/i);
                            if (result) {
                                if (result[1] === "<") {
                                    if (pct < parseInt(result[2])) {
                                        test = true;
                                    }
                                } else if (result[1] === "<=") {
                                    if (pct <= parseInt(result[2])) {
                                        test = true;
                                    }
                                } else if (result[1] === ">=") {
                                    if (pct >= parseInt(result[2])) {
                                        test = true;
                                    }
                                } else if (result[1] === ">") {
                                    if (pct > parseInt(result[2])) {
                                        test = true;
                                    }
                                }
                            }

                            var result = f.match(/(\d+)\s(-|to)\s(\d+)/i);
                            if (result) {
                                if ((result[2] === "-") || (result[2] === "to")) {
                                    if ((pct >= parseInt(result[1])) && (pct <= parseInt(result[3]))) {
                                        test = true;
                                    }
                                }
                            }

                            var result = f.match(/(=)?\s?(\d+)\s?(=)?/i);
                            if (result) {
                                if ((result[1] === "=") || (result[3] === "=")) {
                                    if (parseInt(result[2]) === pct) {
                                        test = true;
                                    }
                                }
                            }

                            if (!isNaN(parseFloat(f)) && isFinite(f)) {
                                if (parseInt(f) === pct) {
                                    test = true;
                                }
                            }
                        }
                        return test;
                    },
                },
            % else:
                filter_columnFilters: false,
            % endif
            filter_reset: '.resetshows',
            columnSelector_mediaquery: false,
        },
        sortStable: true,
        sortAppend: [[2,0]]
    });

    $("#showListTableAnime:has(tbody tr)").tablesorter({
        sortList: [[7,1],[2,0]],
        textExtraction: {
            0: function(node) { return $(node).find("span").text().toLowerCase(); },
            1: function(node) { return $(node).find("span").text().toLowerCase(); },
            3: function(node) { return $(node).find("span").prop("title").toLowerCase(); },
            4: function(node) { return $(node).find("span").text().toLowerCase(); },
            5: function(node) { return $(node).find("span:first").text(); },
            6: function(node) { return $(node).data('show-size'); },
            7: function(node) { return $(node).find("img").attr("alt"); }
        },
        widgets: ['saveSort', 'zebra', 'stickyHeaders', 'filter', 'columnSelector'],
        headers: {
            0: { sorter: 'isoDate' },
            1: { columnSelector: false },
            2: { sorter: 'loadingNames' },
            4: { sorter: 'quality' },
            5: { sorter: 'eps' },
            % if sickbeard.FILTER_ROW:
                7: { filter : 'parsed' }
            % endif
        },
        widgetOptions : {
            % if sickbeard.FILTER_ROW:
                filter_columnFilters: true,
                filter_hideFilters : true,
                filter_saveFilters : true,
                filter_functions : {
                   5:function(e, n, f, i, r, c) {
                        var test = false;
                        var pct = Math.floor((n % 1) * 1000);
                        if (f === '') {
                           test = true;
                        } else {
                            var result = f.match(/(<|<=|>=|>)\s(\d+)/i);
                            if (result) {
                                if (result[1] === "<") {
                                    if (pct < parseInt(result[2])) {
                                        test = true;
                                    }
                                } else if (result[1] === "<=") {
                                    if (pct <= parseInt(result[2])) {
                                        test = true;
                                    }
                                } else if (result[1] === ">=") {
                                    if (pct >= parseInt(result[2])) {
                                        test = true;
                                    }
                                } else if (result[1] === ">") {
                                    if (pct > parseInt(result[2])) {
                                        test = true;
                                    }
                                }
                            }

                            var result = f.match(/(\d+)\s(-|to)\s(\d+)/i);
                            if (result) {
                                if ((result[2] === "-") || (result[2] === "to")) {
                                    if ((pct >= parseInt(result[1])) && (pct <= parseInt(result[3]))) {
                                        test = true;
                                    }
                                }
                            }

                            var result = f.match(/(=)?\s?(\d+)\s?(=)?/i);
                            if (result) {
                                if ((result[1] === "=") || (result[3] === "=")) {
                                    if (parseInt(result[2]) === pct) {
                                        test = true;
                                    }
                                }
                            }

                            if (!isNaN(parseFloat(f)) && isFinite(f)) {
                                if (parseInt(f) === pct) {
                                    test = true;
                                }
                            }
                        }
                        return test;
                    },
                },
            % else:
                filter_columnFilters: false,
            % endif
            filter_reset: '.resetanime',
            columnSelector_mediaquery: false,
        },
        sortStable: true,
        sortAppend: [[2,0]]
    });

    if ($("#showListTableShows").find("tbody").find("tr").size() > 0)
        $.tablesorter.filter.bindSearch( "#showListTableShows", $('.search') );

    % if sickbeard.ANIME_SPLIT_HOME:
        if ($("#showListTableAnime").find("tbody").find("tr").size() > 0)
            $.tablesorter.filter.bindSearch( "#showListTableAnime", $('.search') );
    % endif

    % if sickbeard.FUZZY_DATING:
    fuzzyMoment({
        dtInline : ${('true', 'false')[layout == 'poster']},
        containerClass : '.${fuzzydate}',
        dateHasTime : false,
        dateFormat : '${sickbeard.DATE_PRESET}',
        timeFormat : '${sickbeard.TIME_PRESET}',
        trimZero : ${('false', 'true')[bool(sickbeard.TRIM_ZERO)]}
    });
    % endif

    var $container = [$('#container'), $('#container-anime')];

    $.each($container, function (j) {
        this.isotope({
            itemSelector: '.show',
            sortBy : '${sickbeard.POSTER_SORTBY}',
            sortAscending: ${sickbeard.POSTER_SORTDIR},
            layoutMode: 'masonry',
            masonry: {
                columnWidth: 13,
                isFitWidth: true
            },
            getSortData: {
                name: function( itemElem ) {
                    var name = $( itemElem ).attr('data-name');
                    % if not sickbeard.SORT_ARTICLE:
                        return (name || '').replace(/^(The|A|An)\s/i,'');
                    % else:
                        return (name || '');
                    % endif
                },
                network: '[data-network]',
                date: function( itemElem ) {
                    var date = $( itemElem ).attr('data-date');
                    return date.length && parseInt( date, 10 ) || Number.POSITIVE_INFINITY;
                },
                progress: function( itemElem ) {
                    var progress = $( itemElem ).attr('data-progress');
                    return progress.length && parseInt( progress, 10 ) || Number.NEGATIVE_INFINITY;
                }
            }
        });
    });

    $('#postersort').on( 'change', function() {
        var sortValue = this.value;
        $('#container').isotope({ sortBy: sortValue });
        $('#container-anime').isotope({ sortBy: sortValue });
        $.get(this.options[this.selectedIndex].getAttribute('data-sort'));
    });

    $('#postersortdirection').on( 'change', function() {
        var sortDirection = this.value;
        sortDirection = sortDirection == 'true';
        $('#container').isotope({ sortAscending: sortDirection });
        $('#container-anime').isotope({ sortAscending: sortDirection });
        $.get(this.options[this.selectedIndex].getAttribute('data-sort'));
    });

    $('#popover')
        .popover({
          placement: 'bottom',
          html: true, // required if content has HTML
          content: '<div id="popover-target"></div>'
        })
        // bootstrap popover event triggered when the popover opens
        .on('shown.bs.popover', function () {
          // call this function to copy the column selection code into the popover
          $.tablesorter.columnSelector.attachTo( $('#showListTableShows'), '#popover-target');
          % if sickbeard.ANIME_SPLIT_HOME:
          $.tablesorter.columnSelector.attachTo( $('#showListTableAnime'), '#popover-target');
          % endif
        });

        // Hides size column for now until we can fix it
        $('[data-show-size]').hide();
        $('[data-column="6"]').hide();
});
</script>
</%block>
<%block name="content">
<%namespace file="/inc_defs.mako" import="renderQualityPill"/>
% if not header is UNDEFINED:
    <h1 class="header">${header}</h1>
% else:
    <h1 class="title">${title}</h1>
% endif

<div id="HomeLayout" class="pull-right hidden-print" style="margin-top: -40px;">
    % if layout != 'poster':
        <button id="popover" type="button" class="btn btn-inline">Select Column</button>
    % endif
    <span> Layout:
        <select name="layout" class="form-control form-control-inline input-sm" onchange="location = this.options[this.selectedIndex].value;">
            <option value="${sbRoot}/setHomeLayout/?layout=poster" ${('', 'selected="selected"')[layout == 'poster']}>Poster</option>
            <option value="${sbRoot}/setHomeLayout/?layout=small" ${('', 'selected="selected"')[layout == 'small']}>Small Poster</option>
            <option value="${sbRoot}/setHomeLayout/?layout=banner" ${('', 'selected="selected"')[layout == 'banner']}>Banner</option>
            <option value="${sbRoot}/setHomeLayout/?layout=simple" ${('', 'selected="selected"')[layout == 'simple']}>Simple</option>
        </select>
        % if layout != 'poster':
        Search:
            <input class="search form-control form-control-inline input-sm input200" type="search" data-column="2" placeholder="Search Show Name">
            <button type="button" class="resetshows resetanime btn btn-inline">Reset Search</button>
        % endif
    </span>

    % if layout == 'poster':
    &nbsp;
    <span> Sort By:
        <select id="postersort" class="form-control form-control-inline input-sm">
            <option value="name" data-sort="${sbRoot}/setPosterSortBy/?sort=name" ${('', 'selected="selected"')[sickbeard.POSTER_SORTBY == 'name']}>Name</option>
            <option value="date" data-sort="${sbRoot}/setPosterSortBy/?sort=date" ${('', 'selected="selected"')[sickbeard.POSTER_SORTBY == 'date']}>Next Episode</option>
            <option value="network" data-sort="${sbRoot}/setPosterSortBy/?sort=network" ${('', 'selected="selected"')[sickbeard.POSTER_SORTBY == 'network']}>Network</option>
            <option value="progress" data-sort="${sbRoot}/setPosterSortBy/?sort=progress" ${('', 'selected="selected"')[sickbeard.POSTER_SORTBY == 'progress']}>Progress</option>
        </select>
    </span>
    &nbsp;
    <span> Sort Order:
        <select id="postersortdirection" class="form-control form-control-inline input-sm">
            <option value="true" data-sort="${sbRoot}/setPosterSortDir/?direction=1" ${('', 'selected="selected"')[sickbeard.POSTER_SORTDIR == 1]}>Asc</option>
            <option value="false" data-sort="${sbRoot}/setPosterSortDir/?direction=0" ${('', 'selected="selected"')[sickbeard.POSTER_SORTDIR == 0]}>Desc</option>
        </select>
    </span>
    &nbsp;

    % endif
</div>

% for curShowlist in showlists:
    <% curListType = curShowlist[0] %>
    <% myShowList = list(curShowlist[1]) %>
    % if curListType == "Anime":
        <h1 class="header">Anime List</h1>
    % endif
% if layout == 'poster':
<div id="${('container', 'container-anime')[curListType == 'Anime' and layout == 'poster']}" class="clearfix">
<div class="posterview">
% for curLoadingShow in sickbeard.showQueueScheduler.action.loadingShowList:
    % if curLoadingShow.show == None:
        <div class="show" data-name="0" data-date="010101" data-network="0" data-progress="101">
            <img alt="" title="${curLoadingShow.show_name}" class="show-image" style="border-bottom: 1px solid #111;" src="${sbRoot}/images/poster.png" />
            <div class="show-details">
                <div class="show-add">Loading... (${curLoadingShow.show_name})</div>
            </div>
        </div>

    % endif
% endfor

<% myShowList.sort(lambda x, y: cmp(x.name, y.name)) %>
% for curShow in myShowList:

<%
    cur_airs_next = ''
    cur_snatched = 0
    cur_downloaded = 0
    cur_total = 0
    download_stat_tip = ''
    display_status = curShow.status

    if None is not display_status:
        if re.search(r'(?i)(?:new|returning)\s*series', curShow.status):
            display_status = 'Continuing'
        elif re.search(r'(?i)(?:nded)', curShow.status):
            display_status = 'Ended'

    if curShow.indexerid in show_stat:
        cur_airs_next = show_stat[curShow.indexerid]['ep_airs_next']

        cur_snatched = show_stat[curShow.indexerid]['ep_snatched']
        if not cur_snatched:
            cur_snatched = 0

        cur_downloaded = show_stat[curShow.indexerid]['ep_downloaded']
        if not cur_downloaded:
            cur_downloaded = 0

        cur_total = show_stat[curShow.indexerid]['ep_total']
        if not cur_total:
            cur_total = 0

    if cur_total != 0:
        download_stat = str(cur_downloaded)
        download_stat_tip = "Downloaded: " + str(cur_downloaded)
        if cur_snatched > 0:
            download_stat = download_stat
            download_stat_tip = download_stat_tip + "&#013;" + "Snatched: " + str(cur_snatched)

        download_stat = download_stat + " / " + str(cur_total)
        download_stat_tip = download_stat_tip + "&#013;" + "Total: " + str(cur_total)
    else:
        download_stat = '?'
        download_stat_tip = "no data"

    nom = cur_downloaded
    den = cur_total
    if den == 0:
        den = 1

    progressbar_percent = nom * 100 / den

    data_date = '6000000000.0'
    if cur_airs_next:
        data_date = calendar.timegm(sbdatetime.sbdatetime.convert_to_setting(network_timezones.parse_date_time(cur_airs_next, curShow.airs, curShow.network)).timetuple())
    elif None is not display_status:
        if 'nded' not in display_status and 1 == int(curShow.paused):
            data_date = '5000000500.0'
        elif 'ontinu' in display_status:
            data_date = '5000000000.0'
        elif 'nded' in display_status:
            data_date = '5000000100.0'
%>
    <div class="show" id="show${curShow.indexerid}" data-name="${curShow.name}" data-date="${data_date}" data-network="${curShow.network}" data-progress="${progressbar_percent}">
        <div class="show-image">
            <a href="${sbRoot}/home/displayShow?show=${curShow.indexerid}"><img alt="" class="show-image" src="${sbRoot}/showPoster/?show=${curShow.indexerid}&amp;which=poster_thumb" /></a>
        </div>

        <div class="progressbar hidden-print" style="position:relative;" data-show-id="${curShow.indexerid}" data-progress-percentage="${progressbar_percent}"></div>

        <div class="show-title">
            ${curShow.name}
        </div>

        <div class="show-date">
% if cur_airs_next:
    <% ldatetime = sbdatetime.sbdatetime.convert_to_setting(network_timezones.parse_date_time(cur_airs_next, curShow.airs, curShow.network)) %>
    <span class="${fuzzydate}">
    <%
        try:
            out = str(sbdatetime.sbdatetime.sbfdate(ldatetime))
        except ValueError:
            out = 'Invalid date'
            pass
    %>
        ${out}
    </span>
% else:
    <%
    output_html = '?'
    display_status = curShow.status
    if None is not display_status:
        if 'nded' not in display_status and 1 == int(curShow.paused):
          output_html = 'Paused'
        elif display_status:
            output_html = display_status
    %>
    ${output_html}
% endif
        </div>

        <table width="100%" cellspacing="1" border="0" cellpadding="0">
            <tr>
                <td class="show-table">
                    <span class="show-dlstats" title="${download_stat_tip}">${download_stat}</span>
                </td>

                <td class="show-table">
                    % if layout != 'simple':
                        % if curShow.network:
                            <span title="${curShow.network}"><img class="show-network-image" src="${sbRoot}/showPoster/?show=${curShow.indexerid}&amp;which=network" alt="${curShow.network}" title="${curShow.network}" /></span>
                        % else:
                            <span title="No Network"><img class="show-network-image" src="${sbRoot}/images/network/nonetwork.png" alt="No Network" title="No Network" /></span>
                        % endif
                    % else:
                        <span title="${curShow.network}">${curShow.network}</span>
                    % endif
                </td>

                <td class="show-table">
		    ${renderQualityPill(curShow.quality, overrideClass="show-quality")}
                </td>
            </tr>
        </table>

    </div>

% endfor
</div>
</div>

% else:

<table id="showListTable${curListType}" class="tablesorter" cellspacing="1" border="0" cellpadding="0">

    <thead>
        <tr>
            <th class="nowrap">Next Ep</th>
            <th class="nowrap">Prev Ep</th>
            <th>Show</th>
            <th>Network</th>
            <th>Quality</th>
            <th>Downloads</th>
            ## <th>Size</th>
            <th>Active</th>
            <th>Status</th>
        </tr>
    </thead>

    <tfoot class="hidden-print">
        <tr>
            <th rowspan="1" colspan="1" align="center"><a href="${sbRoot}/home/addShows/">Add ${('Show', 'Anime')[curListType == 'Anime']}</a></th>
            <th>&nbsp;</th>
            <th>&nbsp;</th>
            <th>&nbsp;</th>
            <th>&nbsp;</th>
            <th>&nbsp;</th>
            ## <th>&nbsp;</th> // This is needed for size
            <th>&nbsp;</th>
            <th>&nbsp;</th>
        </tr>
    </tfoot>


% if sickbeard.showQueueScheduler.action.loadingShowList:
    <tbody class="tablesorter-infoOnly">
% for curLoadingShow in sickbeard.showQueueScheduler.action.loadingShowList:

    % if curLoadingShow.show != None and curLoadingShow.show in sickbeard.showList:
         <% continue %>
    % endif
  <tr>
    <td align="center">(loading)</td>
    <td></td>
    <td>
    % if curLoadingShow.show == None:
    <span title="">Loading... (${curLoadingShow.show_name})</span>
    % else:
    <a href="displayShow?show=${curLoadingShow.show.indexerid}">${curLoadingShow.show.name}</a>
    % endif
    </td>
    <td></td>
    <td></td>
    <td></td>
    <td></td>
  </tr>
% endfor
    </tbody>
% endif

    <tbody>

<% myShowList.sort(lambda x, y: cmp(x.name, y.name)) %>
% for curShow in myShowList:
<%
    cur_airs_next = ''
    cur_airs_prev = ''
    cur_snatched = 0
    cur_downloaded = 0
    cur_total = 0
    download_stat_tip = ''

    if curShow.indexerid in show_stat:
        cur_airs_next = show_stat[curShow.indexerid]['ep_airs_next']
        cur_airs_prev = show_stat[curShow.indexerid]['ep_airs_prev']

        cur_snatched = show_stat[curShow.indexerid]['ep_snatched']
        if not cur_snatched:
            cur_snatched = 0

        cur_downloaded = show_stat[curShow.indexerid]['ep_downloaded']
        if not cur_downloaded:
            cur_downloaded = 0

        cur_total = show_stat[curShow.indexerid]['ep_total']
        if not cur_total:
            cur_total = 0

    if cur_total != 0:
        download_stat = str(cur_downloaded)
        download_stat_tip = "Downloaded: " + str(cur_downloaded)
        if cur_snatched > 0:
            download_stat = download_stat + "+" + str(cur_snatched)
            download_stat_tip = download_stat_tip + "&#013;" + "Snatched: " + str(cur_snatched)

        download_stat = download_stat + " / " + str(cur_total)
        download_stat_tip = download_stat_tip + "&#013;" + "Total: " + str(cur_total)
    else:
        download_stat = '?'
        download_stat_tip = "no data"

    nom = cur_downloaded
    den = cur_total
    if den == 0:
        den = 1

    progressbar_percent = nom * 100 / den
%>
    <tr>
    % if cur_airs_next:
        <% ldatetime = sbdatetime.sbdatetime.convert_to_setting(network_timezones.parse_date_time(cur_airs_next, curShow.airs, curShow.network)) %>
        % try:
            <% temp_sbfdate_next = sbdatetime.sbdatetime.sbfdate(ldatetime) %>
            <% temp_timegm_next = calendar.timegm(ldatetime.timetuple()) %>
            <td align="center" class="nowrap">
                <div class="${fuzzydate}">${temp_sbfdate_next}</div>
                <span class="sort_data">${temp_timegm_next}</span>
            </td>
        % except ValueError:
            <td align="center" class="nowrap"></td>
        % endtry
    % else:
        <td align="center" class="nowrap"></td>
    % endif

    % if cur_airs_prev:
        <% pdatetime = sbdatetime.sbdatetime.convert_to_setting(network_timezones.parse_date_time(cur_airs_prev, curShow.airs, curShow.network)) %>
        % try:
            <% temp_sbfdate_prev = sbdatetime.sbdatetime.sbfdate(pdatetime) %>
            <% temp_timegm_prev = calendar.timegm(pdatetime.timetuple()) %>
            <td align="center" class="nowrap">
                <div class="${fuzzydate}">${temp_sbfdate_prev}</div>
                <span class="sort_data">${temp_timegm_prev}</span>
            </td>
        % except ValueError:
            <td align="center" class="nowrap"></td>
        % endtry
    % else:
        <td align="center" class="nowrap"></td>
    % endif

    % if layout == 'small':
        <td class="tvShow">
            <div class="imgsmallposter ${layout}">
                <a href="${sbRoot}/showPoster/?show=${curShow.indexerid}&amp;which=${layout}" rel="dialog" title="${curShow.name}">
                    <img src="${sbRoot}/showPoster/?show=${curShow.indexerid}&amp;which=poster_thumb" class="${layout}" alt="${curShow.indexerid}"/>
                </a>
                <a href="${sbRoot}/home/displayShow?show=${curShow.indexerid}" style="vertical-align: middle;">${curShow.name}</a>
            </div>
        </td>
    % elif layout == 'banner':
        <td>
            <span style="display: none;">${curShow.name}</span>
            <div class="imgbanner ${layout}">
                <a href="${sbRoot}/home/displayShow?show=${curShow.indexerid}">
                <img src="${sbRoot}/showPoster/?show=${curShow.indexerid}&amp;which=banner" class="${layout}" alt="${curShow.indexerid}" title="${curShow.name}"/>
            </div>
        </td>
    % elif layout == 'simple':
        <td class="tvShow"><a href="${sbRoot}/home/displayShow?show=${curShow.indexerid}">${curShow.name}</a></td>
    % endif

    % if layout != 'simple':
        <td align="center">
        % if curShow.network:
            <span title="${curShow.network}" class="hidden-print"><img id="network" width="54" height="27" src="${sbRoot}/showPoster/?show=${curShow.indexerid}&amp;which=network" alt="${curShow.network}" title="${curShow.network}" /></span>
            <span class="visible-print-inline">${curShow.network}</span>
        % else:
            <span title="No Network" class="hidden-print"><img id="network" width="54" height="27" src="${sbRoot}/images/network/nonetwork.png" alt="No Network" title="No Network" /></span>
            <span class="visible-print-inline">No Network</span>
        % endif
        </td>
    % else:
        <td>
            <span title="${curShow.network}">${curShow.network}</span>
        </td>
    % endif

        <td align="center">${renderQualityPill(curShow.quality)}</td>

        <td align="center">
            ## This first span is used for sorting and is never displayed to user
            <span style="display: none;">${download_stat}</span>
            <div class="progressbar hidden-print" style="position:relative;" data-show-id="${curShow.indexerid}" data-progress-percentage="${progressbar_percent}" data-progress-text="${download_stat}" data-progress-tip="${download_stat_tip}"></div>
            <span class="visible-print-inline">${download_stat}</span>
        </td>

        ## <% show_size = sickbeard.helpers.get_size(curShow._location) %>
        ## <td align="center" data-show-size="${show_size}">${sickbeard.helpers.pretty_filesize(show_size)}</td>
        <td align="center" data-show-size="0"></td>

        <td align="center">
            <% paused = int(curShow.paused) == 0 and curShow.status == 'Continuing' %>
            <img src="${sbRoot}/images/${('no16.png', 'yes16.png')[bool(paused)]}" alt="${('No', 'Yes')[bool(paused)]}" width="16" height="16" />
        </td>

        <td align="center">
        <%
            display_status = curShow.status
            if None is not display_status:
                if re.search('(?i)(?:new|returning)\s*series', curShow.status):
                    display_status = 'Continuing'
                elif re.search('(?i)(?:nded)', curShow.status):
                    display_status = 'Ended'
        %>
        ${display_status}
        </td>
    </tr>
% endfor
</tbody>
</table>

% endif
% endfor
</%block>
