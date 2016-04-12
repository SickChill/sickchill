<%inherit file="/layouts/main.mako"/>
<%!
    import sickbeard
    from sickbeard.common import statusStrings
%>
<%block name="scripts">
<script type="text/javascript" src="${srRoot}/js/massUpdate.js?${sbPID}"></script>
</%block>
<%block name="content">
<%namespace file="/inc_defs.mako" import="renderQualityPill"/>

<form name="massUpdateForm" method="post" action="massUpdate">
<table style="width: 100%;" class="home-header">
    <tr>
        <td nowrap>
            % if not header is UNDEFINED:
            <h1 class="header" style="margin: 0;">${header}</h1>
            % else:
            <h1 class="title" style="margin: 0;">${title}</h1>
            % endif
        </td>
        <td align="right">
            <div>
                <input class="btn btn-inline submitMassEdit" type="button" value="${_('Edit Selected')}" />
                <input class="btn btn-inline submitMassUpdate" type="button" value="${_('Submit')}" />
                <span class="show-option">
                    <button id="popover" type="button" class="btn btn-inline">${_('Select Columns')} <b class="caret"></b></button>
                </span>
                <span class="show-option">
                    <button type="button" class="resetsorting btn btn-inline">${_('Clear Filter(s)')}</button>
                </span>
            </div>
        </td>
    </tr>
</table>

<table id="massUpdateTable" class="tablesorter" cellspacing="1" border="0" cellpadding="0">
    <thead>
        <tr>
            <th class="col-checkbox">${_('Edit')}<br><input type="checkbox" class="bulkCheck" id="editCheck" /></th>
            <th class="nowrap" style="text-align: left;">${_('Show Name')}</th>
            <th class="col-quality">${_('Quality')}</th>
            <th class="col-legend">${_('Sports')}</th>
            <th class="col-legend">${_('Scene')}</th>
            <th class="col-legend">${_('Anime')}</th>
            <th class="col-legend">${_('Season folders')}</th>
            <th class="col-legend">${_('Paused')}</th>
            <th class="col-legend">${_('Subtitle')}</th>
            <th class="col-legend">${_('Default Ep Status')}</th>
            <th class="col-legend">${_('Status')}</th>
            <th width="1%">${_('Update')}<br><input type="checkbox" class="bulkCheck" id="updateCheck" /></th>
            <th width="1%">${_('Rescan')}<br><input type="checkbox" class="bulkCheck" id="refreshCheck" /></th>
            <th width="1%">${_('Rename')}<br><input type="checkbox" class="bulkCheck" id="renameCheck" /></th>
        % if sickbeard.USE_SUBTITLES:
            <th width="1%">${_('Search Subtitle')}<br><input type="checkbox" class="bulkCheck" id="subtitleCheck" /></th>
        % endif
            <!-- <th>${_('Force Metadata Regen')} <input type="checkbox" class="bulkCheck" id="metadataCheck" /></th>//-->
            <th width="1%">${_('Delete')}<br><input type="checkbox" class="bulkCheck" id="deleteCheck" /></th>
            <th width="1%">${_('Remove')}<br><input type="checkbox" class="bulkCheck" id="removeCheck" /></th>
        </tr>
    </thead>
    <tfoot>
        <tr>
            <td rowspan="1" colspan="2" class="align-center alt"><input class="btn pull-left submitMassEdit" type="button" value="${_('Edit Selected')}" /></td>
            <td rowspan="1" colspan="${(15, 16)[bool(sickbeard.USE_SUBTITLES)]}" class="align-right alt"><input class="btn pull-right submitMassUpdate" type="button" value="${_('Submit')}" /></td>
        </tr>
    </tfoot>

    <tbody>
<%
    my_show_list = sickbeard.showList
    my_show_list.sort(lambda x, y: cmp(x.name, y.name))
