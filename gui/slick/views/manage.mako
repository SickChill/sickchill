<%inherit file="/layouts/main.mako"/>
<%!
    import sickbeard
    from sickbeard.common import SKIPPED, WANTED, UNAIRED, ARCHIVED, IGNORED, SNATCHED, SNATCHED_PROPER, SNATCHED_BEST, FAILED
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
                <input class="btn btn-inline submitMassEdit" type="button" value="Edit Selected" />
                <input class="btn btn-inline submitMassUpdate" type="button" value="Submit" />
                <span class="show-option">
                    <button id="popover" type="button" class="btn btn-inline">Select Columns <b class="caret"></b></button>
                </span>
                <span class="show-option">
                    <button type="button" class="resetsorting btn btn-inline">Clear Filter(s)</button>
                </span>
            </div>
        </td>
    </tr>
</table>

<table id="massUpdateTable" class="tablesorter" cellspacing="1" border="0" cellpadding="0">
    <thead>
        <tr>
            <th class="col-checkbox">Edit<br><input type="checkbox" class="bulkCheck" id="editCheck" /></th>
            <th class="nowrap" style="text-align: left;">Show Name</th>
            <th class="col-quality">Quality</th>
            <th class="col-legend">Sports</th>
            <th class="col-legend">Scene</th>
            <th class="col-legend">Anime</th>
            <th class="col-legend">Season folders</th>
            <th class="col-legend">Paused</th>
            <th class="col-legend">Subtitle</th>
            <th class="col-legend">Default Ep Status</th>
            <th class="col-legend">Status</th>
            <th width="1%">Update<br><input type="checkbox" class="bulkCheck" id="updateCheck" /></th>
            <th width="1%">Rescan<br><input type="checkbox" class="bulkCheck" id="refreshCheck" /></th>
            <th width="1%">Rename<br><input type="checkbox" class="bulkCheck" id="renameCheck" /></th>
        % if sickbeard.USE_SUBTITLES:
            <th width="1%">Search Subtitle<br><input type="checkbox" class="bulkCheck" id="subtitleCheck" /></th>
        % endif
            <!-- <th>Force Metadata Regen <input type="checkbox" class="bulkCheck" id="metadataCheck" /></th>//-->
            <th width="1%">Delete<br><input type="checkbox" class="bulkCheck" id="deleteCheck" /></th>
            <th width="1%">Remove<br><input type="checkbox" class="bulkCheck" id="removeCheck" /></th>
        </tr>
    </thead>
    <tfoot>
        <tr>
            <td rowspan="1" colspan="2" class="align-center alt"><input class="btn pull-left submitMassEdit" type="button" value="Edit Selected" /></td>
            <td rowspan="1" colspan="${(15, 16)[bool(sickbeard.USE_SUBTITLES)]}" class="align-right alt"><input class="btn pull-right submitMassUpdate" type="button" value="Submit" /></td>
        </tr>
    </tfoot>

    <tbody>
<%
    myShowList = sickbeard.showList
    myShowList.sort(lambda x, y: cmp(x.name, y.name))
%>
    % for curShow in myShowList:
    <%
        curEp = curShow.nextaired

        disabled = sickbeard.showQueueScheduler.action.isBeingUpdated(curShow) or sickbeard.showQueueScheduler.action.isInUpdateQueue(curShow)
        curUpdate = "<input type=\"checkbox\" class=\"updateCheck\" id=\"update-" + str(curShow.indexerid) + "\" " + ("", "disabled=\"disabled\" ")[disabled] + "/>"

        disabled = sickbeard.showQueueScheduler.action.isBeingRefreshed(curShow) or sickbeard.showQueueScheduler.action.isInRefreshQueue(curShow)
        curRefresh = "<input type=\"checkbox\" class=\"refreshCheck\" id=\"refresh-" + str(curShow.indexerid) + "\" " + ("", "disabled=\"disabled\" ")[disabled] + "/>"

        disabled = sickbeard.showQueueScheduler.action.isBeingRenamed(curShow) or sickbeard.showQueueScheduler.action.isInRenameQueue(curShow)
        curRename = "<input type=\"checkbox\" class=\"renameCheck\" id=\"rename-" + str(curShow.indexerid) + "\" " + ("", "disabled=\"disabled\" ")[disabled] + "/>"

        disabled = not curShow.subtitles or sickbeard.showQueueScheduler.action.isBeingSubtitled(curShow) or sickbeard.showQueueScheduler.action.isInSubtitleQueue(curShow)
        curSubtitle = "<input type=\"checkbox\" class=\"subtitleCheck\" id=\"subtitle-" + str(curShow.indexerid) + "\" " + ("", "disabled=\"disabled\" ")[disabled] + "/>"

        disabled = sickbeard.showQueueScheduler.action.isBeingRenamed(curShow) or sickbeard.showQueueScheduler.action.isInRenameQueue(curShow) or sickbeard.showQueueScheduler.action.isInRefreshQueue(curShow)
        curDelete = "<input type=\"checkbox\" class=\"confirm deleteCheck\" id=\"delete-" + str(curShow.indexerid) + "\" " + ("", "disabled=\"disabled\" ")[disabled] + "/>"

        disabled = sickbeard.showQueueScheduler.action.isBeingRenamed(curShow) or sickbeard.showQueueScheduler.action.isInRenameQueue(curShow) or sickbeard.showQueueScheduler.action.isInRefreshQueue(curShow)
        curRemove = "<input type=\"checkbox\" class=\"removeCheck\" id=\"remove-" + str(curShow.indexerid) + "\" " + ("", "disabled=\"disabled\" ")[disabled] + "/>"
    %>
    <tr>
        <td align="center"><input type="checkbox" class="editCheck" id="edit-${curShow.indexerid}" /></td>
        <td class="tvShow"><a href="${srRoot}/home/displayShow?show=${curShow.indexerid}">${curShow.name}</a></td>
        <td align="center">${renderQualityPill(curShow.quality, showTitle=True)}</td>
        <td align="center"><img src="${srRoot}/images/${('no16.png" alt="N"', 'yes16.png" alt="Y"')[int(curShow.is_sports) == 1]} width="16" height="16" /></td>
        <td align="center"><img src="${srRoot}/images/${('no16.png" alt="N"', 'yes16.png" alt="Y"')[int(curShow.is_scene) == 1]} width="16" height="16" /></td>
        <td align="center"><img src="${srRoot}/images/${('no16.png" alt="N"', 'yes16.png" alt="Y"')[int(curShow.is_anime) == 1]} width="16" height="16" /></td>
        <td align="center"><img src="${srRoot}/images/${('no16.png" alt="N"', 'yes16.png" alt="Y"')[not int(curShow.flatten_folders) == 1]} width="16" height="16" /></td>
        <td align="center"><img src="${srRoot}/images/${('no16.png" alt="N"', 'yes16.png" alt="Y"')[int(curShow.paused) == 1]} width="16" height="16" /></td>
        <td align="center"><img src="${srRoot}/images/${('no16.png" alt="N"', 'yes16.png" alt="Y"')[int(curShow.subtitles) == 1]} width="16" height="16" /></td>
        <td align="center">${statusStrings[curShow.default_ep_status]}</td>
        <td align="center">${curShow.status}</td>
        <td align="center">${curUpdate}</td>
        <td align="center">${curRefresh}</td>
        <td align="center">${curRename}</td>
        % if sickbeard.USE_SUBTITLES:
        <td align="center">${curSubtitle}</td>
        % endif
        <td align="center">${curDelete}</td>
        <td align="center">${curRemove}</td>
    </tr>
% endfor
</tbody>
</table>
</form>
</%block>
