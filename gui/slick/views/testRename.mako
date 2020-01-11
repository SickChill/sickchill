<%inherit file="/layouts/main.mako"/>
<%!
    import sickbeard
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
                % if show.air_by_date and sickbeard.NAMING_CUSTOM_ABD:
                    ${sickbeard.NAMING_ABD_PATTERN}
                % elif show.is_sports and sickbeard.NAMING_CUSTOM_SPORTS:
                    ${sickbeard.NAMING_SPORTS_PATTERN}
                % elif show.is_anime and sickbeard.NAMING_CUSTOM_ANIME:
                    ${sickbeard.NAMING_CUSTOM_ANIME}
                %else:
                    ${sickbeard.NAMING_PATTERN}
                % endif
            </blockquote>

            <% curSeason = -1 %>
            <% odd = False%>

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
            <a href="${srRoot}/home/displayShow?show=${show.indexerid}" class="btn btn-danger">
                ${_('Cancel Rename')}
            </a>
        </div>
    </div>
    <div class="row">
        <div class="col-md-12">
            % for cur_ep_obj in ep_obj_list:
                <%
                    curLoc = cur_ep_obj.location[len(cur_ep_obj.show._location)+1:]
                    curExt = curLoc.split('.')[-1]
                    newLoc = cur_ep_obj.proper_path() + '.' + curExt
                %>
                % if int(cur_ep_obj.season) != curSeason:
                    % if cur_ep_obj.season != ep_obj_list[0].season:
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                    % endif
                    <div class="row">
                        <div class="col-md-12">
                            <h2>${('Season '+str(cur_ep_obj.season), 'Specials')[int(cur_ep_obj.season) == 0]}</h2>
                        </div>
                    </div>
                    <div class="row">
                        <div class="col-md-12">
                            <div class="horizontal-scroll">
                                <table id="testRenameTable" class="sickbeardTable" cellspacing="1" border="0" cellpadding="0">
                                    <thead>
                                        <tr class="seasoncols" id="season-${cur_ep_obj.season}-cols">
                                            <th class="col-checkbox"><input type="checkbox" class="seasonCheck" id="${cur_ep_obj.season}" /></th>
                                            <th class="nowrap">${_('Episode')}</th>
                                            <th class="col-name">${_('Old Location')}</th>
                                            <th class="col-name">${_('New Location')}</th>
                                        </tr>
                                    </thead>
                                    <% curSeason = int(cur_ep_obj.season) %>
                                    <tbody>
                % endif
                                        <%
                                            odd = not odd
                                            epStr = str(cur_ep_obj.season) + "x" + str(cur_ep_obj.episode)
                                            epList = sorted([cur_ep_obj.episode] + [x.episode for x in cur_ep_obj.relatedEps])
                                            if len(epList) > 1:
                                                epList = [min(epList), max(epList)]
                                        %>
                                        <tr class="season-${curSeason} ${('wanted', 'good')[curLoc == newLoc]} seasonstyle">
                                            <td class="col-checkbox">
                                                % if curLoc != newLoc:
                                                    <input type="checkbox" class="epCheck" id="${str(cur_ep_obj.season) + 'x' + str(cur_ep_obj.episode)}" name="${str(cur_ep_obj.season) + "x" + str(cur_ep_obj.episode)}"  title="Episode check"/>
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
        </div>
    </div>
    <br/>
    <div class="row">
        <div class="col-md-12">
            <input type="submit" value="${_('Rename Selected')}" class="btn btn-success"/>
            <a href="${srRoot}/home/displayShow?show=${show.indexerid}" class="btn btn-danger">
                ${_('Cancel Rename')}
            </a>
        </div>
    </div>
</%block>
