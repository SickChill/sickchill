<%inherit file="/layouts/main.mako" />
<%!
    import os.path
    import datetime

    from sickchill.oldbeard import scdatetime, providers

    from sickchill.oldbeard.common import ARCHIVED, SNATCHED, FAILED, DOWNLOADED, SUBTITLED
    from sickchill.oldbeard.common import Quality, statusStrings

    from sickchill.show.History import History
    from sickchill.providers.GenericProvider import GenericProvider
    from sickchill import settings

    from operator import itemgetter
%>
<%block name="content">
    <%namespace file="/inc_defs.mako" import="renderQualityPill" />
    <div class="row">
        <div class="col-lg-9 col-md-9 col-sm-9 col-xs-12 pull-right">
            <div class="pull-right">
                <label>
                    <span>${_('Limit')}:</span>
                    <select name="history_limit" id="history_limit" class="form-control form-control-inline input-sm" title="Limit">
                        % for val in [10, 25, 50, 100, 250, 500, 750, 1000, 0]:
                            <option value="${val}" ${selected(limit == val)}>${(val, _("All"))[val == 0]}</option>
                        % endfor
                    </select>
                    &nbsp
                </label>
                <label>
                    <span> ${_('Layout')}:</span>
                    <select id="layout" class="form-control form-control-inline input-sm">
                        % for layout in ['compact', 'detailed']:
                            <option class="text-capitalize" value="${scRoot}/setHistoryLayout/?layout=${layout}" ${selected(layout == settings.HISTORY_LAYOUT)}>${_(layout)}</option>
                        % endfor
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
                    % if settings.HISTORY_LAYOUT == 'detailed':
                        <thead>
                        <tr>
                            <th class="nowrap">${_('Time')}</th>
                            <th>${_('Episode')}</th>
                            <th>${_('Action')}</th>
                            <th>${_('Provider')}</th>
                            <th>${_('Quality')}</th>
                            <th class="col-checkbox"><input type="checkbox" class="bulkCheck" id="removeCheck" aria-label="column check" /></th>
                        </tr>
                        </thead>
                        <tbody>
                            % for hItem in historyResults:
                                <% curStatus, curQuality = Quality.splitCompositeStatus(int(hItem['action'])) %>
                                <tr>
                                    <td class="text-center align-middle">
                                        <%
                                            # noinspection PyCallByClass
                                            air_date = scdatetime.scdatetime.scfdatetime(datetime.datetime.strptime(str(hItem['date']), History.date_format), show_seconds=True)
                                            isoDate = datetime.datetime.strptime(str(hItem['date']), History.date_format).isoformat()
                                        %>
                                        <time datetime="${isoDate}" class="date">${air_date}</time>
                                    </td>
                                    <td class="tvShow text-center align-middle col-md-3"><a href="${scRoot}/home/displayShow?show=${hItem['show_id']}#S${hItem['season']}E${hItem['episode']}">
                                        ${"{} - S{:02}E{:02}".format(hItem['show_name'], int(hItem['season']), int(hItem['episode']))} ${('', '<span class="quality Proper">Proper</span>')["proper" in hItem['resource'].lower() or "repack" in hItem['resource'].lower()]}
                                    </a></td>
                                    <td class="text-center align-middle" ${('', 'class="subtitles_column"')[curStatus == SUBTITLED]}>
                                        % if curStatus == SUBTITLED:
                                            <img width="16" height="11" class="align-middle text-center" src="${static_url('images/subtitles/flags/' + hItem['resource'] + '.png') }" onError="this.onerror=null;this.src='${ static_url('images/flags/unknown.png')}';">
                                        % endif
                                        <span style="cursor: help; vertical-align:middle;" title="${os.path.basename(hItem['resource'])}">${statusStrings[curStatus]}</span>
                                    </td>
                                    <td class="text-center align-middle">
                                        % if curStatus in [DOWNLOADED, ARCHIVED]:
                                            % if hItem['provider'] != '-1':
                                                <span class="align-middle text-center"><i>${hItem['provider']}</i></span>
                                            % else:
                                                <span class="align-middle text-center"><i>${_('Unknown')}</i></span>
                                            % endif
                                        % elif hItem['provider'] and curStatus in [SNATCHED, FAILED]:
                                            <% provider = providers.getProviderClass(GenericProvider.make_id(hItem['provider'])) %>
                                            % if provider is not None:
                                                <img src="${static_url('images/providers/' + provider.image_name())}" width="16" height="16" class="align-middle text-center" /> <span class="align-middle text-center">${provider.name}</span>
                                            % else:
                                                <img src="${static_url('images/providers/missing.png')}" width="16" height="16" class="align-middle text-center" title="missing provider" /> <span class="align-middle text-center">${_('Missing Provider')}</span>
                                            % endif
                                        % else:
                                            <img src="${static_url('images/subtitles/' + hItem['provider'] + '.png')}" width="16" height="16" class="align-middle text-center" /> <span class="align-middle text-center text-capitalize">${hItem['provider']}</span>
                                        % endif
                                    </td>
                                    <td class="text-center align-top col-md-1 word-wrap">
                                        ${renderQualityPill(curQuality)}
                                    </td>
                                    <td class="text-center align-middle">
                                        <% uniqueid = '-'.join([str(hItem['date']), str(hItem['show_id']), str(hItem['season']), str(hItem['episode'])]) %>
                                        <input type="checkbox" class="removeCheck text-center align-middle" id="remove-${uniqueid}" />
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
                            <th class="col-checkbox" class="text-center align-middle"><input type="checkbox" class="bulkCheck" id="removeCheck" /></th>
                        </tr>
                        </thead>
                        <tbody>
                            % for hItem in compactResults:
                                <tr>
                                    <td class="text-center align-middle">
                                        <%
                                            # noinspection PyCallByClass
                                            air_date = scdatetime.scdatetime.scfdatetime(datetime.datetime.strptime(str(hItem['actions'][0]['time']), History.date_format), show_seconds=True)
                                            isoDate = datetime.datetime.strptime(str(hItem['actions'][0]['time']), History.date_format).isoformat('T')
                                        %>
                                        <time datetime="${isoDate}" class="date">${air_date}</time>
                                    </td>
                                    <td class="tvShow align-middle text-center col-md-3">
                                        <span>
                                            <a href="${scRoot}/home/displayShow?show=${hItem['show_id']}#season-${hItem['season']}">
                                                ${"{} - S{:02}E{:02}".format(hItem['show_name'], int(hItem['season']), int(hItem['episode']))}${('', ' <span class="quality Proper">Proper</span>')['proper' in hItem['resource'].lower() or 'repack' in hItem['resource'].lower()]}
                                            </a>
                                        </span>
                                    </td>
                                    <td class="text-center align-middle">
                                        % for action in sorted(hItem['actions'], key=itemgetter('provider')):
                                            <% curStatus, curQuality = Quality.splitCompositeStatus(int(action['action'])) %>
                                            % if curStatus in [SNATCHED, FAILED, DOWNLOADED, ARCHIVED]:
                                                <% provider = providers.getProviderClass(GenericProvider.make_id(action['provider'])) %>
                                                % if provider is not None:
                                                    <img src="${static_url('images/providers/' + provider.image_name())}" width="16" height="16"
                                                         class="align-middle text-center" alt="${provider.name}" style="cursor: help;" title="${provider.name}: ${os.path.basename(action['resource'])}" />
                                                % else:
                                                    <img src="${static_url('images/providers/missing.png')}" width="16" height="16"
                                                         class="align-middle text-center"  alt="${_('missing provider')}" title="${_('missing provider')}" />
                                                % endif
                                            % endif
                                        % endfor
                                    </td>
                                    <td class="text-center align-middle">
                                        % for action in sorted(hItem['actions'], key=itemgetter('provider')):
                                            <% curStatus, curQuality = Quality.splitCompositeStatus(int(action['action'])) %>
                                            % if curStatus in [DOWNLOADED, ARCHIVED]:
                                                % if action['provider'] != '-1':
                                                    <span style="cursor: help;" title="${os.path.basename(action['resource'])}"><i>${action['provider']}</i></span>
                                                % else:
                                                    <span style="cursor: help;" title="${os.path.basename(action['resource'])}"><i>${_('Unknown')}</i></span>
                                                % endif
                                            % endif
                                        % endfor
                                    </td>
                                    % if settings.USE_SUBTITLES:
                                        <td class="text-center align-middle">
                                            % for action in sorted(hItem['actions'], key=itemgetter('provider')):
                                                <% curStatus, curQuality = Quality.splitCompositeStatus(int(action['action'])) %>
                                                % if curStatus == SUBTITLED:
                                                    <img src="${static_url('images/subtitles/' + action['provider'] + '.png')}" width="16" height="16"
                                                         class="align-middle text-center text-capitalize" alt="${action['provider']}" title="${action['provider']}: ${os.path.basename(action['resource'])}" />
                                                    <span class="align-middle text-center"> / </span>
                                                    <img width="16" height="11" style="vertical-align:middle !important;" src="${static_url('images/subtitles/flags/' + action['resource'] + '.png') }" onError="this.onerror=null;this.src='${ static_url('images/flags/unknown.png')}';">
                                                    &nbsp;
                                                % endif
                                            % endfor
                                        </td>
                                    % endif
                                    <td class="text-center align-top col-md-1 word-wrap">${renderQualityPill(curQuality)}</td>
                                    <%
                                        dates = str(hItem['actions'][0]['time'])
                                        for action in hItem['actions'][1:]:
                                            dates = '$'.join([dates, str(action['time'])])
                                        uniqueid = '-'.join([dates, str(hItem['show_id']), str(hItem['season']), str(hItem['episode'])])
                                    %>
                                    <td class="text-center align-middle"><input type="checkbox" class="removeCheck" id="remove-${uniqueid}" aria-label="remove checkbox" /></td>
                                </tr>
                            % endfor
                        </tbody>
                        <tfoot>
                        <tr>
                            <th class="nowrap" colspan="${('6', '7')[settings.USE_SUBTITLES]}">&nbsp;</th>
                        </tr>
                        </tfoot>
                    % endif
                </table>
            </div>
        </div>
    </div>
</%block>
