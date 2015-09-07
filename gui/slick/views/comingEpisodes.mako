<%inherit file="/layouts/main.mako"/>
<%!
    import sickbeard
    from sickbeard.helpers import anon_url
    from sickbeard import sbdatetime
    import datetime
    import time
    import re
%>
<%block name="scripts">
<% fuzzydate = 'airdate' %>
<% sort = sickbeard.COMING_EPS_SORT %>
<script type="text/javascript" src="${sbRoot}/js/ajaxEpSearch.js?${sbPID}"></script>
% if 'list' == layout:
<script type="text/javascript" src="${sbRoot}/js/plotTooltip.js?${sbPID}"></script>
<script type="text/javascript" charset="utf-8">
$.tablesorter.addParser({
    id: 'loadingNames',
    is: function(s) {
        return false
    },
    format: function(s) {
        if (0 == s.indexOf('Loading...'))
            return s.replace('Loading...', '000')
% if not sickbeard.SORT_ARTICLE:
            return (s || '').replace(/^(The|A|An)\s/i, '')
% else:
            return (s || '')
% endif
    },
    type: 'text'
});
$.tablesorter.addParser({
    id: 'quality',
    is: function(s) {
        return false
    },
    format: function(s) {
        return s.replace('hd1080p', 5).replace('hd720p', 4).replace('hd', 3).replace('sd', 2).replace('any', 1).replace('best', 0).replace('custom', 7)
    },
    type: 'numeric'
});
$.tablesorter.addParser({
    id: 'cDate',
    is: function(s) {
        return false
    },
    format: function(s) {
        return s
    },
    type: 'numeric'
});

