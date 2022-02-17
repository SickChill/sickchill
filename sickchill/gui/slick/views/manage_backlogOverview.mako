<%inherit file="/layouts/main.mako"/>
<%!
    import datetime
    from sickchill import settings
    from sickchill.oldbeard import sbdatetime, network_timezones
    from sickchill.oldbeard.common import WANTED, SNATCHED, SNATCHED_PROPER, SNATCHED_BEST, Overview, Quality
    from sickchill.helper.common import episode_num
%>
<%block name="content">
    <div class="row">
        <div class="col-lg-8 col-md-7 col-sm-6 col-xs-12 pull-right">
            <div class="pull-right">
                % if totalWanted > 0:
                    <span class="listing-key wanted">${_('Wanted')}: <b>${totalWanted}</b></span>
                % endif

                % if totalQualSnatched > 0:
                    <span class="listing-key snatched">${_('Snatched (Allowed)')}: <b>${totalQualSnatched}</b></span>
                % endif

                % if totalQual > 0:
                    <span class="listing-key qual">${_('Allowed')}: <b>${totalQual}</b></span>
                % endif
            </div>
        </div>
        <div class="col-lg-4 col-md-5 col-sm-6 col-xs-12">
            % if not header is UNDEFINED:
                <h1 class="header">${header}</h1>
            % else:
                <h1 class="title">${title}</h1>
            % endif
        </div>
    </div>
    <div class="row">
        <div class="col-md-12">
            <label for="pickShow">${_('Jump to Show')}:</label>
            <select id="pickShow" class="form-control form-control-inline input-sm">
                % for curShow in backLogShows:
                    <option value="${curShow.indexerid}">${curShow.name}</option>
                % endfor
            </select>
        </div>
    </div>

    % for curShow in backLogShows:
        % if not showQualSnatched(curShow) and not showCounts[curShow.indexerid][Overview.WANTED] + showCounts[curShow.indexerid][Overview.QUAL]:
            <% continue %>
        % endif

        <div class="row">
            <div class="col-md-12">
                <div class="pull-right" style="margin-top: 30px;">
                    % if showCounts[curShow.indexerid][Overview.WANTED] > 0:
                        <span class="listing-key wanted">${_('Wanted')}: <b>${showCounts[curShow.indexerid][Overview.WANTED]}</b></span>
                    % endif

                    % if showQualSnatched(curShow) and showCounts[curShow.indexerid][Overview.SNATCHED] > 0:
                        <span class="listing-key snatched">${_('Snatched (Allowed)')}: <b>${showCounts[curShow.indexerid][Overview.SNATCHED]}</b></span>
                    % endif

                    % if showCounts[curShow.indexerid][Overview.QUAL] > 0:
                        <span class="listing-key qual">${_('Allowed')}: <b>${showCounts[curShow.indexerid][Overview.QUAL]}</b></span>
                    % endif

                    <a class="btn btn-inline forceBacklog" href="${scRoot}/manage/backlogShow?indexer_id=${curShow.indexerid}"><i class="icon-play-circle icon-white"></i> ${_('Force Backlog')}</a>
                </div>

                <h2 style="display: inline-block;">
                    <a href="${scRoot}/home/displayShow?show=${curShow.indexerid}">${curShow.name}</a>
                </h2>
            </div>
        </div>
        <div class="row">
            <div class="col-md-12">
                <div class="horizontal-scroll">
                    <table class="sickchillTable">
                        <tr class="seasonheader" id="show-${curShow.indexerid}">
                            <td colspan="3" class="align-left" style="position: relative;"></td>
                        </tr>
                        <tr class="seasoncols"><th>${_('Episode')}</th><th>${_('Name')}</th><th class="nowrap">${_('Airdate')}</th></tr>

                        % for curResult in showSQLResults[curShow.indexerid]:
                            <%
                                whichStr = episode_num(curResult['season'], curResult['episode']) or episode_num(curResult['season'], curResult['episode'], numbering='absolute')
                                if whichStr not in showCats[curShow.indexerid] or showCats[curShow.indexerid][whichStr] not in (Overview.QUAL, Overview.WANTED, Overview.SNATCHED):
                                    continue

                                if not showQualSnatched(curShow) and showCats[curShow.indexerid][whichStr] == Overview.SNATCHED:
                                    continue
                            %>
                            <tr class="seasonstyle ${Overview.overviewStrings[showCats[curShow.indexerid][whichStr]]}">
                                <td class="tableleft" align="center">${whichStr}</td>
                                <td class="tableright" align="center" class="nowrap">
                                    ${curResult["name"]}
                                </td>
                                <td>
                                    % try:
                                        % if int(curResult['airdate']) > 1:
                                            <% airDate = datetime.datetime.fromordinal(curResult['airdate']) %>
                                            % if airDate > datetime.datetime.utcfromtimestamp(0) or curShow.network:
                                                <% airDate = sbdatetime.sbdatetime.convert_to_setting(network_timezones.parse_date_time(curResult['airdate'], curShow.airs, curShow.network)) %>
                                            % endif
                                            <time datetime="${airDate.isoformat('T')}" class="date">${sbdatetime.sbdatetime.sbfdatetime(airDate)}</time>
                                        % else:
                                            Never
                                        % endif
                                    % except:
                                        Unknown
                                    % endtry
                                </td>
                            </tr>
                        % endfor
                    </table>
                </div>
            </div>
        </div>
    % endfor
</%block>
