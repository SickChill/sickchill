<%inherit file="/layouts/main.mako"/>
<%!
    import sickbeard
    import os.path
    import datetime

    from sickbeard import providers, sbdatetime

    from sickbeard.common import ARCHIVED, SNATCHED, FAILED, DOWNLOADED, SUBTITLED
    from sickbeard.common import Quality, statusStrings

    from sickrage.show.History import History
    from sickrage.helper.encoding import ek
    from sickrage.providers.GenericProvider import GenericProvider
%>
<%block name="content">
    <%namespace file="/inc_defs.mako" import="renderQualityPill"/>
    <div class="row">
        <div class="col-lg-9 col-md-9 col-sm-9 col-xs-12 pull-right">
            <div class="pull-right">
                <label>
                    <span>${_('Limit')}:</span>
                    <select name="history_limit" id="history_limit" class="form-control form-control-inline input-sm" title="Limit">
                        <option value="10" ${('', 'selected="selected"')[limit == 10]}>10</option>
                        <option value="25" ${('', 'selected="selected"')[limit == 25]}>25</option>
                        <option value="50" ${('', 'selected="selected"')[limit == 50]}>50</option>
                        <option value="100" ${('', 'selected="selected"')[limit == 100]}>100</option>
                        <option value="250" ${('', 'selected="selected"')[limit == 250]}>250</option>
                        <option value="500" ${('', 'selected="selected"')[limit == 500]}>500</option>
                        <option value="750" ${('', 'selected="selected"')[limit == 750]}>750</option>
                        <option value="1000" ${('', 'selected="selected"')[limit == 1000]}>1000</option>
                        <option value="0" ${('', 'selected="selected"')[limit == 0  ]}>All</option>
                    </select>
                    &nbsp;
                </label>
                <label>
                    <span> ${_('Layout')}:</span>
                    <select name="${_('HistoryLayout')}" class="form-control form-control-inline input-sm" onchange="location = this.options[this.selectedIndex].value;">
                        <option value="${srRoot}/setHistoryLayout/?layout=compact"  ${('', 'selected="selected"')[sickbeard.HISTORY_LAYOUT == 'compact']}>${_('Compact')}</option>
                        <option value="${srRoot}/setHistoryLayout/?layout=detailed" ${('', 'selected="selected"')[sickbeard.HISTORY_LAYOUT == 'detailed']}>${_('Detailed')}</option>
                    </select>
                </label>
            </div>
        </div>
        <div class="col-lg-3 col-md-3 col-sm-3 col-xs-12">
            % if not header is UNDEFINED:
                <h1 class="header">${header}</h1>
            % else:
                <h1 class="title">${title}</h1>
            % endif
        </div>
    </div>
    <div class="row">
        <div class="col-md-12">
            <div class="horizontal-scroll">
                <table id="historyTable" class="sickbeardTable tablesorter" cellspacing="1" border="0" cellpadding="0">
                    % if sickbeard.HISTORY_LAYOUT == "detailed":
                        <thead>
                            <tr>
                                <th class="nowrap">${_('Time')}</th>
                                <th>${_('Episode')}</th>
                                <th>${_('Action')}</th>
                                <th>${_('Provider')}</th>
                                <th>${_('Quality')}</th>
                                <th class="col-checkbox"><input type="checkbox" class="bulkCheck" id="removeCheck" /></th>
                            </tr>
                        </thead>
                        <tbody>
                            % for hItem in historyResults:
                            <% curStatus, curQuality = Quality.splitCompositeStatus(int(hItem[b"action"])) %>
                                <tr>
                                    <td align="center">
                                        <% airDate = sbdatetime.sbdatetime.sbfdatetime(datetime.datetime.strptime(str(hItem[b"date"]), History.date_format), show_seconds=True) %>
                                        <% isoDate = datetime.datetime.strptime(str(hItem[b"date"]), History.date_format).isoformat('T') %>
                                        <time datetime="${isoDate}" class="date">${airDate}</time>
                                    </td>
                                    <td class="tvShow" width="35%"><a href="${srRoot}/home/displayShow?show=${hItem[b"show_id"]}#S${hItem[b"season"]}E${hItem[b"episode"]}">${hItem[b"show_name"]} - ${"S%02i" % int(hItem[b"season"])}${"E%02i" % int(hItem[b"episode"])} ${('', '<span class="quality Proper">Proper</span>')[b"proper" in hItem[b"resource"].lower() or "repack" in hItem[b"resource"].lower()]}</a></td>
                                    <td align="center" ${('', 'class="subtitles_column"')[curStatus == SUBTITLED]}>
                                        % if curStatus == SUBTITLED:
                                            <img width="16" height="11" style="vertical-align:middle;" src="${ static_url('images/subtitles/flags/' + hItem[b'resource'] + '.png') }" onError="this.onerror=null;this.src='${ static_url('images/flags/unknown.png') }';">
                                        % endif
                                        <span style="cursor: help; vertical-align:middle;" title="${ek(os.path.basename, hItem[b'resource'])}">${statusStrings[curStatus]}</span>
                                    </td>
                                    <td align="center">
                                        % if curStatus in [DOWNLOADED, ARCHIVED]:
                                            % if hItem[b"provider"] != "-1":
                                                <span style="vertical-align:middle;"><i>${hItem[b"provider"]}</i></span>
                                            % else:
                                                <span style="vertical-align:middle;"><i>${_('Unknown')}</i></span>
                                            % endif
                                        % else:
                                            % if hItem[b"provider"] > 0:
                                                % if curStatus in [SNATCHED, FAILED]:
                                                    <% provider = providers.getProviderClass(GenericProvider.make_id(hItem[b"provider"])) %>
                                                    % if provider is not None:
                                                        <img src="${ static_url('images/providers/' + provider.image_name()) }" width="16" height="16" style="vertical-align:middle;" /> <span style="vertical-align:middle;">${provider.name}</span>
                                                    % else:
                                                        <img src="${ static_url('images/providers/missing.png') }" width="16" height="16" style="vertical-align:middle;" title="missing provider"/> <span style="vertical-align:middle;">${_('Missing Provider')}</span>
                                                    % endif
                                                % else:
                                                    <img src="${ static_url('images/subtitles/' + hItem[b'provider'] + '.png') }" width="16" height="16" style="vertical-align:middle;" /> <span style="vertical-align:middle;">${hItem[b"provider"].capitalize()}</span>
                                                % endif
                                            % endif
                                        % endif
                                    </td>
                                    <td align="center">
                                        <span style="display: none;">${curQuality}</span>
                                        ${renderQualityPill(curQuality)}
                                    </td>
                                    <td align="center">
                                        <% uniqueid = '-'.join([str(hItem[b"date"]), str(hItem[b"show_id"]), str(hItem[b'season']), str(hItem[b'episode'])]) %>
                                        <input type="checkbox" class="removeCheck" id="remove-${uniqueid}" />
                                    </td>
                                </tr>
                            % endfor
                        </tbody>
                        <tfoot>
                            <tr>
                                <th class="nowrap" colspan="6">&nbsp;</th>
                            </tr>
                        </tfoot>
                    % else:
                        <thead>
                            <tr>
                                <th class="nowrap">${_('Time')}</th>
                                <th>${_('Episode')}</th>
                                <th>${_('Snatched')}</th>
                                <th>${_('Downloaded')}</th>
                                % if sickbeard.USE_SUBTITLES:
                                    <th>${_('Subtitled')}</th>
                                % endif
                                <th>${_('Quality')}</th>
                                <th class="col-checkbox"><input type="checkbox" class="bulkCheck" id="removeCheck" /></th>
                            </tr>
                        </thead>
                        <tbody>
                            % for hItem in compactResults:
                                <tr>
                                    <td align="center">
                                        <% airDate = sbdatetime.sbdatetime.sbfdatetime(datetime.datetime.strptime(str(hItem[b"actions"][0][b"time"]), History.date_format), show_seconds=True) %>
                                        <% isoDate = datetime.datetime.strptime(str(hItem[b"actions"][0][b"time"]), History.date_format).isoformat('T') %>
                                        <time datetime="${isoDate}" class="date">${airDate}</time>
                                    </td>
                                    <td class="tvShow" width="25%">
                                        <span><a href="${srRoot}/home/displayShow?show=${hItem[b"show_id"]}#season-${hItem[b"season"]}">${hItem[b"show_name"]} - ${"S%02i" % int(hItem[b"season"])}${"E%02i" % int(hItem[b"episode"])}${('', ' <span class="quality Proper">Proper</span>')[b'proper' in hItem[b"resource"].lower() or 'repack' in hItem[b"resource"].lower()]}</a></span>
                                    </td>
                                    <td align="center" provider="${str(sorted(hItem[b"actions"])[0][b"provider"])}">
                                        % for action in sorted(hItem[b"actions"]):
                                            <% curStatus, curQuality = Quality.splitCompositeStatus(int(action[b"action"])) %>
                                            % if curStatus in [SNATCHED, FAILED]:
                                                <% provider = providers.getProviderClass(GenericProvider.make_id(action[b"provider"])) %>
                                                % if provider is not None:
                                                    <img src="${ static_url('images/providers/' + provider.image_name()) }" width="16" height="16" style="vertical-align:middle;" alt="${provider.name}" style="cursor: help;" title="${provider.name}: ${ek(os.path.basename, action[b"resource"])}"/>
                                                % else:
                                                    <img src="${ static_url('images/providers/missing.png') }" width="16" height="16" style="vertical-align:middle;" alt="${_('missing provider')}" title="${_('missing provider')}"/>
                                                % endif
                                            % endif
                                        % endfor
                                    </td>
                                    <td align="center">
                                        % for action in sorted(hItem[b"actions"]):
                                            <% curStatus, curQuality = Quality.splitCompositeStatus(int(action[b"action"])) %>
                                            % if curStatus in [DOWNLOADED, ARCHIVED]:
                                                % if action[b"provider"] != "-1":
                                                    <span style="cursor: help;" title="${ek(os.path.basename, action[b"resource"])}"><i>${action[b"provider"]}</i></span>
                                                % else:
                                                    <span style="cursor: help;" title="${ek(os.path.basename, action[b"resource"])}"><i>${_('Unknown')}</i></span>
                                                % endif
                                            % endif
                                        % endfor
                                    </td>
                                    % if sickbeard.USE_SUBTITLES:
                                        <td align="center">
                                            % for action in sorted(hItem[b"actions"]):
                                                <% curStatus, curQuality = Quality.splitCompositeStatus(int(action[b"action"])) %>
                                                % if curStatus == SUBTITLED:
                                                    <img src="${ static_url('images/subtitles/' + action[b'provider'] + '.png') }" width="16" height="16" style="vertical-align:middle;" alt="${action[b"provider"]}" title="${action[b"provider"].capitalize()}: ${ek(os.path.basename, action[b"resource"])}"/>
                                                    <span style="vertical-align:middle;"> / </span>
                                                    <img width="16" height="11" style="vertical-align:middle !important;" src="${ static_url('images/subtitles/flags/' + action[b'resource'] + '.png') }" onError="this.onerror=null;this.src='${ static_url('images/flags/unknown.png') }';">
                                                    &nbsp;
                                                % endif
                                            % endfor
                                        </td>
                                    % endif
                                    <td align="center" width="14%" quality="${curQuality}">${renderQualityPill(curQuality)}</td>
                                    <%
                                        dates = str(hItem[b"actions"][0][b"time"])
                                        for action in hItem[b"actions"][1:]:
                                            dates = '$'.join([dates, str(action[b"time"])])
                                        uniqueid = '-'.join([dates, str(hItem[b"show_id"]), str(hItem[b'season']), str(hItem[b'episode'])])
                                    %>
                                    <td align="center"><input type="checkbox" class="removeCheck" id="remove-${uniqueid}" /></td>
                                </tr>
                            % endfor
                        </tbody>
                        <tfoot>
                            <tr>
                                <th class="nowrap" colspan="7">&nbsp;</th>
                            </tr>
                        </tfoot>
                    % endif
                </table>
            </div>
        </div>
    </div>
</%block>