$(document).ready(function(){
<% sort_codes = {'date': 0, 'show': 1, 'network': 4} %>
% if sort not in sort_codes:
    <% sort = 'date' %>
% endif

    sortList = [[${sort_codes[sort]}, 0]];

    $('#showListTable:has(tbody tr)').tablesorter({
        widgets: ['stickyHeaders'],
        sortList: sortList,
        textExtraction: {
            0: function(node) { return $(node).find('span').text().toLowerCase() },
            5: function(node) { return $(node).find('span').text().toLowerCase() }
        },
        headers: {
            0: { sorter: 'cDate' },
            1: { sorter: 'loadingNames' },
            2: { sorter: false },
            3: { sorter: false },
            4: { sorter: 'loadingNames' },
            5: { sorter: 'quality' },
            6: { sorter: false },
            7: { sorter: false },
            8: { sorter: false }
        }
    });

    $('#sbRoot').ajaxEpSearch();

    <% fuzzydate = 'airdate' %>
    % if sickbeard.FUZZY_DATING:
    fuzzyMoment({
        containerClass : '.${fuzzydate}',
        dateHasTime : true,
        dateFormat : '${sickbeard.DATE_PRESET}',
        timeFormat : '${sickbeard.TIME_PRESET}',
        trimZero : ${('false', 'true')[bool(sickbeard.TRIM_ZERO)]}
    });
    % endif

});
</script>
% elif layout in ['banner', 'poster']:
<script type="text/javascript" charset="utf-8">
$(document).ready(function(){
    $('#sbRoot').ajaxEpSearch({'size': 16, 'loadingImage': 'loading16' + themeSpinner + '.gif'});
    $('.ep_summary').hide();
    $('.ep_summaryTrigger').click(function() {
        $(this).next('.ep_summary').slideToggle('normal', function() {
            $(this).prev('.ep_summaryTrigger').attr('src', function(i, src) {
                return $(this).next('.ep_summary').is(':visible') ? src.replace('plus','minus') : src.replace('minus','plus')
            });
        });
    });

    % if sickbeard.FUZZY_DATING:
    fuzzyMoment({
        dtInline : true,
        dtGlue : ' at ',
        containerClass : '.${fuzzydate}',
        dateHasTime : true,
        dateFormat : '${sickbeard.DATE_PRESET}',
        timeFormat : '${sickbeard.TIME_PRESET}',
        trimZero : ${('false', 'true')[bool(sickbeard.TRIM_ZERO)]}
    });
    % endif

});
</script>
% endif
<script type="text/javascript" charset="utf-8">
window.setInterval('location.reload(true)', 600000); // Refresh every 10 minutes
</script>
</%block>
<%block name="css">
<style type="text/css">
#SubMenu {display:none;}
#contentWrapper {padding-top:30px;}
</style>
</%block>
<%block name="content">
<% sort = sickbeard.COMING_EPS_SORT %>
<% fuzzydate = 'airdate' %>
<%namespace file="/inc_defs.mako" import="renderQualityPill"/>
<h1 class="header">${header}</h1>
<div class="h2footer pull-right">
    <span>Layout:
        <select name="layout" class="form-control form-control-inline input-sm" onchange="location = this.options[this.selectedIndex].value;">
            <option value="${sbRoot}/setComingEpsLayout/?layout=poster" ${('', 'selected="selected"')[sickbeard.COMING_EPS_LAYOUT == 'poster']} >Poster</option>
            <option value="${sbRoot}/setComingEpsLayout/?layout=calendar" ${('', 'selected="selected"')[sickbeard.COMING_EPS_LAYOUT == 'calendar']} >Calendar</option>
            <option value="${sbRoot}/setComingEpsLayout/?layout=banner" ${('', 'selected="selected"')[sickbeard.COMING_EPS_LAYOUT == 'banner']} >Banner</option>
            <option value="${sbRoot}/setComingEpsLayout/?layout=list" ${('', 'selected="selected"')[sickbeard.COMING_EPS_LAYOUT == 'list']} >List</option>
        </select>
    </span>
    &nbsp;

    <span>Sort By:
        <select name="sort" class="form-control form-control-inline input-sm" onchange="location = this.options[this.selectedIndex].value;">
            <option value="${sbRoot}/setComingEpsSort/?sort=date" ${('', 'selected="selected"')[sickbeard.COMING_EPS_SORT == 'date']} >Date</option>
            <option value="${sbRoot}/setComingEpsSort/?sort=network" ${('', 'selected="selected"')[sickbeard.COMING_EPS_SORT == 'network']} >Network</option>
            <option value="${sbRoot}/setComingEpsSort/?sort=show" ${('', 'selected="selected"')[sickbeard.COMING_EPS_SORT == 'show']} >Show</option>
        </select>
    </span>
    &nbsp;

    <span>View Paused:
        <select name="viewpaused" class="form-control form-control-inline input-sm" onchange="location = this.options[this.selectedIndex].value;">
            <option value="${sbRoot}/toggleComingEpsDisplayPaused" ${('', 'selected="selected"')[not bool(sickbeard.COMING_EPS_DISPLAY_PAUSED)]}>Hidden</option>
            <option value="${sbRoot}/toggleComingEpsDisplayPaused" ${('', 'selected="selected"')[bool(sickbeard.COMING_EPS_DISPLAY_PAUSED)]}>Shown</option>
        </select>
    </span>
</div>

<div class="key pull-right">
% if 'calendar' != layout:
    <b>Key:</b>
    <span class="listing-key listing-overdue">Missed</span>
    <span class="listing-key listing-current">Current</span>
    <span class="listing-key listing-default">Future</span>
    <span class="listing-key listing-toofar">Distant</span>
% endif
    <a class="btn btn-inline forceBacklog" href="webcal://${sbHost}:${sbHttpPort}/calendar">
    <i class="icon-calendar icon-white"></i>Subscribe</a>
</div>

<br>

% if 'list' == layout:
<!-- start list view //-->
<% show_div = 'listing-default' %>

<input type="hidden" id="sbRoot" value="${sbRoot}" />

