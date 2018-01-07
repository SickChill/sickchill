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
    <script type="text/javascript" src="${static_url('js/lib/jquery.bookmarkscroll.js')}"></script>
    <script type="text/javascript" src="${static_url('js/plotTooltip.js')}"></script>
    <script type="text/javascript" src="${static_url('js/sceneExceptionsTooltip.js')}"></script>
    <script type="text/javascript" src="${static_url('js/ratingTooltip.js')}"></script>
    <script type="text/javascript" src="${static_url('js/ajaxEpSearch.js')}"></script>
</%block>

<%block name="content">
    <%namespace file="/inc_defs.mako" import="renderQualityPill"/>
    <div class="show-header row">
        <div class="col-md-12">

            <div class="row">
                <div class="col-md-12" style="margin: 5px 0;">
                    <div class="form-inline">
                        <label for="pickShow">${_('Change Show')}:</label>
                        <div class="pick-show-group input350">
                            <div class="navShow">
                                <span id="prevShow" class="displayshow-icon-left" title="${_('Prev Show')}"></span>
                            </div>
                            <select id="pickShow" class="form-control input-sm" title="Change Show">
                                % for curShowList in sortedShowLists:
                                    % if len(sortedShowLists) > 1:
                                        <optgroup label="${curShowList[0]}">
                                    % endif
                                    % for curShow in curShowList[1]:
                                        <option value="${curShow.indexerid}" ${('', 'selected="selected"')[curShow == show]}>${curShow.name}</option>
                                    % endfor
                                    % if len(sortedShowLists) > 1:
                                        </optgroup>
                                    % endif
                                % endfor
                            </select>
                            <div class="navShow">
                                <span id="nextShow" class="displayshow-icon-right" title="${_('Next Show')}"></span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <div class="row">
                <div class="col-lg-12 col-md-12 col-sm-12 col-xs-12" id="showtitle" data-showname="${show.name}">
                    <h1 class="title" id="scene_exception_${show.indexerid}">${show.name}</h1>
                    % if seasonResults:
                        ##There is a special/season_0?##
                        <% season_special = (int(seasonResults[-1]["season"]) == 0) %>
                        % if not sickbeard.DISPLAY_SHOW_SPECIALS and season_special:
                            <% lastSeason = seasonResults.pop(-1) %>
                        % endif

                        <div class="h2footer pull-right">
                            <span>
                                % if (len(seasonResults) > 5):
                                    <select id="seasonJump" class="form-control input-sm" style="position: relative; top: -4px;" title="Season">
                                        <option value="jump">${_('Jump to Season')}</option>
                                        % for seasonNum in seasonResults:
                                            <option value="#season-${seasonNum["season"]}" data-season="${seasonNum["season"]}">${(_('Specials'), _('Season') + ' ' + str(seasonNum["season"]))[int(seasonNum["season"]) > 0]}</option>
                                        % endfor
                                    </select>
                                % else:
                                    <label>
                                        <span>${_('Season')}:</span>
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
                                    </label>
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
                <div class="col-md-12">
                    <div class="poster-container">
                        <img src="${srRoot}/showPoster/?show=${show.indexerid}&amp;which=poster_thumb"
                             class="tvshowImg" alt="${_('Poster for')} ${show.name}"
                             onclick="location.href='${srRoot}/showPoster/?show=${show.indexerid}&amp;which=poster'"/>
                    </div>
                    <div class="info-container">
                        <div class="row">
                            <div class="pull-right col-lg-4 col-md-4 hidden-sm hidden-xs">
                                <img src="${srRoot}/showPoster/?show=${show.indexerid}&amp;which=banner" style="max-height:50px;border:1px solid black;" class="pull-right">
                            </div>
                            <div class="pull-left col-lg-8 col-md-8 col-sm-12 col-xs-12">
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
                                        <img src="${static_url('images/blank.png')}" class="country-flag flag-${country}" width="16" height="11" style="margin-left: 3px; vertical-align:middle;" />
                                    % endfor
                                % endif
                                    <span>
                                % if show.imdb_info.get('year'):
                                    (${show.imdb_info['year']}) -
                                % endif
                                        ${show.imdb_info['runtimes']} ${_('minutes')}
                            </span>
                                    <a href="${anon_url('http://www.imdb.com/title/', _show.imdbid)}" rel="noreferrer" onclick="window.open(this.href, '_blank'); return false;" title="http://www.imdb.com/title/${show.imdbid}"><span class="displayshow-icon-imdb" /></a>
                                % endif
                                <a href="${anon_url(sickbeard.indexerApi(_show.indexer).config['show_url'], _show.indexerid)}" onclick="window.open(this.href, '_blank'); return false;" title="${sickbeard.indexerApi(show.indexer).config["show_url"] + str(show.indexerid)}"><img alt="${sickbeard.indexerApi(show.indexer).name}" src="${static_url('images/indexers/' + sickbeard.indexerApi(show.indexer).config["icon"])}" style="margin-top: -1px; vertical-align:middle;"/></a>
                                % if xem_numbering or xem_absolute_numbering:
                                    <a href="${anon_url('http://thexem.de/search?q=', _show.name)}" rel="noreferrer" onclick="window.open(this.href, '_blank'); return false;" title="http://thexem.de/search?q-${show.name}"><span alt="" class="displayshow-icon-xem" /></a>
                                % endif
                                <a href="${anon_url('https://fanart.tv/series/', _show.indexerid)}" rel="noreferrer" onclick="window.open(this.href, '_blank'); return false;" title="https://fanart.tv/series/${show.name}"><span class="displayshow-icon-fanart" /></a>
                            </div>
                            <div class="pull-left col-lg-8 col-md-8 col-sm-12 col-xs-12">
                                <ul class="tags">
                                    % if show.genre and not show.imdb_info.get('genres'):
                                        % for genre in show.genre[1:-1].split('|'):
                                            <a href="${anon_url('http://trakt.tv/shows/popular/?genres=', genre.lower())}" target="_blank" title="${_('View other popular {genre} shows on trakt.tv.').format(genre=_(genre))}"><li>${_(genre)}</li></a>
                                        % endfor
                                    % elif show.imdb_info.get('genres'):
                                        % for imdbgenre in show.imdb_info['genres'].replace('Sci-Fi','Science-Fiction').split('|'):
                                            <a href="${anon_url('http://www.imdb.com/search/title?count=100&title_type=tv_series&genres=', imdbgenre.lower())}" target="_blank" title="${_('View other popular {imdbgenre} shows on IMDB.').format(imdbgenre=_(imdbgenre))}"><li>${_(imdbgenre)}</li></a>
                                        % endfor
                                    % endif
                                </ul>
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
                                                <td><img src="${static_url('images/subtitles/flags/' + info_flag + '.png') }" width="16" height="11" alt="${show.lang}" title="${show.lang}" onError="this.onerror=null;this.src='${ static_url('images/flags/unknown.png')}';"/></td>
                                            </tr>
                                            % if sickbeard.USE_SUBTITLES:
                                                <tr>
                                                    <td class="showLegend">${_('Subtitles')}: </td>
                                                    <td><span class="displayshow-icon-${("disable", "enable")[bool(show.subtitles)]}" title=${("N", "Y")[bool(show.subtitles)]}></span></td>
                                                </tr>
                                            % endif
                                            <tr>
                                                <td class="showLegend">${_('Subtitles SR Metadata')}: </td>
                                                <td><span class="displayshow-icon-${("disable", "enable")[bool(show.subtitles_sr_metadata)]}" title=${("N", "Y")[bool(show.subtitles_sr_metadata)]}></span></td>
                                            </tr>
                                            <tr>
                                                <td class="showLegend">${_('Season Folders')}: </td>
                                                <td><span class="displayshow-icon-${("disable", "enable")[bool(show.season_folders or sickbeard.NAMING_FORCE_FOLDERS)]}" title=${("N", "Y")[bool(show.season_folders or sickbeard.NAMING_FORCE_FOLDERS)]}></span></td>
                                            </tr>
                                            <tr>
                                                <td class="showLegend">${_('Paused')}: </td>
                                                <td><span class="displayshow-icon-${("disable", "enable")[bool(show.paused)]}" title=${("N", "Y")[bool(show.paused)]}></span></td>
                                            </tr>
                                            <tr>
                                                <td class="showLegend">${_('Air-by-Date')}: </td>
                                                <td><span class="displayshow-icon-${("disable", "enable")[bool(show.air_by_date)]}" title=${("N", "Y")[bool(show.air_by_date)]}></span></td>
                                            </tr>
                                            <tr>
                                                <td class="showLegend">${_('Sports')}: </td>
                                                <td><span class="displayshow-icon-${("disable", "enable")[bool(show.is_sports)]}" title=${("N", "Y")[bool(show.is_sports)]}></span></td>
                                            </tr>
                                            <tr>
                                                <td class="showLegend">${_('Anime')}: </td>
                                                <td><span class="displayshow-icon-${("disable", "enable")[bool(show.is_anime)]}" title=${("N", "Y")[bool(show.is_anime)]}></span></td>
                                            </tr>
                                            <tr>
                                                <td class="showLegend">${_('DVD Order')}: </td>
                                                <td><span class="displayshow-icon-${("disable", "enable")[bool(show.dvdorder)]}" title=${("N", "Y")[bool(show.dvdorder)]}></span></td>
                                            </tr>
                                            <tr>
                                                <td class="showLegend">${_('Scene Numbering')}: </td>
                                                <td><span class="displayshow-icon-${("disable", "enable")[bool(show.scene)]}" title=${("N", "Y")[bool(show.scene)]}></span></td>
                                            </tr>
                                        </table>
                                    </div>
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
                    epStr = str(epResult[b"season"]) + "x" + str(epResult[b"episode"])
                    if not epStr in epCats:
                        continue

                    if not sickbeard.DISPLAY_SHOW_SPECIALS and int(epResult[b"season"]) == 0:
                        continue

                    scene = False
                    scene_anime = False
                    if not show.air_by_date and not show.is_sports and not show.is_anime and show.is_scene:
                        scene = True
                    elif not show.air_by_date and not show.is_sports and show.is_anime and show.is_scene:
                        scene_anime = True

                    (dfltSeas, dfltEpis, dfltAbsolute) = (0, 0, 0)
                    if (epResult[b"season"], epResult[b"episode"]) in xem_numbering:
                        (dfltSeas, dfltEpis) = xem_numbering[(epResult[b"season"], epResult[b"episode"])]

                    if epResult[b"absolute_number"] in xem_absolute_numbering:
                        dfltAbsolute = xem_absolute_numbering[epResult[b"absolute_number"]]

                    if epResult[b"absolute_number"] in scene_absolute_numbering:
                        scAbsolute = scene_absolute_numbering[epResult[b"absolute_number"]]
                        dfltAbsNumbering = False
                    else:
                        scAbsolute = dfltAbsolute
                        dfltAbsNumbering = True

                    if (epResult[b"season"], epResult[b"episode"]) in scene_numbering:
                        (scSeas, scEpis) = scene_numbering[(epResult[b"season"], epResult[b"episode"])]
                        dfltEpNumbering = False
                    else:
                        (scSeas, scEpis) = (dfltSeas, dfltEpis)
                        dfltEpNumbering = True

                    epLoc = epResult[b"location"]
                    if epLoc and show._location and epLoc.lower().startswith(show._location.lower()):
                        epLoc = epLoc[len(show._location)+1:]
                %>
                % if int(epResult[b"season"]) != curSeason:
                    % if epResult[b"season"] != sql_results[0][b"season"]:
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                    % endif
                    <div class="row">
                        <div class="col-md-12">
                            <br/>
                            <h3 style="display: inline;"><a name="season-${epResult[b"season"]}"></a>${(_("Specials"), _("Season") + ' ' + str(epResult[b"season"]))[int
                            (epResult[b"season"]) > 0]}</h3>
                            % if not sickbeard.DISPLAY_ALL_SEASONS:
                                % if curSeason == -1:
                                    <button id="showseason-${epResult[b'season']}" type="button" class="btn btn-xs pull-right" data-toggle="collapse" data-target="#collapseSeason-${epResult[b'season']}" aria-expanded="true">${_('Hide Episodes')}</button>
                                %else:
                                    <button id="showseason-${epResult[b'season']}" type="button" class="btn btn-xs pull-right" data-toggle="collapse" data-target="#collapseSeason-${epResult[b'season']}">${_('Show Episodes')}</button>
                                %endif
                            % endif
                        </div>
                    </div>
                    <div class="row">
                        <div class="col-md-12">
                            <div class="horizontal-scroll">
                                <table id="${("showTable", "animeTable")[bool(show.is_anime)]}" class="displayShowTable display_show" cellspacing="0" border="0" cellpadding="0">
                                    <thead>
                                        <tr class="seasoncols">
                                            <th data-sorter="false" data-priority="critical" class="col-checkbox">
                                                <input type="checkbox" class="seasonCheck" id="${epResult[b"season"]}" />
                                            </th>
                                            <th data-sorter="false" class="col-metadata">${_('NFO')}</th>
                                            <th data-sorter="false" class="col-metadata">${_('TBN')}</th>
                                            <th data-sorter="false" class="col-ep episode">${_('Episode')}</th>
                                            <th data-sorter="false" ${("class=\"col-ep columnSelector-false\"", "class=\"col-ep\"")[bool(show.is_anime)]}>${_('Absolute')}</th>
                                            <th data-sorter="false" ${("class=\"col-ep columnSelector-false\"", "class=\"col-ep\"")[bool(scene)]}>${_('Scene')}</th>
                                            <th data-sorter="false" ${("class=\"col-ep columnSelector-false\"", "class=\"col-ep\"")[bool(scene_anime)]}>${_('Scene Absolute')}</th>
                                            <th data-sorter="false" class="col-name">${_('Name')}</th>
                                            <th data-sorter="false" class="col-name columnSelector-false location">${_('File Name')}</th>
                                            <th data-sorter="false" class="col-ep columnSelector-false size">${_('Size')}</th>
                                            <th data-sorter="false" class="col-airdate">${_('Airdate')}</th>
                                            <th data-sorter="false" ${("class=\"col-ep columnSelector-false\"", "class=\"col-ep\"")[bool(sickbeard.DOWNLOAD_URL)]}>${_('Download')}</th>
                                            <th data-sorter="false" ${("class=\"col-ep columnSelector-false\"", "class=\"col-ep\"")[bool(sickbeard.USE_SUBTITLES)]}>${_('Subtitles')}</th>
                                            <th data-sorter="false" class="col-status">${_('Status')}</th>
                                            <th data-sorter="false" class="col-search">${_('Search')}</th>
                                        </tr>
                                    </thead>

                                % if not sickbeard.DISPLAY_ALL_SEASONS:
                                    <tbody class="toggle collapse${("", " in")[curSeason == -1]}" id="collapseSeason-${epResult[b'season']}">
                                % else:
                                    <tbody>
                                % endif
                                <% curSeason = int(epResult[b"season"]) %>
                % endif
                                    <tr class="${Overview.overviewStrings[epCats[epStr]]} season-${curSeason} seasonstyle" id="${'S' + str(epResult[b"season"]) + 'E' + str(epResult[b"episode"])}">
                                        <td class="col-checkbox">
                                            % if int(epResult[b"status"]) != UNAIRED:
                                                <input type="checkbox" class="epCheck" id="${str(epResult[b"season"])+'x'+str(epResult[b"episode"])}" name="${str(epResult[b"season"]) +"x"+str(epResult[b"episode"])}" />
                                            % endif
                                        </td>
                                        <td align="center"><img src="${static_url('images/' + ("nfo-no.gif", "nfo.gif")[epResult[b"hasnfo"]])}" alt="${("N", "Y")[epResult[b"hasnfo"]]}" width="23" height="11" /></td>
                                        <td align="center"><img src="${static_url('images/' + ("tbn-no.gif", "tbn.gif")[epResult[b"hastbn"]])}" alt="${("N", "Y")[epResult[b"hastbn"]]}" width="23" height="11" /></td>
                                        <td align="center" class="episode">
                                            <%
                                                text = str(epResult[b'episode'])
                                                if epLoc:
                                                    text = '<span title="' + epLoc + '" class="addQTip">' + text + "</span>"
                                            %>
                                        ${text}
                                        </td>
                                        <td align="center">${epResult[b"absolute_number"]}</td>
                                        <td align="center">
                                            <input type="text" placeholder="${str(dfltSeas) + 'x' + str(dfltEpis)}" size="6" maxlength="8"
                                                   class="sceneSeasonXEpisode form-control input-scene" data-for-season="${epResult[b"season"]}" data-for-episode="${epResult[b"episode"]}"
                                                   id="sceneSeasonXEpisode_${show.indexerid}_${str(epResult[b"season"])}_${str(epResult[b"episode"])}"
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
                                                   class="sceneAbsolute form-control input-scene" data-for-absolute="${epResult[b"absolute_number"]}"
                                                   id="sceneAbsolute_${show.indexerid}${"_"+str(epResult[b"absolute_number"])}"
                                                   title="${_('Change the value here if scene absolute numbering differs from the indexer absolute numbering')}"
                                                % if dfltAbsNumbering:
                                                   value=""
                                                % else:
                                                   value="${str(scAbsolute)}"
                                                % endif
                                                   style="padding: 0; text-align: center; max-width: 60px;" autocapitalize="off" />
                                        </td>
                                        <td class="col-name">
                                            % if epResult[b"description"] != "" and epResult[b"description"] is not None:
                                                <img src="${static_url('images/info32.png')}" width="16" height="16" class="plotInfo" alt="" id="plot_info_${str(show.indexerid)}_${str(epResult[b"season"])}_${str(epResult[b"episode"])}" />
                                            % else:
                                                <img src="${static_url('images/info32.png')}" width="16" height="16" class="plotInfoNone" alt="" />
                                            % endif
                                            ${epResult[b"name"]}
                                        </td>
                                        <td class="col-name location">${epLoc}</td>
                                        <td class="col-ep size">
                                            % if epResult[b"file_size"]:
                                            ${pretty_file_size(epResult[b"file_size"])}
                                            % endif
                                        </td>
                                        <td class="col-airdate">
                                            % if int(epResult[b'airdate']) != 1:
                                            ## Lets do this exactly like ComingEpisodes and History
                                            ## Avoid issues with dateutil's _isdst on Windows but still provide air dates
                                        <% airDate = datetime.datetime.fromordinal(epResult[b'airdate']) %>
                                            % if airDate.year >= 1970 or show.network:
                                                <% airDate = sbdatetime.sbdatetime.convert_to_setting(network_timezones.parse_date_time(epResult[b'airdate'], show.airs, show.network)) %>
                                            % endif
                                                <time datetime="${airDate.isoformat('T')}" class="date">${sbdatetime.sbdatetime.sbfdatetime(airDate)}</time>
                                            % else:
                                                Never
                                            % endif
                                        </td>
                                        <td>
                                            % if sickbeard.DOWNLOAD_URL and epResult[b'location']:
                                            <%
                                                filename = epResult[b'location']
                                                for rootDir in sickbeard.ROOT_DIRS.split('|'):
                                                    if rootDir.startswith('/'):
                                                        filename = filename.replace(rootDir, "")
                                                filename = sickbeard.DOWNLOAD_URL + urllib.quote(filename.encode('utf8'))
                                            %>
                                                <center><a href="${filename}">${_('Download')}</a></center>
                                            % endif
                                        </td>
                                        <td class="col-subtitles" align="center">
                                            % for flag in (epResult[b"subtitles"] or '').split(','):
                                                % if flag.strip():
                                                    % if flag != 'und':
                                                        <a class="epRetrySubtitlesSearch" href="retrySearchSubtitles?show=${show.indexerid}&amp;season=${epResult[b"season"]}&amp;episode=${epResult[b"episode"]}&amp;lang=${flag}">
                                                            <img src="${static_url('images/subtitles/flags/' + flag + '.png') }" data-image-url="${ static_url('images/subtitles/flags/' + flag + '.png') }" width="16" height="11" alt="${subtitles.name_from_code(flag)}" onError="this.onerror=null;this.src='${ static_url('images/flags/unknown.png')}';" />
                                                        </a>
                                                    % else:
                                                        <img src="${static_url('images/subtitles/flags/' + flag + '.png') }" width="16" height="11" alt="${subtitles.name_from_code(flag)}" onError="this.onerror=null;this.src='${ static_url('images/flags/unknown.png')}';" />
                                                    % endif
                                                % endif
                                            % endfor
                                        </td>
                                        <% curStatus, curQuality = Quality.splitCompositeStatus(int(epResult[b"status"])) %>
                                        % if curQuality != Quality.NONE:
                                            <td class="col-status">${statusStrings[curStatus]} ${renderQualityPill(curQuality)}</td>
                                        % else:
                                            <td class="col-status">${statusStrings[curStatus]}</td>
                                        % endif
                                        <td class="col-search">
                                            % if int(epResult[b"season"]) != 0:
                                                % if (int(epResult[b"status"]) in Quality.SNATCHED + Quality.SNATCHED_PROPER + Quality.SNATCHED_BEST + Quality.DOWNLOADED ) and sickbeard.USE_FAILED_DOWNLOADS:
                                                    <a class="epRetry" id="${str(show.indexerid)}x${str(epResult[b"season"])}x${str(epResult[b"episode"])}" name="${str(show.indexerid)}x${str(epResult[b"season"])}x${str(epResult[b"episode"])}" href="retryEpisode?show=${show.indexerid}&amp;season=${epResult[b"season"]}&amp;episode=${epResult[b"episode"]}"><span class="displayshow-icon-search" title="Retry Download" /></a>
                                                % else:
                                                    <a class="epSearch" id="${str(show.indexerid)}x${str(epResult[b"season"])}x${str(epResult[b"episode"])}" name="${str(show.indexerid)}x${str(epResult[b"season"])}x${str(epResult[b"episode"])}" href="searchEpisode?show=${show.indexerid}&amp;season=${epResult[b"season"]}&amp;episode=${epResult[b"episode"]}"><span class="displayshow-icon-search" title="Manual Search" /></a>
                                                % endif
                                            % endif
                                            % if int(epResult[b"status"]) not in Quality.SNATCHED + Quality.SNATCHED_PROPER and sickbeard.USE_SUBTITLES and show.subtitles and epResult[b"location"] and subtitles.needs_subtitles(epResult['subtitles']):
                                                % if int(epResult[b"season"]) != 0 or sickbeard.SUBTITLES_INCLUDE_SPECIALS:
                                                    <a class="epSubtitlesSearch" href="searchEpisodeSubtitles?show=${show.indexerid}&amp;season=${epResult[b"season"]}&amp;episode=${epResult[b"episode"]}"><span class="displayshow-icon-sub" title="Search Subtitles" /></a>
                                                % endif
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

    <div id="confirmSubtitleDownloadModal" class="modal fade">
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header">
                    <button type="button" class="close" data-dismiss="modal" aria-hidden="true">&times;</button>
                    <h4 class="modal-title">${_('Download subtitle')}</h4>
                </div>
                <div class="modal-body">
                    <p>${_('Do you want to re-download the subtitle for this language?')}</p>
                    <p class="text-warning"><small>${_('It will overwrite your current subtitle')}</small></p>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-info" data-dismiss="modal">${_('No')}</button>
                    <button type="button" class="btn btn-success" data-dismiss="modal">${_('Yes')}</button>
                </div>
            </div>
        </div>
    </div>
</%block>
