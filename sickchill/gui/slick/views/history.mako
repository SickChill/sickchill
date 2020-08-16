<%inherit file="/layouts/main.mako"/>
<%!
    import os.path
    import datetime

    from sickchill.oldbeard import sbdatetime, providers

    from sickchill.oldbeard.common import ARCHIVED, SNATCHED, FAILED, DOWNLOADED, SUBTITLED
    from sickchill.oldbeard.common import Quality, statusStrings

    from sickchill.show.History import History
    from sickchill.providers.GenericProvider import GenericProvider
    from sickchill import settings

    from operator import itemgetter
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
                    <select id="layout" class="form-control form-control-inline input-sm">
                        <option value="${scRoot}/setHistoryLayout/?layout=compact"  ${('', 'selected="selected"')[settings.HISTORY_LAYOUT == 'compact']}>${_('Compact')}</option>
                        <option value="${scRoot}/setHistoryLayout/?layout=detailed" ${('', 'selected="selected"')[settings.HISTORY_LAYOUT == 'detailed']}>${_('Detailed')}</option>
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
                <table id="historyTable" class="sickchillTable tablesorter">
                    % if settings.HISTORY_LAYOUT == "detailed":
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
                            <% curStatus, curQuality = Quality.splitCompositeStatus(int(hItem["action"])) %>
                                <tr>
                                    <td align="center">
                                        <%
                                            # noinspection PyCallByClass
                                            airDate = sbdatetime.sbdatetime.sbfdatetime(datetime.datetime.strptime(str(hItem["date"]), History.date_format), show_seconds=True)
                                            isoDate = datetime.datetime.strptime(str(hItem["date"]), History.date_format).isoformat()
                                        %>
                                        <time datetime="${isoDate}" class="date">${airDate}</time>
                                    </td>
                                    <td class="tvShow" width="35%"><a href="${scRoot}/home/displayShow?show=${hItem["show_id"]}#S${hItem["season"]}E${hItem["episode"]}">
                                        ${"{} - S{:02}E{:02}".format(hItem["show_name"], int(hItem["season"]), int(hItem["episode"]))} ${('', '<span class="quality Proper">Proper</span>')["proper" in hItem["resource"].lower() or "repack" in hItem["resource"].lower()]}
                                    </a></td>
                                    <td align="center" ${('', 'class="subtitles_column"')[curStatus == SUBTITLED]}>
                                        % if curStatus == SUBTITLED:
                                            <img width="16" height="11" style="vertical-align:middle;" src="${static_url('images/subtitles/flags/' + hItem['resource'] + '.png') }" onError="this.onerror=null;this.src='${ static_url('images/flags/unknown.png')}';">
                                        % endif
                                        <span style="cursor: help; vertical-align:middle;" title="${os.path.basename(hItem['resource'])}">${statusStrings[curStatus]}</span>
                                    </td>
                                    <td align="center">
                                        % if curStatus in [DOWNLOADED, ARCHIVED]:
                                            % if hItem["provider"] != "-1":
                                                <span style="vertical-align:middle;"><i>${hItem["provider"]}</i></span>
                                            % else:
                                                <span style="vertical-align:middle;"><i>${_('Unknown')}</i></span>
                                            % endif
                                        % else:
                                            % if hItem["provider"]:
                                                % if curStatus in [SNATCHED, FAILED]:
                                                    <% provider = providers.getProviderClass(GenericProvider.make_id(hItem["provider"])) %>
                                                    % if provider is not None:
                                                        <img src="${static_url('images/providers/' + provider.image_name())}" width="16" height="16" style="vertical-align:middle;" /> <span style="vertical-align:middle;">${provider.name}</span>
                                                    % else:
                                                        <img src="${static_url('images/providers/missing.png')}" width="16" height="16" style="vertical-align:middle;" title="missing provider"/> <span style="vertical-align:middle;">${_('Missing Provider')}</span>
                                                    % endif
                                                % else:
                                                    <img src="${static_url('images/subtitles/' + hItem['provider'] + '.png')}" width="16" height="16" style="vertical-align:middle;" /> <span style="vertical-align:middle;">${hItem["provider"].capitalize()}</span>
                                                % endif
                                            % endif
                                        % endif
                                    </td>
                                    <td align="center">
                                        <span style="display: none;">${curQuality}</span>
                                        ${renderQualityPill(curQuality)}
                                    </td>
                                    <td align="center">
                                        <% uniqueid = '-'.join([str(hItem["date"]), str(hItem["show_id"]), str(hItem['season']), str(hItem['episode'])]) %>
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
                                % if settings.USE_SUBTITLES:
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
                                        <%
                                            # noinspection PyCallByClass
                                            airDate = sbdatetime.sbdatetime.sbfdatetime(datetime.datetime.strptime(str(hItem["actions"][0]["time"]), History.date_format), show_seconds=True)
                                            isoDate = datetime.datetime.strptime(str(hItem["actions"][0]["time"]), History.date_format).isoformat('T')
                                        %>
                                        <time datetime="${isoDate}" class="date">${airDate}</time>
                                    </td>
                                    <td class="tvShow" width="25%">
                                        <span>
                                            <a href="${scRoot}/home/displayShow?show=${hItem["show_id"]}#season-${hItem["season"]}">
                                                ${"{} - S{:02}E{:02}".format(hItem["show_name"], int(hItem["season"]), int(hItem["episode"]))}${('', ' <span class="quality Proper">Proper</span>')['proper' in hItem["resource"].lower() or 'repack' in hItem["resource"].lower()]}
                                            </a>
                                        </span>
                                    </td>
                                    <td align="center" provider="${str(sorted(hItem["actions"], key=itemgetter('provider'))[0]["provider"])}">
                                        % for action in sorted(hItem["actions"], key=itemgetter('provider')):
                                            <% curStatus, curQuality = Quality.splitCompositeStatus(int(action["action"])) %>
                                            % if curStatus in [SNATCHED, FAILED]:
                                                <% provider = providers.getProviderClass(GenericProvider.make_id(action["provider"])) %>
                                                % if provider is not None:
                                                    <img src="${static_url('images/providers/' + provider.image_name())}" width="16" height="16"
                                                         style="vertical-align:middle;" alt="${provider.name}" style="cursor: help;" title="${provider.name}: ${os.path.basename(action["resource"])}"/>
                                                % else:
                                                    <img src="${static_url('images/providers/missing.png')}" width="16" height="16" style="vertical-align:middle;" alt="${_('missing provider')}" title="${_('missing provider')}"/>
                                                % endif
                                            % endif
                                        % endfor
                                    </td>
                                    <td align="center">
                                        % for action in sorted(hItem["actions"], key=itemgetter('provider')):
                                            <% curStatus, curQuality = Quality.splitCompositeStatus(int(action["action"])) %>
                                            % if curStatus in [DOWNLOADED, ARCHIVED]:
                                                % if action["provider"] != "-1":
                                                    <span style="cursor: help;" title="${os.path.basename(action["resource"])}"><i>${action["provider"]}</i></span>
                                                % else:
                                                    <span style="cursor: help;" title="${os.path.basename(action["resource"])}"><i>${_('Unknown')}</i></span>
                                                % endif
                                            % endif
                                        % endfor
                                    </td>
                                    % if settings.USE_SUBTITLES:
                                        <td align="center">
                                            % for action in sorted(hItem["actions"], key=itemgetter('provider')):
                                                <% curStatus, curQuality = Quality.splitCompositeStatus(int(action["action"])) %>
                                                % if curStatus == SUBTITLED:
                                                    <img src="${static_url('images/subtitles/' + action['provider'] + '.png')}" width="16" height="16"
                                                         style="vertical-align:middle;" alt="${action["provider"]}" title="${action["provider"].capitalize()}: ${os.path.basename(action["resource"])}"/>
                                                    <span style="vertical-align:middle;"> / </span>
                                                    <img width="16" height="11" style="vertical-align:middle !important;" src="${static_url('images/subtitles/flags/' + action['resource'] + '.png') }" onError="this.onerror=null;this.src='${ static_url('images/flags/unknown.png')}';">
                                                    &nbsp;
                                                % endif
                                            % endfor
                                        </td>
                                    % endif
                                    <td align="center" width="14%" quality="${curQuality}">${renderQualityPill(curQuality)}</td>
                                    <%
                                        dates = str(hItem["actions"][0]["time"])
                                        for action in hItem["actions"][1:]:
                                            dates = '$'.join([dates, str(action["time"])])
                                        uniqueid = '-'.join([dates, str(hItem["show_id"]), str(hItem['season']), str(hItem['episode'])])
                                    %>
                                    <td align="center"><input type="checkbox" class="removeCheck" id="remove-${uniqueid}" /></td>
                                </tr>
                            % endfor
                        </tbody>
                        <tfoot>
                            <tr>
                                <th class="nowrap" colspan="${("6", "7")[settings.USE_SUBTITLES]}">&nbsp;</th>
                            </tr>
                        </tfoot>
                    % endif
                </table>
            </div>
        </div>
    </div>
</%block>