<table id="showListTable" class="sickbeardTable tablesorter seasonstyle" cellspacing="1" border="0" cellpadding="0">

    <thead>
        <tr>
            <th>Airdate</th>
            <th>Show</th>
            <th nowrap="nowrap">Next Ep</th>
            <th>Next Ep Name</th>
            <th>Network</th>
            <th>Quality</th>
            <th>Indexers</th>
            <th>Search</th>
        </tr>
    </thead>

    <tbody style="text-shadow:none;">

% for cur_result in sql_results:
<%
    cur_indexer = int(cur_result['indexer'])
    run_time = cur_result['runtime']

    if int(cur_result['paused']) and not sickbeard.COMING_EPS_DISPLAY_PAUSED:
        continue

    cur_ep_airdate = cur_result['localtime'].date()

    if run_time:
        cur_ep_enddate = cur_result['localtime'] + datetime.timedelta(minutes = run_time)
        if cur_ep_enddate < today:
            show_div = 'listing-overdue'
        elif cur_ep_airdate >= next_week.date():
            show_div = 'listing-toofar'
        elif cur_ep_airdate >= today.date() and cur_ep_airdate < next_week.date():
            if cur_ep_airdate == today.date():
                show_div = 'listing-current'
            else:
                show_div = 'listing-default'
%>

        <!-- start ${cur_result['show_name']} //-->
        <tr class="${show_div}">
            ## forced to use a div to wrap airdate, the column sort went crazy with a span
            <td align="center" nowrap="nowrap">
                <div class="${fuzzydate}">${sbdatetime.sbdatetime.sbfdatetime(cur_result['localtime']).decode(sickbeard.SYS_ENCODING)}</div><span class="sort_data">${time.mktime(cur_result['localtime'].timetuple())}</span>
            </td>

            <td class="tvShow" nowrap="nowrap"><a href="${sbRoot}/home/displayShow?show=${cur_result['showid']}">${cur_result['show_name']}</a>
% if int(cur_result['paused']):
                <span class="pause">[paused]</span>
% endif
            </td>

            <td nowrap="nowrap" align="center">
                ${'S%02iE%02i' % (int(cur_result['season']), int(cur_result['episode']))}
            </td>

            <td>
% if cur_result['description']:
                <img alt='' src='${sbRoot}/images/info32.png' height='16' width='16' class='plotInfo' id="plot_info_${'%s_%s_%s' % (str(cur_result['showid']), str(cur_result['season']), str(cur_result['episode']))}" />
% else:
                <img alt="" src="${sbRoot}/images/info32.png" width="16" height="16" class="plotInfoNone"  />
% endif
                ${cur_result['name']}
            </td>

            <td align="center">
                ${cur_result['network']}
            </td>

            <td align="center">
	        ${renderQualityPill(cur_result['quality'])}
            </td>

            <td align="center" style="vertical-align: middle;">
% if cur_result['imdb_id']:
                <a href="${anon_url('http://www.imdb.com/title/', cur_result['imdb_id'])}" rel="noreferrer" onclick="window.open(this.href, '_blank'); return false" title="http://www.imdb.com/title/${cur_result['imdb_id']}"><img alt="[imdb]" height="16" width="16" src="${sbRoot}/images/imdb.png" />
% endif
                <a href="${anon_url(sickbeard.indexerApi(cur_indexer).config['show_url'], cur_result['showid'])}" rel="noreferrer" onclick="window.open(this.href, '_blank'); return false" title="${sickbeard.indexerApi(cur_indexer).config['show_url']}${cur_result['showid']}"><img alt="${sickbeard.indexerApi(cur_indexer).name}" height="16" width="16" src="${sbRoot}/images/${sickbeard.indexerApi(cur_indexer).config['icon']}" /></a>
            </td>

            <td align="center">
                <a href="${sbRoot}/home/searchEpisode?show=${cur_result['showid']}&amp;season=${cur_result['season']}&amp;episode=${cur_result['episode']}" title="Manual Search" id="forceUpdate-${cur_result['showid']}x${cur_result['season']}x${cur_result['episode']}" class="forceUpdate epSearch"><img alt="[search]" height="16" width="16" src="${sbRoot}/images/search16.png" id="forceUpdateImage-${cur_result['showid']}" /></a>
            </td>
        </tr>
        <!-- end ${cur_result['show_name']} //-->