%>
    % for cur_show in my_show_list:
    <%
        disabled = sickbeard.show_queue_scheduler.action.isBeingUpdated(cur_show) or sickbeard.show_queue_scheduler.action.isInUpdateQueue(cur_show)
        cur_update = "<input type=\"checkbox\" class=\"updateCheck\" id=\"update-" + str(cur_show.indexerid) + "\" " + ("", "disabled=\"disabled\" ")[disabled] + "/>"

        disabled = sickbeard.show_queue_scheduler.action.isBeingRefreshed(cur_show) or sickbeard.show_queue_scheduler.action.isInRefreshQueue(cur_show)
        cur_resfresh = "<input type=\"checkbox\" class=\"refreshCheck\" id=\"refresh-" + str(cur_show.indexerid) + "\" " + ("", "disabled=\"disabled\" ")[disabled] + "/>"

        disabled = sickbeard.show_queue_scheduler.action.isBeingRenamed(cur_show) or sickbeard.show_queue_scheduler.action.isInRenameQueue(cur_show)
        cur_rename = "<input type=\"checkbox\" class=\"renameCheck\" id=\"rename-" + str(cur_show.indexerid) + "\" " + ("", "disabled=\"disabled\" ")[disabled] + "/>"

        disabled = not cur_show.subtitles or sickbeard.show_queue_scheduler.action.isBeingSubtitled(cur_show) or sickbeard.show_queue_scheduler.action.isInSubtitleQueue(cur_show)
        cur_subtitle = "<input type=\"checkbox\" class=\"subtitleCheck\" id=\"subtitle-" + str(cur_show.indexerid) + "\" " + ("", "disabled=\"disabled\" ")[disabled] + "/>"

        disabled = sickbeard.show_queue_scheduler.action.isBeingRenamed(cur_show) or sickbeard.show_queue_scheduler.action.isInRenameQueue(cur_show) or sickbeard.show_queue_scheduler.action.isInRefreshQueue(cur_show)
        cur_delete = "<input type=\"checkbox\" class=\"confirm deleteCheck\" id=\"delete-" + str(cur_show.indexerid) + "\" " + ("", "disabled=\"disabled\" ")[disabled] + "/>"

        disabled = sickbeard.show_queue_scheduler.action.isBeingRenamed(cur_show) or sickbeard.show_queue_scheduler.action.isInRenameQueue(cur_show) or sickbeard.show_queue_scheduler.action.isInRefreshQueue(cur_show)
        cur_remove = "<input type=\"checkbox\" class=\"removeCheck\" id=\"remove-" + str(cur_show.indexerid) + "\" " + ("", "disabled=\"disabled\" ")[disabled] + "/>"
    %>
    <tr>
        <td align="center"><input type="checkbox" class="editCheck" id="edit-${cur_show.indexerid}" /></td>
        <td class="tvShow"><a href="${srRoot}/home/displayShow?show=${cur_show.indexerid}">${cur_show.name}</a></td>
        <td align="center">${renderQualityPill(cur_show.quality, showTitle=True)}</td>
        <td align="center"><img src="${srRoot}/images/${('no16.png" alt="N"', 'yes16.png" alt="Y"')[int(cur_show.is_sports) == 1]} width="16" height="16" /></td>
        <td align="center"><img src="${srRoot}/images/${('no16.png" alt="N"', 'yes16.png" alt="Y"')[int(cur_show.is_scene) == 1]} width="16" height="16" /></td>
        <td align="center"><img src="${srRoot}/images/${('no16.png" alt="N"', 'yes16.png" alt="Y"')[int(cur_show.is_anime) == 1]} width="16" height="16" /></td>
        <td align="center"><img src="${srRoot}/images/${('no16.png" alt="N"', 'yes16.png" alt="Y"')[not int(cur_show.flatten_folders) == 1]} width="16" height="16" /></td>
        <td align="center"><img src="${srRoot}/images/${('no16.png" alt="N"', 'yes16.png" alt="Y"')[int(cur_show.paused) == 1]} width="16" height="16" /></td>
        <td align="center"><img src="${srRoot}/images/${('no16.png" alt="N"', 'yes16.png" alt="Y"')[int(cur_show.subtitles) == 1]} width="16" height="16" /></td>
        <td align="center">${statusStrings[cur_show.default_ep_status]}</td>
        <td align="center">${_(cur_show.status)}</td>
        <td align="center">${cur_update}</td>
        <td align="center">${cur_resfresh}</td>
        <td align="center">${cur_rename}</td>
        % if sickbeard.USE_SUBTITLES:
        <td align="center">${cur_subtitle}</td>
        % endif
        <td align="center">${cur_delete}</td>
        <td align="center">${cur_remove}</td>
    </tr>
% endfor
</tbody>
</table>
</form>
</%block>
