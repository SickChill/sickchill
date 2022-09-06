<%inherit file="/layouts/main.mako"/>
<%!
    import datetime
    from urllib.parse import quote
    from sickchill import settings
    from sickchill.oldbeard import subtitles, notifiers, sbdatetime, network_timezones, helpers

    from sickchill.oldbeard.common import SKIPPED, WANTED, UNAIRED, ARCHIVED, IGNORED, FAILED, DOWNLOADED
    from sickchill.oldbeard.common import Quality, qualityPresets, statusStrings, Overview
    from sickchill.oldbeard.helpers import anon_url
    from sickchill.helper.common import pretty_file_size, try_int
%>
<%block name="metas">
    <meta data-var="showBackgroundImage" data-content="${static_url(show.show_image_url('fanart'))}">
</%block>
<%block name="scripts">
    <script type="text/javascript" src="${static_url('js/lib/jquery.bookmarkscroll.js')}"></script>
    <script type="text/javascript" src="${static_url('js/plotTooltip.js')}"></script>
    <script type="text/javascript" src="${static_url('js/sceneExceptionsTooltip.js')}"></script>
    <script type="text/javascript" src="${static_url('js/ratingTooltip.js')}"></script>
    <script type="text/javascript" src="${static_url('js/ajaxEpSearch.js')}"></script>
</%block>

