<%inherit file="/layouts/main.mako"/>
<%!
    import datetime
    import urllib
    import sickbeard
    from sickbeard import subtitles, sbdatetime, network_timezones
    import sickbeard.helpers

    from sickbeard.common import SKIPPED, WANTED, UNAIRED, ARCHIVED, IGNORED, FAILED, DOWNLOADED
    from sickbeard.common import Quality, qualityPresets, statusStrings, Overview
    from sickbeard.helpers import anon_url
    from sickrage.helper.common import pretty_file_size
%>

<%block name="scripts">
    <script type="text/javascript" src="${srRoot}/js/lib/jquery.bookmarkscroll.js?${sbPID}"></script>
    <script type="text/javascript" src="${srRoot}/js/plotTooltip.js?${sbPID}"></script>
    <script type="text/javascript" src="${srRoot}/js/sceneExceptionsTooltip.js?${sbPID}"></script>
    <script type="text/javascript" src="${srRoot}/js/ratingTooltip.js?${sbPID}"></script>
    <script type="text/javascript" src="${srRoot}/js/ajaxEpSearch.js?${sbPID}"></script>
    <script type="text/javascript" src="${srRoot}/js/ajaxEpSubtitles.js?${sbPID}"></script>
</%block>

<%block name="content">
    <%namespace file="/inc_defs.mako" import="renderQualityPill"/>
    <div class="show-header row">
        <div class="col-md-12">

            <div class="row">
                <div class="col-md-12" style="margin: 5px 0;">
                    <input type="hidden" id="srRoot" value="${srRoot}" />
                    <div class="form-inline">
                        ${_('Change Show')}:
                        <div class="navShow"><img id="prevShow" src="${srRoot}/images/prev.png" alt="&lt;&lt;" title="${_('Prev Show')}" /></div>
                        <select id="pickShow" class="form-control input-sm input350" title="Change Show">
                            % for curShowList in sortedShowLists:
                                <% curShowType = curShowList[0] %>
                                <% curShowList = curShowList[1] %>

                                % if len(sortedShowLists) > 1:
                                    <optgroup label="${curShowType}">
                                % endif
                                % for curShow in curShowList:
                                    <option value="${curShow.indexerid}" ${('', 'selected="selected"')[curShow == show]}>${curShow.name}</option>
                                % endfor
                                % if len(sortedShowLists) > 1:
                                    </optgroup>
                                % endif
                            % endfor
                        </select>
                        <div class="navShow"><img id="nextShow" src="${srRoot}/images/next.png" alt="&gt;&gt;" title="${_('Next Show')}" /></div>
                    </div>
                </div>
            </div>

            <div class="row">
                <div class="col-lg-12 col-md-12 col-sm-12 col-xs-12" id="showtitle" data-showname="${show.name}">
                    <h1 class="title" id="scene_exception_${show.indexerid}">${show.name}</h1>
                    % if seasonResults:
                        ##There is a special/season_0?##
                        % if int(seasonResults[-1]["season"]) == 0:
                            <% season_special = 1 %>
                        % else:
                            <% season_special = 0 %>
                        % endif
                        % if not sickbeard.DISPLAY_SHOW_SPECIALS and season_special:
                            <% lastSeason = seasonResults.pop(-1) %>
                        % endif

                        <span class="h2footer displayspecials pull-right">
                            % if season_special:
                                ${_('Display Specials')}:
                                <a class="inner" href="${srRoot}/toggleDisplayShowSpecials/?show=${show.indexerid}">
                                    ${(_('Show'), _('Hide'))[bool(sickbeard.DISPLAY_SHOW_SPECIALS)]}
                                </a>
                            % endif
                        </span>

                        <div class="h2footer pull-right">
                            <span>
                                % if (len(seasonResults) > 14):
                                    <select id="seasonJump" class="form-control input-sm" style="position: relative; top: -4px;" title="Season">
                                        <option value="jump">${_('Jump to Season')}</option>
                                        % for seasonNum in seasonResults:
                                            <option value="#season-${seasonNum["season"]}" data-season="${seasonNum["season"]}">${(_('Specials'), _('Season') + ' ' + str(seasonNum["season"]))[int(seasonNum["season"]) > 0]}</option>
                                        % endfor
                                    </select>
                                % else:
                                    ${_('Season')}:
                                    % for seasonNum in seasonResults:
                                        % if int(seasonNum["season"]) == 0:
                                            <a href="#season-${seasonNum["season"]}">${_('Specials')}</a>
                                        % else:
                                            <a href="#season-${seasonNum["season"]}">${str(seasonNum["season"])}</a>
                                        % endif
                                        % if seasonNum != seasonResults[-1]:
                                            <span class="separator">|</span>
                                        % endif
                                    % endfor
                                % endif
                            </span>
                        </div>
                    % endif
                </div>
            </div>

            <!-- Alert -->
            % if show_message:
                <div class="row">
                    <div class="col-md-12">
                        <div class="alert alert-info">
                            ${show_message}
                        </div>
                    </div>
                </div>
            % endif

            <!-- Header -->
            <div class="row">
                <div class="col-lg-3 col-md-3 col-sm-3 col-xs-12">
                    <img src="${srRoot}/showPoster/?show=${show.indexerid}&amp;which=poster_thumb"
                         class="pull-md-left pull-lg-left tvshowImg img-responsive" alt="${_('Poster for')} ${show.name}"
                         onclick="location.href='${srRoot}/showPoster/?show=${show.indexerid}&amp;which=poster'"/>
                </div>
                <div class="col-lg-9 col-md-9 col-sm-9 col-xs-12">
                    <div class="row">
                        <div class="col-md-12" id="showinfo">
                            <div class="row">
                                <div class="pull-right col-lg-3 col-md-3 hidden-sm hidden-xs">
                                    <img src="${srRoot}/showPoster/?show=${show.indexerid}&amp;which=banner" style="max-height:50px;border:1px solid black;" class="pull-right">
                                </div>
                                <div class="pull-left col-lg-9 col-md-9 col-sm-12 col-xs-12">
                                    % if 'rating' in show.imdb_info:
                                    <% rating_tip = str(show.imdb_info['rating']) + " / 10" + _('Stars') + "<br>" + str(show.imdb_info['votes']) +  _('Votes') %>
                                        <span class="imdbstars" qtip-content="${rating_tip}">${show.imdb_info['rating']}</span>
                                    % endif

                                    <% _show = show %>
                                    % if not show.imdbid:
                                        <span>(${show.startyear}) - ${show.runtime} ${_('minutes')} - </span>
                                    % else:
                                        % if 'country_codes' in show.imdb_info:
                                            % for country in show.imdb_info['country_codes'].split('|'):
                                                <img src="${srRoot}/images/blank.png" class="country-flag flag-${country}" width="16" height="11" style="margin-left: 3px; vertical-align:middle;" />
                                            % endfor
                                        % endif
                                        <span>
                                            % if show.imdb_info.get('year'):
                                                (${show.imdb_info['year']}) -
                                            % endif
                                            ${show.imdb_info['runtimes']} ${_('minutes')}</span>

                                        <a href="${anon_url('http://www.imdb.com/title/', _show.imdbid)}" rel="noreferrer" onclick="window.open(this.href, '_blank'); return false;" title="http://www.imdb.com/title/${show.imdbid}"><img alt="[imdb]" height="16" width="16" src="${srRoot}/images/imdb.png" style="margin-top: -1px; vertical-align:middle;"/></a>
                                    % endif
                                    <a href="${anon_url(sickbeard.indexerApi(_show.indexer).config['show_url'], _show.indexerid)}" onclick="window.open(this.href, '_blank'); return false;" title="${sickbeard.indexerApi(show.indexer).config["show_url"] + str(show.indexerid)}"><img alt="${sickbeard.indexerApi(show.indexer).name}" height="16" width="16" src="${srRoot}/images/${sickbeard.indexerApi(show.indexer).config["icon"]}" style="margin-top: -1px; vertical-align:middle;"/></a>
                                    % if xem_numbering or xem_absolute_numbering:
                                        <a href="${anon_url('http://thexem.de/search?q=', _show.name)}" rel="noreferrer" onclick="window.open(this.href, '_blank'); return false;" title="http://thexem.de/search?q-${show.name}"><img alt="[xem]" height="16" width="16" src="${srRoot}/images/xem.png" style="margin-top: -1px; vertical-align:middle;"/></a>
                                    % endif
                                    <a href="${anon_url('https://fanart.tv/series/', _show.indexerid)}" rel="noreferrer" onclick="window.open(this.href, '_blank'); return false;" title="https://fanart.tv/series/${show.name}"><img alt="[fanart.tv]" height="16" width="16" src="${srRoot}/images/fanart.tv.png" style="margin-top: -1px; vertical-align:middle;"/></a>

                                </div>
                                <div class="pull-left col-lg-9 col-md-9 col-sm-12 col-xs-12">
                                    <ul class="tags">
                                        % if show.genre and not show.imdb_info.get('genres'):
                                            % for genre in show.genre[1:-1].split('|'):
                                                <a href="${anon_url('http://trakt.tv/shows/popular/?genres=', genre.lower())}" target="_blank" title="${_('View other popular {genre} shows on trakt.tv.').format(genre=genre)}"><li>${_('genre')}</li></a>
                                            % endfor
                                        % elif show.imdb_info.get('genres'):
                                            % for imdbgenre in show.imdb_info['genres'].replace('Sci-Fi','Science-Fiction').split('|'):
                                                <a href="${anon_url('http://www.imdb.com/search/title?count=100&title_type=tv_series&genres=', imdbgenre.lower())}" target="_blank" title="${_('View other popular {imdbgenre} shows on IMDB.').format(imdbgenre=imdbgenre)}"><li>${imdbgenre}</li></a>
                                            % endfor
                                        % endif
                                    </ul>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-12">
                            <div id="summary">
                                <div class="col-lg-8 col-md-8 col-sm-8 col-xs-12">
                                    <table class="summaryTable pull-left">
                                        <% anyQualities, bestQualities = Quality.splitQuality(int(show.quality)) %>
                                    <tr>
                                        <td class="showLegend">${_('Quality')}: </td>
                                    <td>
                                        % if show.quality in qualityPresets:
                                            ${renderQualityPill(show.quality)}
                                        % else:
                                            % if anyQualities:
                                                <i>${_('Allowed')}:</i> ${", ".join([capture(renderQualityPill, x) for x in sorted(anyQualities)])}${("", "<br>")[bool(bestQualities)]}
                                            % endif
                                            % if bestQualities:
                                                <i>${_('Preferred')}:</i> ${", ".join([capture(renderQualityPill, x) for x in sorted(bestQualities)])}
                                            % endif
                                        % endif

                                        % if show.network and show.airs:
                                            <tr>
                                                <td class="showLegend">${_('Originally Airs')}: </td>
                                                <td>${show.airs} ${("<font color='#FF0000'><b>(invalid Timeformat)</b></font> ", "")[network_timezones.test_timeformat(show.airs)]} on ${show.network}</td>
                                            </tr>
                                        % elif show.network:
                                            <tr><td class="showLegend">${_('Originally Airs')}: </td>
                                                <td>${show.network}</td></tr>
                                        % elif show.airs:
                                            <tr>
                                                <td class="showLegend">${_('Originally Airs')}: </td>
                                                <td>${show.airs} ${("<font color='#FF0000'><b>(invalid Timeformat)</b></font>", "")[network_timezones.test_timeformat(show.airs)]}</td>
                                            </tr>
                                        % endif
                                        <tr>
                                            <td class="showLegend">${_('Show Status')}: </td>
                                            <td>${_(show.status)}</td>
                                        </tr>
                                        <tr>
                                            <td class="showLegend">${_('Default EP Status')}: </td>
                                            <td>${statusStrings[show.default_ep_status]}</td>
                                        </tr>
                                        % if showLoc[1]:
                                            <tr>
                                                <td class="showLegend">${_('Location')}: </td>
                                                <td>${showLoc[0]}</td>
                                            </tr>
                                        % else:
                                            <tr>
                                                <td class="showLegend"><span style="color: red;">${_('Location')}: </span></td>
                                                <td><span style="color: red;">${showLoc[0]}</span> (${_('Missing')})</td>
                                            </tr>
                                        % endif
                                        <tr>
                                            <td class="showLegend">${_('Scene Name')}:</td>
                                            <td>${(show.name, " | ".join(show.exceptions))[show.exceptions != 0]}</td>
                                        </tr>

                                        % if show.rls_require_words:
                                            <tr>
                                                <td class="showLegend">${_('Required Words')}: </td>
                                                <td>${show.rls_require_words}</td>
                                            </tr>
                                        % endif
                                        % if show.rls_ignore_words:
                                            <tr>
                                                <td class="showLegend">${_('Ignored Words')}: </td>
                                                <td>${show.rls_ignore_words}</td>
                                            </tr>
                                        % endif
                                        % if bwl and bwl.whitelist:
                                            <tr>
                                                <td class="showLegend">Wanted Group${("", "s")[len(bwl.whitelist) > 1]}:</td>
                                                <td>${', '.join(bwl.whitelist)}</td>
                                            </tr>
                                        % endif
                                        % if bwl and bwl.blacklist:
                                            <tr>
                                                <td class="showLegend">Unwanted Group${("", "s")[len(bwl.blacklist) > 1]}:</td>
                                                <td>${', '.join(bwl.blacklist)}</td>
                                            </tr>
                                        % endif
                                        <tr>
                                            <td class="showLegend">${_('Size')}:</td>
                                            <td>${pretty_file_size(sickbeard.helpers.get_size(showLoc[0]))}</td>
                                        </tr>
                                    </table>
                                </div>
                                <div class="col-lg-4 col-md-4 col-sm-4 col-xs-12 pull-xs-left">
                                    <table class="pull-xs-left pull-md-right pull-sm-right pull-lg-right">
                                        <% info_flag = subtitles.code_from_code(show.lang) if show.lang else '' %>
                                        <tr>
                                            <td class="showLegend">${_('Info Language')}:</td>
                                            <td><img src="${srRoot}/images/subtitles/flags/${info_flag}.png" width="16" height="11" alt="${show.lang}" title="${show.lang}" onError="this.onerror=null;this.src='${srRoot}/images/flags/unknown.png';"/></td>
                                        </tr>
                                        % if sickbeard.USE_SUBTITLES:
                                            <tr>
                                                <td class="showLegend">${_('Subtitles')}: </td>
                                                <td><img src="${srRoot}/images/${("no16.png", "yes16.png")[bool(show.subtitles)]}" alt="${("N", "Y")[bool(show.subtitles)]}" width="16" height="16" /></td>
                                            </tr>
                                        % endif
                                        <tr>
                                            <td class="showLegend">${_('Season Folders')}: </td>
                                            <td><img src="${srRoot}/images/${("no16.png", "yes16.png")[bool(not show.flatten_folders or sickbeard.NAMING_FORCE_FOLDERS)]}" alt=="${("N", "Y")[bool(not show.flatten_folders or sickbeard.NAMING_FORCE_FOLDERS)]}" width="16" height="16" /></td>
                                        </tr>
                                        <tr>
                                            <td class="showLegend">${_('Paused')}: </td>
                                            <td><img src="${srRoot}/images/${("no16.png", "yes16.png")[bool(show.paused)]}" alt="${("N", "Y")[bool(show.paused)]}" width="16" height="16" /></td>
                                        </tr>
                                        <tr>
                                            <td class="showLegend">${_('Air-by-Date')}: </td>
                                            <td><img src="${srRoot}/images/${("no16.png", "yes16.png")[bool(show.air_by_date)]}" alt="${("N", "Y")[bool(show.air_by_date)]}" width="16" height="16" /></td>
                                        </tr>
                                        <tr>
                                            <td class="showLegend">${_('Sports')}: </td>
                                            <td><img src="${srRoot}/images/${("no16.png", "yes16.png")[bool(show.is_sports)]}" alt="${("N", "Y")[bool(show.is_sports)]}" width="16" height="16" /></td>
                                        </tr>
                                        <tr>
                                            <td class="showLegend">${_('Anime')}: </td>
                                            <td><img src="${srRoot}/images/${("no16.png", "yes16.png")[bool(show.is_anime)]}" alt="${("N", "Y")[bool(show.is_anime)]}" width="16" height="16" /></td>
                                        </tr>
                                        <tr>
                                            <td class="showLegend">${_('DVD Order')}: </td>
                                            <td><img src="${srRoot}/images/${("no16.png", "yes16.png")[bool(show.dvdorder)]}" alt="${("N", "Y")[bool(show.dvdorder)]}" width="16" height="16" /></td>
                                        </tr>
                                        <tr>
                                            <td class="showLegend">${_('Scene Numbering')}: </td>
                                            <td><img src="${srRoot}/images/${("no16.png", "yes16.png")[bool(show.scene)]}" alt="${("N", "Y")[bool(show.scene)]}" width="16" height="16" /></td>
                                        </tr>
                                    </table>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            <!-- Labels -->
            <div class="row">
                <div class="col-lg-8 col-md-8 col-sm-12 col-xs-12 pull-right">
                    <div class="pull-right" id="checkboxControls">
                        <div style="padding-bottom: 5px;">
                            <% total_snatched = epCounts[Overview.SNATCHED] + epCounts[Overview.SNATCHED_PROPER] + epCounts[Overview.SNATCHED_BEST] %>
                            <label class="pull-right" for="wanted"><span class="wanted"><input type="checkbox" id="wanted" checked="checked" /> ${_('Wanted')}: <b>${epCounts[Overview.WANTED]}</b></span></label>
                            <label class="pull-right" for="qual"><span class="qual"><input type="checkbox" id="qual" checked="checked" /> ${_('Allowed')}: <b>${epCounts[Overview.QUAL]}</b></span></label>
                            <label class="pull-right" for="good"><span class="good"><input type="checkbox" id="good" checked="checked" /> ${_('Preferred')}: <b>${epCounts[Overview.GOOD]}</b></span></label>
                            <label class="pull-right" for="skipped"><span class="skipped"><input type="checkbox" id="skipped" checked="checked" /> ${_('Skipped')}: <b>${epCounts[Overview.SKIPPED]}</b></span></label>
                            <label class="pull-right" for="snatched"><span class="snatched"><input type="checkbox" id="snatched" checked="checked" /> ${_('Snatched')}: <b>${total_snatched}</b></span></label>
                        </div>
                        <div class="clearfix"></div>

                        <div class="pull-right" >
                            <button class="btn btn-xs seriesCheck">${_('Select Filtered Episodes')}</button>
                            <button class="btn btn-xs clearAll">${_('Clear All')}</button>
                        </div>
                    </div>
                </div>
            </div>
            <!-- Episode selector -->
            <div class="row">
                <div class="col-lg-12 col-md-12 col-sm-12 col-xs-12" style="padding-bottom: 5px; padding-top: 5px;">
                    ${_('Change selected episodes to')}:<br>
                    <select id="statusSelect" class="form-control form-control-inline input-sm" title="Change Status">
                        <% availableStatus = [WANTED, SKIPPED, IGNORED, FAILED] %>
                        % if not sickbeard.USE_FAILED_DOWNLOADS:
                            <% availableStatus.remove(FAILED) %>
                        % endif
                        % for curStatus in availableStatus + Quality.DOWNLOADED + Quality.ARCHIVED:
                            % if curStatus not in [DOWNLOADED, ARCHIVED]:
                                <option value="${curStatus}">${statusStrings[curStatus]}</option>
                            % endif
                        % endfor
                    </select>
                    <input type="hidden" id="showID" value="${show.indexerid}" />
                    <input type="hidden" id="indexer" value="${show.indexer}" />
                    <input class="btn btn-inline" type="button" id="changeStatus" value="Go" />
                    <button id="popover" type="button" class="btn btn-xs pull-right">${_('Select Columns')} <b class="caret"></b></button>
                </div>
            </div>
        </div>
    </div>
    <div class="row">
        <div class="col-md-12">
            <% curSeason = -1 %>
            <% odd = 0 %>
            % for epResult in sql_results:
                <%
                    epStr = str(epResult["season"]) + "x" + str(epResult["episode"])
                    if not epStr in epCats:
                        continue

                    if not sickbeard.DISPLAY_SHOW_SPECIALS and int(epResult["season"]) == 0:
                        continue

                    scene = False
                    scene_anime = False
                    if not show.air_by_date and not show.is_sports and not show.is_anime and show.is_scene:
                        scene = True
                    elif not show.air_by_date and not show.is_sports and show.is_anime and show.is_scene:
                        scene_anime = True

                    (dfltSeas, dfltEpis, dfltAbsolute) = (0, 0, 0)
                    if (epResult["season"], epResult["episode"]) in xem_numbering:
                        (dfltSeas, dfltEpis) = xem_numbering[(epResult["season"], epResult["episode"])]

                    if epResult["absolute_number"] in xem_absolute_numbering:
                        dfltAbsolute = xem_absolute_numbering[epResult["absolute_number"]]

                    if epResult["absolute_number"] in scene_absolute_numbering:
                        scAbsolute = scene_absolute_numbering[epResult["absolute_number"]]
                        dfltAbsNumbering = False
                    else:
                        scAbsolute = dfltAbsolute
                        dfltAbsNumbering = True

                    if (epResult["season"], epResult["episode"]) in scene_numbering:
                        (scSeas, scEpis) = scene_numbering[(epResult["season"], epResult["episode"])]
                        dfltEpNumbering = False
                    else:
                        (scSeas, scEpis) = (dfltSeas, dfltEpis)
                        dfltEpNumbering = True

                    epLoc = epResult["location"]
                    if epLoc and show._location and epLoc.lower().startswith(show._location.lower()):
                        epLoc = epLoc[len(show._location)+1:]
                %>
                % if int(epResult["season"]) != curSeason:
                    % if epResult["season"] != sql_results[0]["season"]:
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                    % endif
                    <div class="row">
                        <div class="col-md-12">
                            <br/>
                            <br/>
                            <h3 style="display: inline;"><a name="season-${epResult["season"]}"></a>${(_("Specials"), _("Season") + ' ' + str(epResult["season"]))[int(epResult["season"]) > 0]}</h3>
                            % if sickbeard.DISPLAY_ALL_SEASONS is False:
                                <button id="showseason-${epResult['season']}" type="button" class="btn btn-xs pull-right" data-toggle="collapse" data-target="#collapseSeason-${epResult['season']}">${_('Show Episodes')}</button>
                            % endif
                        </div>
                    </div>
                    <div class="row">
                        <div class="col-md-12">
                            <div class="horizontal-scroll">
                                <table id="${("showTable", "animeTable")[bool(show.is_anime)]}" class="displayShowTable display_show" cellspacing="0" border="0" cellpadding="0">
                                    <thead>
                                        <tr class="seasoncols" style="display:none;">
                                            <th data-sorter="false" data-priority="critical" class="col-checkbox"><input type="checkbox" class="seasonCheck"/></th>
                                            <th data-sorter="false" class="col-metadata">${_('NFO')}</th>
                                            <th data-sorter="false" class="col-metadata">${_('TBN')}</th>
                                            <th data-sorter="false" class="col-ep">${_('Episode')}</th>
                                            <th data-sorter="false" ${("class=\"col-ep columnSelector-false\"", "class=\"col-ep\"")[bool(show.is_anime)]}>${_('Absolute')}</th>
                                            <th data-sorter="false" ${("class=\"col-ep columnSelector-false\"", "class=\"col-ep\"")[bool(scene)]}>${_('Scene')}</th>
                                            <th data-sorter="false" ${("class=\"col-ep columnSelector-false\"", "class=\"col-ep\"")[bool(scene_anime)]}>${_('Scene Absolute')}</th>
                                            <th data-sorter="false" class="col-name">${_('Name')}</th>
                                            <th data-sorter="false" class="col-name columnSelector-false">${_('File Name')}</th>
                                            <th data-sorter="false" class="col-ep columnSelector-false">${_('Size')}</th>
                                            <th data-sorter="false" class="col-airdate">${_('Airdate')}</th>
                                            <th data-sorter="false" ${("class=\"col-ep columnSelector-false\"", "class=\"col-ep\"")[bool(sickbeard.DOWNLOAD_URL)]}>${_('Download')}</th>
                                            <th data-sorter="false" ${("class=\"col-ep columnSelector-false\"", "class=\"col-ep\"")[bool(sickbeard.USE_SUBTITLES)]}>${_('Subtitles')}</th>
                                            <th data-sorter="false" class="col-status">${_('Status')}</th>
                                            <th data-sorter="false" class="col-search">${_('Search')}</th>
                                        </tr>
                                    </thead>

                                % if curSeason == -1:
                                    <tbody class="tablesorter-no-sort">
                                        <tr id="season-${epResult["season"]}-cols" class="seasoncols">
                                            <th class="col-checkbox"><input type="checkbox" class="seasonCheck" id="${epResult["season"]}" /></th>
                                            <th class="col-metadata">${_('NFO')}</th>
                                            <th class="col-metadata">${_('TBN')}</th>
                                            <th class="col-ep">${_('Episode')}</th>
                                            <th class="col-ep">${_('Absolute')}</th>
                                            <th class="col-ep">${_('Scene')}</th>
                                            <th class="col-ep">${_('Scene Absolute')}</th>
                                            <th class="col-name">${_('Name')}</th>
                                            <th class="col-name">${_('File Name')}</th>
                                            <th class="col-ep">${_('Size')}</th>
                                            <th class="col-airdate">${_('Airdate')}</th>
                                            <th class="col-ep">${_('Download')}</th>
                                            <th class="col-ep">${_('Subtitles')}</th>
                                            <th class="col-status">${_('Status')}</th>
                                            <th class="col-search">${_('Search')}</th>
                                        </tr>
                                    </tbody>
                                % else:
                                    <tbody class="tablesorter-no-sort">
                                        <tr id="season-${epResult["season"]}-cols" class="seasoncols">
                                            <th class="col-checkbox"><input type="checkbox" class="seasonCheck" id="${epResult["season"]}" /></th>
                                            <th class="col-metadata">${_('NFO')}</th>
                                            <th class="col-metadata">${_('TBN')}</th>
                                            <th class="col-ep">${_('Episode')}</th>
                                            <th class="col-ep">${_('Absolute')}</th>
                                            <th class="col-ep">${_('Scene')}</th>
                                            <th class="col-ep">${_('Scene Absolute')}</th>
                                            <th class="col-name">${_('Name')}</th>
                                            <th class="col-name">${_('File Name')}</th>
                                            <th class="col-ep">${_('Size')}</th>
                                            <th class="col-airdate">${_('Airdate')}</th>
                                            <th class="col-ep">${_('Download')}</th>
                                            <th class="col-ep">${_('Subtitles')}</th>
                                            <th class="col-status">${_('Status')}</th>
                                            <th class="col-search">${_('Search')}</th>
                                        </tr>
                                    </tbody>
                                % endif

                                % if sickbeard.DISPLAY_ALL_SEASONS is False:
                                    <tbody class="toggle collapse${("", " in")[curSeason == -1]}" id="collapseSeason-${epResult['season']}">
                                % else:
                                    <tbody>
                                % endif
                                <% curSeason = int(epResult["season"]) %>
                % endif
                                    <tr class="${Overview.overviewStrings[epCats[epStr]]} season-${curSeason} seasonstyle" id="${'S' + str(epResult["season"]) + 'E' + str(epResult["episode"])}">
                                        <td class="col-checkbox">
                                            % if int(epResult["status"]) != UNAIRED:
                                                <input type="checkbox" class="epCheck" id="${str(epResult["season"])+'x'+str(epResult["episode"])}" name="${str(epResult["season"]) +"x"+str(epResult["episode"])}" />
                                            % endif
                                        </td>
                                        <td align="center"><img src="${srRoot}/images/${("nfo-no.gif", "nfo.gif")[epResult["hasnfo"]]}" alt="${("N", "Y")[epResult["hasnfo"]]}" width="23" height="11" /></td>
                                        <td align="center"><img src="${srRoot}/images/${("tbn-no.gif", "tbn.gif")[epResult["hastbn"]]}" alt="${("N", "Y")[epResult["hastbn"]]}" width="23" height="11" /></td>
                                        <td align="center">
                                            <%
                                                text = str(epResult['episode'])
                                                if epLoc != '' and epLoc is not None:
                                                    text = '<span title="' + epLoc + '" class="addQTip">' + text + "</span>"
                                            %>
                                        ${text}
                                        </td>
                                        <td align="center">${epResult["absolute_number"]}</td>
                                        <td align="center">
                                            <input type="text" placeholder="${str(dfltSeas) + 'x' + str(dfltEpis)}" size="6" maxlength="8"
                                                   class="sceneSeasonXEpisode form-control input-scene" data-for-season="${epResult["season"]}" data-for-episode="${epResult["episode"]}"
                                                   id="sceneSeasonXEpisode_${show.indexerid}_${str(epResult["season"])}_${str(epResult["episode"])}"
                                                   title="${_('Change the value here if scene numbering differs from the indexer episode numbering')}"
                                                % if dfltEpNumbering:
                                                   value=""
                                                % else:
                                                   value="${str(scSeas)}x${str(scEpis)}"
                                                % endif
                                                   style="padding: 0; text-align: center; max-width: 60px;" autocapitalize="off" />
                                        </td>
                                        <td align="center">
                                            <input type="text" placeholder="${str(dfltAbsolute)}" size="6" maxlength="8"
                                                   class="sceneAbsolute form-control input-scene" data-for-absolute="${epResult["absolute_number"]}"
                                                   id="sceneAbsolute_${show.indexerid}${"_"+str(epResult["absolute_number"])}"
                                                   title="${_('Change the value here if scene absolute numbering differs from the indexer absolute numbering')}"
                                                % if dfltAbsNumbering:
                                                   value=""
                                                % else:
                                                   value="${str(scAbsolute)}"
                                                % endif
                                                   style="padding: 0; text-align: center; max-width: 60px;" autocapitalize="off" />
                                        </td>
                                        <td class="col-name">
                                            % if epResult["description"] != "" and epResult["description"] is not None:
                                                <img src="${srRoot}/images/info32.png" width="16" height="16" class="plotInfo" alt="" id="plot_info_${str(show.indexerid)}_${str(epResult["season"])}_${str(epResult["episode"])}" />
                                            % else:
                                                <img src="${srRoot}/images/info32.png" width="16" height="16" class="plotInfoNone" alt="" />
                                            % endif
                                            ${epResult["name"]}
                                        </td>
                                        <td class="col-name">${epLoc}</td>
                                        <td class="col-ep">
                                            % if epResult["file_size"]:
                                            ${pretty_file_size(epResult["file_size"])}
                                            % endif
                                        </td>
                                        <td class="col-airdate">
                                            % if int(epResult['airdate']) != 1:
                                            ## Lets do this exactly like ComingEpisodes and History
                                            ## Avoid issues with dateutil's _isdst on Windows but still provide air dates
                                        <% airDate = datetime.datetime.fromordinal(epResult['airdate']) %>
                                            % if airDate.year >= 1970 or show.network:
                                                <% airDate = sbdatetime.sbdatetime.convert_to_setting(network_timezones.parse_date_time(epResult['airdate'], show.airs, show.network)) %>
                                            % endif
                                                <time datetime="${airDate.isoformat('T')}" class="date">${sbdatetime.sbdatetime.sbfdatetime(airDate)}</time>
                                            % else:
                                                Never
                                            % endif
                                        </td>
                                        <td>
                                            % if sickbeard.DOWNLOAD_URL and epResult['location']:
                                            <%
                                                filename = epResult['location']
                                                for rootDir in sickbeard.ROOT_DIRS.split('|'):
                                                    if rootDir.startswith('/'):
                                                        filename = filename.replace(rootDir, "")
                                                    filename = sickbeard.DOWNLOAD_URL + urllib.quote(filename.encode('utf8'))
                                            %>
                                                <center><a href="${filename}">${_('Download')}</a></center>
                                            % endif
                                        </td>
                                        <td class="col-subtitles" align="center">
                                            % for flag in (epResult["subtitles"] or '').split(','):
                                                % if flag.strip():
                                                    <img src="${srRoot}/images/subtitles/flags/${flag}.png" width="16" height="11" alt="${subtitles.name_from_code(flag)}" onError="this.onerror=null;this.src='${srRoot}/images/flags/unknown.png';" />
                                                % endif
                                            % endfor
                                        </td>
                                        <% curStatus, curQuality = Quality.splitCompositeStatus(int(epResult["status"])) %>
                                        % if curQuality != Quality.NONE:
                                            <td class="col-status">${statusStrings[curStatus]} ${renderQualityPill(curQuality)}</td>
                                        % else:
                                            <td class="col-status">${statusStrings[curStatus]}</td>
                                        % endif
                                        <td class="col-search">
                                            % if int(epResult["season"]) != 0:
                                                % if (int(epResult["status"]) in Quality.SNATCHED + Quality.SNATCHED_PROPER + Quality.SNATCHED_BEST + Quality.DOWNLOADED ) and sickbeard.USE_FAILED_DOWNLOADS:
                                                    <a class="epRetry" id="${str(show.indexerid)}x${str(epResult["season"])}x${str(epResult["episode"])}" name="${str(show.indexerid)}x${str(epResult["season"])}x${str(epResult["episode"])}" href="retryEpisode?show=${show.indexerid}&amp;season=${epResult["season"]}&amp;episode=${epResult["episode"]}"><img src="${srRoot}/images/search16.png" height="16" alt="retry" title="Retry Download" /></a>
                                                % else:
                                                    <a class="epSearch" id="${str(show.indexerid)}x${str(epResult["season"])}x${str(epResult["episode"])}" name="${str(show.indexerid)}x${str(epResult["season"])}x${str(epResult["episode"])}" href="searchEpisode?show=${show.indexerid}&amp;season=${epResult["season"]}&amp;episode=${epResult["episode"]}"><img src="${srRoot}/images/search16.png" width="16" height="16" alt="search" title="Manual Search" /></a>
                                                % endif
                                            % endif
                                            % if int(epResult["status"]) not in Quality.SNATCHED + Quality.SNATCHED_PROPER and sickbeard.USE_SUBTITLES and show.subtitles and epResult["location"] and subtitles.needs_subtitles(epResult['subtitles']):
                                                <a class="epSubtitlesSearch" href="searchEpisodeSubtitles?show=${show.indexerid}&amp;season=${epResult["season"]}&amp;episode=${epResult["episode"]}"><img src="${srRoot}/images/closed_captioning.png" height="16" alt="search subtitles" title="Search Subtitles" /></a>
                                            % endif
                                        </td>
                                    </tr>
            % endfor
                    </tbody>
                </table>
            </div>
        </div>
    </div>

    <!-- Modals -->
    <div id="manualSearchModalFailed" class="modal fade">
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header">
                    <button type="button" class="close" data-dismiss="modal" aria-hidden="true">&times;</button>
                    <h4 class="modal-title">${_('Manual Search')}</h4>
                </div>
                <div class="modal-body">
                    <p>${_('Do you want to mark this episode as failed?')}</p>
                    <p class="text-warning"><small>${_('The episode release name will be added to the failed history, preventing it to be downloaded again.')}</small></p>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-danger" data-dismiss="modal">No</button>
                    <button type="button" class="btn btn-success" data-dismiss="modal">Yes</button>
                </div>
            </div>
        </div>
    </div>

    <div id="manualSearchModalQuality" class="modal fade">
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header">
                    <button type="button" class="close" data-dismiss="modal" aria-hidden="true">&times;</button>
                    <h4 class="modal-title">${_('Manual Search')}</h4>
                </div>
                <div class="modal-body">
                    <p>${_('Do you want to include the current episode quality in the search?')}</p>
                    <p class="text-warning"><small>${_('Choosing No will ignore any releases with the same episode quality as the one currently downloaded/snatched.')}</small></p>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-danger" data-dismiss="modal">No</button>
                    <button type="button" class="btn btn-success" data-dismiss="modal">Yes</button>
                </div>
            </div>
        </div>
    </div>
</%block>