% endfor
    </tbody>

    <tfoot>
        <tr>
            <th rowspan="1" colspan="10" align="center">&nbsp</th>
        </tr>
    </tfoot>

</table>
<!-- end list view //-->


% elif layout in ['banner', 'poster']:
<!-- start non list view //-->
<%
    cur_segment = None
    too_late_header = False
    missed_header = False
    today_header = False
    show_div = 'ep_listing listing-default'
%>
% if 'show' == sort:
    <br /><br />
% endif

% for cur_result in sql_results:
<%
    cur_indexer = int(cur_result['indexer'])

    if int(cur_result['paused']) and not sickbeard.COMING_EPS_DISPLAY_PAUSED:
        continue

    run_time = cur_result['runtime']
%>
    % if 'network' == sort:
        <% show_network = ('no network', cur_result['network'])[bool(cur_result['network'])] %>
        % if cur_segment != show_network:
            <div class="comingepheader">
               <br><h2 class="network">${show_network}</h2>

            <% cur_segment = cur_result['network'] %>
        % endif
        <% cur_ep_airdate = cur_result['localtime'].date() %>

        % if run_time:
            <% cur_ep_enddate = cur_result['localtime'] + datetime.timedelta(minutes = run_time) %>
            % if cur_ep_enddate < today:
                <% show_div = 'ep_listing listing-overdue' %>
            % elif cur_ep_airdate >= next_week.date():
                <% show_div = 'ep_listing listing-toofar' %>
            % elif cur_ep_enddate >= today and cur_ep_airdate < next_week.date():
                % if cur_ep_airdate == today.date():
                    <% show_div = 'ep_listing listing-current' %>
                % else:
                    <% show_div = 'ep_listing listing-default' %>
                % endif
            % endif
        % endif
    % elif 'date' == sort:
        <% cur_ep_airdate = cur_result['localtime'].date() %>

        % if cur_segment != cur_ep_airdate:
            %if run_time:
                <% cur_ep_enddate = cur_result['localtime'] + datetime.timedelta(minutes = run_time) %>
                % if cur_ep_enddate < today and cur_ep_airdate != today.date() and not missed_header:
                        <br /><h2 class="day">Missed</h2>
                <% missed_header = True %>
                % elif cur_ep_airdate >= next_week.date() and not too_late_header:
                        <br /><h2 class="day">Later</h2>
                <% too_late_header = True %>
                % elif cur_ep_enddate >= today and cur_ep_airdate < next_week.date():
                    % if cur_ep_airdate == today.date():
                        <br /><h2 class="day">${datetime.date.fromordinal(cur_ep_airdate.toordinal()).strftime('%A').decode(sickbeard.SYS_ENCODING).capitalize()}<span style="font-size: 14px; vertical-align: top;">[Today]</span></h2>
                        <% today_header = True %>
                    % else:
                        <br /><h2 class="day">${datetime.date.fromordinal(cur_ep_airdate.toordinal()).strftime('%A').decode(sickbeard.SYS_ENCODING).capitalize()}</h2>
                    % endif
                % endif
            % endif
                <% cur_segment = cur_ep_airdate %>
        % endif

        % if cur_ep_airdate == today.date() and not today_header:
            <div class="comingepheader">
            <br /><h2 class="day">${datetime.date.fromordinal(cur_ep_airdate.toordinal()).strftime('%A').decode(sickbeard.SYS_ENCODING).capitalize()} <span style="font-size: 14px; vertical-align: top;">[Today]</span></h2>
            <% today_header = True %>
        % endif
        % if run_time:
            % if cur_ep_enddate < today:
                <% show_div = 'ep_listing listing-overdue' %>
            % elif cur_ep_airdate >= next_week.date():
                <% show_div = 'ep_listing listing-toofar' %>
            % elif cur_ep_enddate >= today and cur_ep_airdate < next_week.date():
                % if cur_ep_airdate == today.date():
                    <% show_div = 'ep_listing listing-current' %>
                % else:
                    <% show_div = 'ep_listing listing-default'%>
                % endif
            % endif
        % endif

        % elif 'show' == sort:
            <% cur_ep_airdate = cur_result['localtime'].date() %>

            % if run_time:
                <% cur_ep_enddate = cur_result['localtime'] + datetime.timedelta(minutes = run_time) %>
                % if cur_ep_enddate < today:
                    <% show_div = 'ep_listing listing-overdue listingradius' %>
                % elif cur_ep_airdate >= next_week.date():
                    <% show_div = 'ep_listing listing-toofar listingradius' %>
                % elif cur_ep_enddate >= today and cur_ep_airdate < next_week.date():
                    % if cur_ep_airdate == today.date():
                        <% show_div = 'ep_listing listing-current listingradius' %>
                    % else:
                        <% show_div = 'ep_listing listing-default listingradius' %>
                    % endif
                % endif
            % endif
        % endif