<%block name="content">
    <%namespace file="/inc_defs.mako" import="renderQualityPill"/>
    <%namespace file="/inc_defs.mako" import="renderStatusPill"/>
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
                        % if not settings.DISPLAY_SHOW_SPECIALS and season_special:
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
                                    <label id="seasonJumpLinks">
                                        <span>${_('Season')}:</span>
                                        % for seasonNum in seasonResults:
                                            % if int(seasonNum["season"]) == 0:
                                                <a data-season="season-${seasonNum["season"]}" href="#">${_('Specials')}</a>
                                            % else:
                                                <a data-season="season-${seasonNum["season"]}" href="#">${seasonNum["season"]}</a>
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
                        <a href="${static_url(show.show_image_url('poster_thumb'))}">
                            <img src="${static_url(show.show_image_url('poster_thumb'))}"
                                 class="tvshowImg" alt="${_('Poster for')} ${show.name}"
                            />
                        </a>

                    </div>
                    <div class="info-container">
                        <div class="row">
                            <div class="pull-right col-lg-4 col-md-4 hidden-sm hidden-xs">
                                <img src="${static_url(show.show_image_url('banner'))}"
                                     style="max-height:50px;border:1px solid black;" class="pull-right">
                            </div>
                            <div class="pull-left col-lg-8 col-md-8 col-sm-12 col-xs-12">
                                % if 'rating' in show.imdb_info and 'votes' in show.imdb_info:
                                    <% rating_tip = str(show.imdb_info['rating']) + " / 10" + _('Stars') + "<br>" + str(show.imdb_info['votes']) +  _('Votes') %>
                                    <span class="imdbstars" data-qtip-content="${rating_tip}">${show.imdb_info['rating']}</span>
                                % endif

                                % if not show.imdb_id:
                                    <span>(${show.startyear}) - ${show.runtime} ${_('minutes')} - </span>
                                % else:
                                    % if 'country_codes' in show.imdb_info:
                                        % for country in show.imdb_info['country_codes'].split('|'):
                                            <img src="${static_url('images/blank.png')}" class="country-flag flag-${country}" width="16" height="11" style="margin-left: 3px; vertical-align:middle;" />
                                        % endfor
                                    % endif
                                    <span>
                                    % if show.imdb_info.get('year'):
                                        (${show.imdb_info['year']})
                                    % endif
                                    % if show.imdb_info.get('runtimes'):
                                        ${show.imdb_info['runtimes']} ${_('minutes')}
                                    % endif
                                    </span>
                                    <a href="${anon_url('http://www.imdb.com/title/', show.imdb_id)}" rel="noreferrer" target="_blank" title="http://www.imdb.com/title/${show.imdb_id}"><span class="displayshow-icon-imdb"></span></a>
                                    <a href="${anon_url('https://trakt.tv/shows/', show.imdb_id)}" rel="noreferrer" target="_blank" title="https://trakt.tv/shows/${show.imdb_id}"><span class="displayshow-icon-trakt"></span></a>
                                % endif
                                <a href="${anon_url(show.idxr.show_url, show.indexerid)}" target="_blank"
                                   title="${show.idxr.show_url + str(show.indexerid)}"><img alt="${show.idxr.name}" src="${static_url(show.idxr.icon)}" style="margin-top: -1px; vertical-align:middle;"/></a>
                                % if xem_numbering or xem_absolute_numbering:
                                    <a href="${anon_url('http://thexem.info/search?q=', show.name)}" rel="noreferrer" target="_blank" title="http://thexem.info/search?q-${show.name}"><span class="displayshow-icon-xem"></span></a>
                                % endif
                                <a href="${anon_url('https://fanart.tv/series/', show.indexerid)}" rel="noreferrer" target="_blank" title="https://fanart.tv/series/${show.name}"><span class="displayshow-icon-fanart"></span></a>
                            </div>
                            <div class="pull-left col-lg-8 col-md-8 col-sm-12 col-xs-12">
                                <ul class="tags">
                                    % if show.genre and not show.imdb_info.get('genres'):
                                        % for genre in show.genre:
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
                                                </td>
                                            </tr>
                                            % if show.network and show.airs:
                                                <tr>
                                                    <td class="showLegend">${_('Originally Airs')}: </td>
                                                    <td>${show.airs} ${("<font color='#FF0000'><b>(invalid Timeformat)</b></font> ", "")[network_timezones.test_timeformat(show.airs)]} on ${show.network}</td>
                                                </tr>
                                            % elif show.network:
                                                <tr>
                                                    <td class="showLegend">${_('Originally Airs')}: </td>
                                                    <td>${show.network}</td>
                                                </tr>
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

                                            % if show.rls_prefer_words:
                                                <tr>
                                                    <td class="showLegend">${_('Preferred Words')}: </td>
                                                    <td>${show.rls_prefer_words}</td>
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
                                                <td>${pretty_file_size(helpers.get_size(showLoc[0]))}</td>
                                            </tr>
                                        </table>
                                    </div>
                                    <div class="col-lg-4 col-md-4 col-sm-4 col-xs-12 pull-xs-left">
                                        <table class="pull-xs-left pull-md-right pull-sm-right pull-lg-right">
                                            <% info_flag = subtitles.code_from_code(show.lang) if show.lang else '' %>
                                            <tr>
                                                <td class="showLegend">${_('Info Language')}:</td>
                                                <td><img src="${static_url('images/subtitles/flags/' + info_flag + '.png') }" width="16" height="11" alt="${show.lang}" title="${show.lang}" onError="this.onerror=null;this.src='${static_url('images/flags/unknown.png')}';"/></td>
                                            </tr>
                                            % if settings.USE_SUBTITLES:
                                                <tr>
                                                    <td class="showLegend">${_('Subtitles')}: </td>
                                                    <td><span class="displayshow-icon-${("disable", "enable")[bool(show.subtitles)]}" title=${("N", "Y")[bool(show.subtitles)]}></span></td>
                                                </tr>
                                            % endif
                                            <tr>
                                                <td class="showLegend">${_('Subtitles SC Metadata')}: </td>
                                                <td><span class="displayshow-icon-${("disable", "enable")[bool(show.subtitles_sr_metadata)]}" title=${("N", "Y")[bool(show.subtitles_sr_metadata)]}></span></td>
                                            </tr>
                                            <tr>
                                                <td class="showLegend">${_('Season Folders')}: </td>
                                                <td><span class="displayshow-icon-${("disable", "enable")[bool(show.season_folders or settings.NAMING_FORCE_FOLDERS)]}" title=${("N", "Y")[bool(show.season_folders or settings.NAMING_FORCE_FOLDERS)]}></span></td>
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
                                                <td><span class="displayshow-icon-${("disable", "enable")[show.is_sports]}" title=${("N", "Y")[show.is_sports]}></span></td>
                                            </tr>
                                            <tr>
                                                <td class="showLegend">${_('Anime')}: </td>
                                                <td><span class="displayshow-icon-${("disable", "enable")[show.is_anime]}" title=${("N", "Y")[show.is_anime]}></span></td>
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
                        % if not settings.USE_FAILED_DOWNLOADS:
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
            % for epResult in sql_results:
                <%
                    epStr = str(epResult["season"]) + "x" + str(epResult["episode"])
                    if not epStr in epCats:
                        continue

                    if not settings.DISPLAY_SHOW_SPECIALS and int(epResult["season"]) == 0:
                        continue

                    scene = False
                    scene_anime = False
                    if not show.air_by_date and not show.is_sports and not show.is_anime and show.is_scene:
                        scene = True
                    elif not show.air_by_date and not show.is_sports and show.is_anime and show.is_scene:
                        scene_anime = True

                    (default_season, default_episode, default_absolute_number) = (0, 0, 0)
                    if (epResult["season"], epResult["episode"]) in xem_numbering:
                        (default_season, default_episode) = xem_numbering[(epResult["season"], epResult["episode"])]

                    if epResult["absolute_number"] in xem_absolute_numbering:
                        default_absolute_number = xem_absolute_numbering[epResult["absolute_number"]]

                    if epResult["absolute_number"] in scene_absolute_numbering:
                        scAbsolute = scene_absolute_numbering[epResult["absolute_number"]]
                        default_absolute_numbering = False
                    else:
                        scAbsolute = default_absolute_number
                        default_absolute_numbering = True

                    if (epResult["season"], epResult["episode"]) in scene_numbering:
                        (season_number, episode_number) = scene_numbering[(epResult["season"], epResult["episode"])]
                        default_episode_numbering = False
                    else:
                        (season_number, episode_number) = (default_season, default_episode)
                        default_episode_numbering = True

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
                    <div class="row seasonheader" data-season-id="${epResult["season"]}">
                        <div class="col-md-12">
                            <br/>
                            <h3 style="display: inline;"><a id="season-${epResult["season"]}"></a>${(_("Specials"), _("Season") + ' ' + str(epResult["season"]))[int(epResult["season"]) > 0]}</h3>
                            % if not settings.DISPLAY_ALL_SEASONS:
                                % if curSeason == -1:
                                    <button id="showseason-${epResult['season']}" type="button" class="btn btn-xs pull-right" data-toggle="collapse" data-target="#collapseSeason-${epResult['season']}" aria-expanded="true">${_('Hide Episodes')}</button>
                                %else:
                                    <button id="showseason-${epResult['season']}" type="button" class="btn btn-xs pull-right" data-toggle="collapse" data-target="#collapseSeason-${epResult['season']}">${_('Show Episodes')}</button>
                                %endif
                            % endif
                        </div>
                    </div>
                    <div class="row" id="${epResult["season"]}-cols">
                        <div class="col-md-12">
                            <div class="horizontal-scroll">
                                <table id="${("showTable", "animeTable")[show.is_anime]}" class="displayShowTable display_show" cellspacing="0" border="0" cellpadding="0">
                                    <thead>
                                        <tr class="seasoncols ${epResult["season"]}">
                                            <th data-sorter="false" data-priority="critical" class="col-checkbox">
                                                <input type="checkbox" class="seasonCheck" id="${epResult["season"]}" />
                                            </th>
                                            <th data-sorter="false" class="col-metadata">${_('NFO')}</th>
                                            <th data-sorter="false" class="col-metadata">${_('TBN')}</th>
                                            <th data-sorter="false" class="col-ep episode">${_('Episode')}</th>
                                            <th data-sorter="false" ${("class=\"col-ep columnSelector-false\"", "class=\"col-ep\"")[show.is_anime]}>${_('Absolute')}</th>
                                            <th data-sorter="false" ${("class=\"col-ep columnSelector-false\"", "class=\"col-ep\"")[scene]}>${_('Scene')}</th>
                                            <th data-sorter="false" ${("class=\"col-ep columnSelector-false\"", "class=\"col-ep\"")[scene_anime]}>${_('Scene Absolute')}</th>
                                            <th data-sorter="false" class="col-name">${_('Name')}</th>
                                            <th data-sorter="false" class="col-name columnSelector-false location">${_('File Name')}</th>
                                            <th data-sorter="false" class="col-ep columnSelector-false size">${_('Size')}</th>
                                            <th data-sorter="false" class="col-airdate">${_('Airdate')}</th>
                                            <th data-sorter="false" ${("class=\"col-ep columnSelector-false\"", "class=\"col-ep\"")[bool(settings.DOWNLOAD_URL)]}>${_('Download')}</th>
                                            <th data-sorter="false" ${("class=\"col-ep columnSelector-false\"", "class=\"col-ep\"")[bool(settings.KODI_HOST and settings.USE_KODI)]}>${_('Play')}</th>
                                            <th data-sorter="false" ${("class=\"col-ep columnSelector-false\"", "class=\"col-ep\"")[bool(settings.USE_SUBTITLES)]}>${_('Subtitles')}</th>
                                            <th data-sorter="false" class="col-ep">${_('Status')}</th>
                                            <th data-sorter="false" class="col-search text-nowrap">
                                                ${_('Search')}
                                                <a class="manual-snatch-show-release" href="manual_search_show_releases?show=${show.indexerid}&amp;season=${epResult["season"]}">
                                                    <span class="displayshow-icon-plus" title="Manual Snatch Season"></span>
                                                </a>
                                            </th>
                                        </tr>
                                    </thead>

                                % if not settings.DISPLAY_ALL_SEASONS:
                                    <tbody class="toggle collapse${("", " in")[curSeason == -1]}" id="collapseSeason-${epResult['season']}">
                                % else:
                                    <tbody>
                                % endif
                                <% curSeason = epResult["season"] %>
                % endif
                                    <tr class="${Overview.overviewStrings[epCats[epStr]]} season-${curSeason} seasonstyle" id="S${epResult["season"]}E${epResult["episode"]}">
                                        <td class="col-checkbox">
                                            % if try_int(epResult["status"]) != UNAIRED:
                                                <input type="checkbox" class="epCheck" id="${epStr}" name="${epStr}" />
                                            % endif
                                        </td>
                                        <td align="center">
                                            <img src="${static_url('images/' + ("nfo-no.gif", "nfo.gif")[bool(epResult["hasnfo"])])}"
                                                                alt="${("N", "Y")[bool(epResult["hasnfo"])]}" width="23" height="11" />
                                        </td>
                                        <td align="center">
                                            <img src="${static_url('images/' + ("tbn-no.gif", "tbn.gif")[bool(epResult["hastbn"])])}"
                                                 alt="${("N", "Y")[bool(epResult["hastbn"])]}" width="23" height="11" />
                                        </td>
                                        <td align="center" class="episode">
                                            <%
                                                text = str(epResult['episode'])
                                                if epLoc:
                                                    text = '<span title="' + epLoc + '" class="addQTip">' + text + "</span>"
                                            %>
                                        ${text}
                                        </td>
                                        <td align="center">${epResult["absolute_number"]}</td>
                                        <td align="center">
                                            <input type="text" placeholder="${str(default_season) + 'x' + str(default_episode)}" size="6" maxlength="8"
                                                   class="sceneSeasonXEpisode form-control input-scene" data-for-season="${epResult["season"]}" data-for-episode="${epResult["episode"]}"
                                                   id="sceneSeasonXEpisode_${show.indexerid}_${epResult["season"]}_${epResult["episode"]}"
                                                   title="${_('Change the value here if scene numbering differs from the indexer episode numbering')}"
                                                % if default_episode_numbering:
                                                   value=""
                                                % else:
                                                   value="${str(season_number)}x${str(episode_number)}"
                                                % endif
                                                   style="padding: 0; text-align: center; max-width: 60px;" autocapitalize="off" />
                                        </td>
                                        <td align="center">
                                            <input type="text" placeholder="${str(default_absolute_number)}" size="6" maxlength="8"
                                                   class="sceneAbsolute form-control input-scene" data-for-absolute="${epResult["absolute_number"]}"
                                                   id="sceneAbsolute_${show.indexerid}_${epResult["absolute_number"]}"
                                                   title="${_('Change the value here if scene absolute numbering differs from the indexer absolute numbering')}"
                                                % if default_absolute_numbering:
                                                   value=""
                                                % else:
                                                   value="${str(scAbsolute)}"
                                                % endif
                                                   style="padding: 0; text-align: center; max-width: 60px;" autocapitalize="off" />
                                        </td>
                                        <td class="col-name">
                                            % if epResult["description"]:
                                                <img src="${static_url('images/info32.png')}" width="16" height="16" class="plotInfo" alt="" id="plot_info_${str(show.indexerid)}_${epResult["season"]}_${epResult["episode"]}" />
                                            % else:
                                                <img src="${static_url('images/info32.png')}" width="16" height="16" class="plotInfoNone" alt="" />
                                            % endif
                                            ${epResult["name"]}
                                        </td>
                                        <td class="col-name location">${epLoc}</td>
                                        <td class="col-ep size">
                                            % if epResult["file_size"]:
                                            ${pretty_file_size(epResult["file_size"])}
                                            % endif
                                        </td>
                                        <td class="col-airdate">
                                            % if int(epResult['airdate']) > 1:
                                                ## Lets do this exactly like ComingEpisodes and History
                                                ## Avoid issues with dateutil's _isdst on Windows but still provide air dates
                                                <% airDate = datetime.datetime.fromordinal(epResult['airdate'] or 1) %>
                                                % if airDate.year >= 1970 or show.network:
                                                    <% airDate = sbdatetime.sbdatetime.convert_to_setting(network_timezones.parse_date_time(epResult['airdate'], show.airs, show.network)) %>
                                                % endif
                                                <time datetime="${airDate.isoformat('T')}" class="date">${sbdatetime.sbdatetime.sbfdatetime(airDate)}</time>
                                            % else:
                                                Never
                                            % endif
                                        </td>
                                        <td class="col-download">
                                            % if settings.DOWNLOAD_URL and epResult['location']:
                                                <%
                                                    filename = epResult['location']
                                                    for rootDir in settings.ROOT_DIRS.split('|'):
                                                        if rootDir.startswith('/'):
                                                            filename = filename.replace(rootDir, "")
                                                    filename = settings.DOWNLOAD_URL + quote(filename)
                                                %>
                                                <a href="${filename}">${_('Download')}</a>
                                            % endif
                                        </td>
                                        <td class="col-play" align="center">
                                            <a class="play-on-kodi${(' hidden', '')[bool(epResult['location'] and settings.USE_KODI and settings.KODI_HOST)]}"
                                               href="playOnKodi?show=${show.indexerid}&amp;season=${epResult["season"]}&amp;episode=${epResult["episode"]}"
                                            >
                                                <span class="displayshow-play-icon-kodi" title="KODI"></span>
                                            </a>
                                        </td>
                                        <td class="col-subtitles" align="center">
                                            % for flag in (epResult["subtitles"] or '').split(','):
                                                % if flag.strip():
                                                    % if flag != 'und':
                                                        <a class="epRetrySubtitlesSearch" href="retrySearchSubtitles?show=${show.indexerid}&amp;season=${epResult["season"]}&amp;episode=${epResult["episode"]}&amp;lang=${flag}">
                                                            <img src="${static_url('images/subtitles/flags/' + flag + '.png')}" data-image-url="${static_url('images/subtitles/flags/' + flag + '.png')}" width="16" height="11" alt="${subtitles.name_from_code(flag)}" onError="this.onerror=null;this.src='${static_url('images/flags/unknown.png')}';" />
                                                        </a>
                                                    % else:
                                                        <img src="${static_url('images/subtitles/flags/' + flag + '.png')}" width="16" height="11" alt="${subtitles.name_from_code(flag)}" onError="this.onerror=null;this.src='${static_url('images/flags/unknown.png')}';" />
                                                    % endif
                                                % endif
                                            % endfor
                                        </td>
                                        <% curStatus, curQuality = Quality.splitCompositeStatus(int(epResult["status"])) %>
                                        % if curQuality != Quality.NONE:
                                            <td class="col-status">${renderStatusPill(curStatus)} ${renderQualityPill(curQuality)}</td>
                                        % else:
                                            <td class="col-status">${renderStatusPill(curStatus)}</td>
                                        % endif
                                        <td class="col-search">
                                            % if int(epResult["season"]) != 0:
                                                % if (int(epResult["status"]) in Quality.SNATCHED + Quality.SNATCHED_PROPER + Quality.SNATCHED_BEST + Quality.DOWNLOADED ) and settings.USE_FAILED_DOWNLOADS:
                                                    <a class="epRetry" id="${str(show.indexerid)}x${epStr}" name="${str(show.indexerid)}x${epStr}" href="retryEpisode?show=${show.indexerid}&amp;season=${epResult["season"]}&amp;episode=${epResult["episode"]}">
                                                        <span class="displayshow-icon-search" title="Retry Download"></span>
                                                    </a>
                                                % else:
                                                    <a class="epSearch" id="${str(show.indexerid)}x${epStr}" name="${str(show.indexerid)}x${epStr}" href="searchEpisode?show=${show.indexerid}&amp;season=${epResult["season"]}&amp;episode=${epResult["episode"]}">
                                                        <span class="displayshow-icon-search" title="Manual Search"></span>
                                                    </a>
                                                % endif
                                                <a class="manual-snatch-show-release" href="manual_search_show_releases?show=${show.indexerid}&amp;season=${epResult["season"]}&amp;episode=${epResult["episode"]}">
                                                    <span class="displayshow-icon-plus" title="Manual Snatch"></span>
                                                </a>
                                            % endif
                                            % if int(epResult["status"]) not in Quality.SNATCHED + Quality.SNATCHED_PROPER and settings.USE_SUBTITLES and show.subtitles and epResult["location"] and subtitles.needs_subtitles(epResult['subtitles']):
                                                % if int(epResult["season"]) != 0 or settings.SUBTITLES_INCLUDE_SPECIALS:
                                                    <a class="epSubtitlesSearch" href="searchEpisodeSubtitles?show=${show.indexerid}&amp;season=${epResult["season"]}&amp;episode=${epResult["episode"]}">
                                                        <span class="displayshow-icon-sub" title="Search Subtitles"></span>
                                                    </a>
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

    <div id="playOnKodiModal" class="modal fade">
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header">
                    <button type="button" class="close" data-dismiss="modal">
                        <span aria-hidden="true">&times;</span>
                         <span class="sr-only">${_('Close')}</span>
                    </button>
                    <h4 class="modal-title">${_('Select Kodi Player')}</h4>
                </div>
                <div class="modal-body">
                    <div class="form-group col-md-12">
                        <select id="kodi-play-host" name="kodi-play-host" class="form-control">
                            % if settings.USE_KODI and settings.KODI_HOST:
                                % try:
                                    % for index, connection in enumerate(notifiers.kodi_notifier.connections):
                                        <option value="${index}">${connection.name} (${connection.host})</option>
                                    % endfor
                                % except:
                                    <% pass %>
                                % endtry
                            % endif
                        </select>
                    </div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-success" data-dismiss="modal">${_('Play')}</button>
                    <button type="button" class="btn btn-info" data-dismiss="modal">${_('Cancel')}</button>
                </div>
            </div>
        </div>
    </div>
</%block>
