<%inherit file="/layouts/main.mako"/>
<%!
    from sickchill import settings
    from sickchill.helper.common import try_int
%>
<%block name="scripts">
    <script type="text/javascript" src="${static_url('js/testRename.js')}" xmlns="http://www.w3.org/1999/html"></script>
</%block>

<%block name="content">
    <div class="row">
        <div class="col-md-12">
            % if not header is UNDEFINED:
                <h1 class="header">${header}</h1>
            % else:
                <h1 class="title">${title}</h1>
            % endif
        </div>
    </div>
    <div class="row">
        <div class="col-md-12">
            <input type="hidden" id="showID" value="${show.indexerid}" />

            <h3>${_('Preview of the proposed name changes')}</h3>
            <blockquote>
                % if show.air_by_date and settings.NAMING_CUSTOM_ABD:
                    ${settings.NAMING_ABD_PATTERN}
                % elif show.is_sports and settings.NAMING_CUSTOM_SPORTS:
                    ${settings.NAMING_SPORTS_PATTERN}
                % elif show.is_anime and settings.NAMING_CUSTOM_ANIME:
                    ${settings.NAMING_CUSTOM_ANIME}
                %else:
                    ${settings.NAMING_PATTERN}
                % endif
            </blockquote>
        </div>
    </div>
    <div class="row">
        <div class="col-md-12">
            <h2>${_('All Seasons')}</h2>
        </div>
    </div>
    <div class="row">
        <div class="col-md-12">
            <input type="checkbox" class="seriesCheck" id="select-all" title="Check"/>
            <label for="select-all">${_('select all')}</label>
        </div>
    </div>
    <div class="row">
        <div class="col-md-12">
            <input type="submit" value="${_('Rename Selected')}" class="btn btn-success"/>
            <a href="${scRoot}/home/displayShow?show=${show.indexerid}" class="btn btn-danger">
                ${_('Cancel Rename')}
            </a>
        </div>
    </div>
    <div class="row">
        <div class="col-md-12">
        % for current_season in sorted(show.episodes, reverse=True, key=lambda x: try_int(x)):
            <div class="row">
                <div class="col-md-12">
                    <h2>${('Season '+ str(current_season), 'Specials')[try_int(current_season, None) == 0]}</h2>
                </div>
            </div>
            <div class="row">
                <div class="col-md-12">
                    <div class="horizontal-scroll">
                        <table id="testRenameTable" class="sickchillTable">
                            <thead>
                                <tr class="seasoncols" id="season-${current_season}-cols">
                                    <th class="col-checkbox"><input type="checkbox" title="check_season" class="seasonCheck" id="${current_season}" /></th>
                                    <th class="nowrap">${_('Episode')}</th>
                                    <th class="col-name">${_('Old Location')}</th>
                                    <th class="col-name">${_('New Location')}</th>
                                </tr>
                            </thead>
                            <tbody>
                            % for current_episode in sorted(show.episodes[current_season], reverse=True):
                                <%
                                    ep_obj = show.episodes[current_season][current_episode]
                                    if not (ep_obj and ep_obj._location):
                                        continue

                                    epStr = str(ep_obj.season) + "x" + str(ep_obj.episode)

                                    epList = sorted([ep_obj.episode] + [x.episode for x in ep_obj.relatedEps])
                                    if ep_obj.episode != min(epList):
                                        continue

                                    if len(epList) > 1:
                                        epList = [min(epList), max(epList)]

                                    curLoc = ep_obj.location[len(show._location)+1:]
                                    curExt = curLoc.split('.')[-1]
                                    newLoc = ep_obj.proper_path() + '.' + curExt
                                %>
                                <tr class="season-${current_season} ${('wanted', 'good')[curLoc == newLoc]} seasonstyle">
                                    <td class="col-checkbox">
                                        % if curLoc != newLoc:
                                            <input type="checkbox" class="epCheck" id="${epStr}" name="${epStr}"  title="Episode check"/>
                                        % endif
                                    </td>
                                    <td align="center" valign="top" class="nowrap">${"-".join(map(str, epList))}</td>
                                    <td width="50%" class="col-name">${curLoc}</td>
                                    <td width="50%" class="col-name">${newLoc}</td>

                                </tr>
                            % endfor
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        % endfor
        </div>
    </div>
    <br/>
    <div class="row">
        <div class="col-md-12">
            <input type="submit" value="${_('Rename Selected')}" class="btn btn-success"/>
            <a href="${scRoot}/home/displayShow?show=${show.indexerid}" class="btn btn-danger">
                ${_('Cancel Rename')}
            </a>
        </div>
    </div>
</%block>