<div class="${show_div}" id="listing-${cur_result['showid']}">
    <div class="tvshowDiv">
        <table width="100%" border="0" cellpadding="0" cellspacing="0">
        <tr>
            <th ${('class="nobg"', 'rowspan="2"')[banner == layout]} valign="top">
                <a href="${sbRoot}/home/displayShow?show=${cur_result['showid']}"><img alt="" class="${('posterThumb', 'bannerThumb')[layout == 'banner']}" src="${sbRoot}/showPoster/?show=${cur_result['showid']}&amp;which=${(layout, 'poster_thumb')[layout == 'poster']}" /></a>
            </th>
% if 'banner' == layout:
        </tr>
        <tr>
% endif
            <td class="next_episode">
                <div class="clearfix">
                    <span class="tvshowTitle">
                        <a href="${sbRoot}/home/displayShow?show=${cur_result['showid']}">${cur_result['show_name']}
                    % if int(cur_result['paused']):
                        <span class="pause">[paused]</span>
                    % endif
                    </a></span>

                    <span class="tvshowTitleIcons">
% if cur_result['imdb_id']:
                        <a href="${anon_url('http://www.imdb.com/title/', cur_result['imdb_id'])}" rel="noreferrer" onclick="window.open(this.href, '_blank'); return false" title="http://www.imdb.com/title/${cur_result['imdb_id']}"><img alt="[imdb]" height="16" width="16" src="${sbRoot}/images/imdb.png" />
% endif
                        <a href="${anon_url(sickbeard.indexerApi(cur_indexer).config['show_url'], cur_result['showid'])}" rel="noreferrer" onclick="window.open(this.href, '_blank'); return false" title="${sickbeard.indexerApi(cur_indexer).config['show_url']}"><img alt="${sickbeard.indexerApi(cur_indexer).name}" height="16" width="16" src="${sbRoot}/images/${sickbeard.indexerApi(cur_indexer).config['icon']}" /></a>
                        <span><a href="${sbRoot}/home/searchEpisode?show=${cur_result['showid']}&amp;season=${cur_result['season']}&amp;episode=${cur_result['episode']}" title="Manual Search" id="forceUpdate-${cur_result['showid']}" class="epSearch forceUpdate"><img alt="[search]" height="16" width="16" src="${sbRoot}/images/search16.png" id="forceUpdateImage-${cur_result['showid']}" /></a></span>
                    </span>
                </div>

                <span class="title">Next Episode:</span> <span>${'S%02iE%02i' % (int(cur_result['season']), int(cur_result['episode']))} - ${cur_result['name']}</span>

                <div class="clearfix">

                    <span class="title">Airs: </span><span class="${fuzzydate}">${sbdatetime.sbdatetime.sbfdatetime(cur_result['localtime']).decode(sickbeard.SYS_ENCODING)}</span>${('', '<span> on %s</span>' % str(cur_result['network']))[bool(cur_result['network'])]}
                </div>

                <div class="clearfix">
                    <span class="title">Quality:</span>
	            ${renderQualityPill(cur_result['quality'])}
                </div>
            </td>
        </tr>
        <tr>
            <td style="vertical-align: top;">
                <div>
% if cur_result['description']:
                        <span class="title" style="vertical-align:middle;">Plot:</span>
                        <img class="ep_summaryTrigger" src="${sbRoot}/images/plus.png" height="16" width="16" alt="" title="Toggle Summary" /><div class="ep_summary">${cur_result['description']}</div>
% else:
                        <span class="title ep_summaryTriggerNone" style="vertical-align:middle;">Plot:</span>
                        <img class="ep_summaryTriggerNone" src="${sbRoot}/images/plus.png" height="16" width="16" alt="" />
% endif
                </div>
        </td>
        </tr>
        </table>
    </div>
</div>

<!-- end ${cur_result['show_name']} //-->
% endfor

<!-- end non list view //-->
% endif

% if 'calendar' == layout:

## <% today = datetime.date.today() %>
<% dates = [today.date() + datetime.timedelta(days = i) for i in range(7)] %>
<% tbl_day = 0 %>
<br>
<br>
<div class="calendarWrapper">
<input type="hidden" id="sbRoot" value="${sbRoot}" />
    % for day in dates:
    <% tbl_day += 1 %>
        <table class="sickbeardTable tablesorter calendarTable ${'cal-%s' % (('even', 'odd')[bool(tbl_day % 2)])}" cellspacing="0" border="0" cellpadding="0">
        <thead><tr><th>${day.strftime('%A').decode(sickbeard.SYS_ENCODING).capitalize()}</th></tr></thead>
        <tbody>
        <% day_has_show = False %>
        % for cur_result in sql_results:
            % if int(cur_result['paused']) and not sickbeard.COMING_EPS_DISPLAY_PAUSED:
                <% continue %>
            % endif

            <% cur_indexer = int(cur_result['indexer']) %>
            <% run_time = cur_result['runtime'] %>
            <% airday = cur_result['localtime'].date() %>

            % if airday == day:
                % try:
                    <% day_has_show = True %>
                    <% airtime = sbdatetime.sbdatetime.fromtimestamp(time.mktime(cur_result['localtime'].timetuple())).sbftime().decode(sickbeard.SYS_ENCODING) %>
                    % if sickbeard.TRIM_ZERO:
                        <% airtime = re.sub(r'0(\d:\d\d)', r'\1', airtime, 0, re.IGNORECASE | re.MULTILINE) %>
                    % endif
                % except OverflowError:
                    <% airtime = "Invalid" %>
                % endtry

                <tr>
                    <td class="calendarShow">
                        <div class="poster">
                            <a title="${cur_result['show_name']}" href="${sbRoot}/home/displayShow?show=${cur_result['showid']}"><img alt="" src="${sbRoot}/showPoster/?show=${cur_result['showid']}&amp;which=poster_thumb" /></a>
                        </div>
                        <div class="text">
                            <span class="airtime">
                                ${airtime} on ${cur_result["network"]}
                            </span>
                            <span class="episode-title" title="${cur_result['name']}">
                                ${'S%02iE%02i' % (int(cur_result['season']), int(cur_result['episode']))} - ${cur_result['name']}
                            </span>
                        </div>
                    </td> <!-- end ${cur_result['show_name']} -->
                </tr>
            % endif

        % endfor
        % if not day_has_show:
            <tr><td class="calendarShow"><span class="show-status">No shows for this day</span></td></tr>
        % endif
        </tbody>
        </table>
    % endfor

<!-- end calender view //-->
</div>
% endif

<div class="clearfix"></div>
</%block>
