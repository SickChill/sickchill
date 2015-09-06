<%inherit file="/layouts/main.mako"/>
<%!
    import sickbeard
    from sickbeard.common import SKIPPED, WANTED, UNAIRED, ARCHIVED, IGNORED, SNATCHED, SNATCHED_PROPER, SNATCHED_BEST, FAILED
    from sickbeard.common import statusStrings
%>
<%block name="scripts">
<script type="text/javascript" src="${sbRoot}/js/lib/bootbox.min.js?${sbPID}"></script>
<script type="text/javascript" charset="utf-8">
$.tablesorter.addParser({
    id: 'showNames',
    is: function(s) {
        return false;
    },
    format: function(s) {
        % if not sickbeard.SORT_ARTICLE:
            return (s || '').replace(/^(The|A|An)\s/i,'');
        % else:
            return (s || '');
        % endif
    },
    type: 'text'
});
$.tablesorter.addParser({
    id: 'quality',
    is: function(s) {
        return false;
    },
    format: function(s) {
        return s.replace('hd1080p',5).replace('hd720p',4).replace('hd',3).replace('sd',2).replace('any',1).replace('best',0).replace('custom',7);
    },
    type: 'numeric'
});

$(document).ready(function(){
    $("#massUpdateTable:has(tbody tr)").tablesorter({
        sortList: [[1,0]],
        textExtraction: {
            2: function(node) { return $(node).find("span").text().toLowerCase(); },
            3: function(node) { return $(node).find("img").attr("alt"); },
            4: function(node) { return $(node).find("img").attr("alt"); },
            5: function(node) { return $(node).find("img").attr("alt"); },
            6: function(node) { return $(node).find("img").attr("alt"); },
            7: function(node) { return $(node).find("img").attr("alt"); },
            8: function(node) { return $(node).find("img").attr("alt"); },
        },
        widgets: ['zebra'],
        headers: {
            0: { sorter: false},
            1: { sorter: 'showNames'},
            2: { sorter: 'quality'},
            3: { sorter: 'sports'},
            4: { sorter: 'scene'},
            5: { sorter: 'anime'},
            6: { sorter: 'flatfold'},
            7: { sorter: 'paused'},
            8: { sorter: 'subtitle'},
            9: { sorter: 'default_ep_status'},
           10: { sorter: 'status'},
           11: { sorter: false},
           12: { sorter: false},
           13: { sorter: false},
           14: { sorter: false},
           15: { sorter: false},
           16: { sorter: false},
           17: { sorter: false}
        }
    });
});
</script>
<script type="text/javascript" src="${sbRoot}/js/massUpdate.js?${sbPID}"></script>
</%block>
<%block name="content">
<%namespace file="/inc_defs.mako" import="renderQualityPill"/>
% if not header is UNDEFINED:
    <h1 class="header">${header}</h1>
% else:
    <h1 class="title">${title}</h1>
% endif
<form name="massUpdateForm" method="post" action="massUpdate">

<table id="massUpdateTable" class="sickbeardTable tablesorter" cellspacing="1" border="0" cellpadding="0">
    <thead>
        <tr>
            <th class="col-checkbox">Edit<br/><input type="checkbox" class="bulkCheck" id="editCheck" /></th>
            <th class="nowrap" style="text-align: left;">Show Name</th>
            <th class="col-quality">Quality</th>
            <th class="col-legend">Sports</th>
            <th class="col-legend">Scene</th>
            <th class="col-legend">Anime</th>
            <th class="col-legend">Flat Folders</th>
            <th class="col-legend">Paused</th>
            <th class="col-legend">Subtitle</th>
            <th class="col-legend">Default Ep<br>Status</th>
            <th class="col-legend">Status</th>
            <th width="1%">Update<br/><input type="checkbox" class="bulkCheck" id="updateCheck" /></th>
            <th width="1%">Rescan<br/><input type="checkbox" class="bulkCheck" id="refreshCheck" /></th>
            <th width="1%">Rename<br/><input type="checkbox" class="bulkCheck" id="renameCheck" /></th>
        % if sickbeard.USE_SUBTITLES:
            <th width="1%">Search Subtitle<br/><input type="checkbox" class="bulkCheck" id="subtitleCheck" /></th>
        % endif
            <!-- <th>Force Metadata Regen <input type="checkbox" class="bulkCheck" id="metadataCheck" /></th>//-->
            <th width="1%">Delete<br/><input type="checkbox" class="bulkCheck" id="deleteCheck" /></th>
            <th width="1%">Remove<br/><input type="checkbox" class="bulkCheck" id="removeCheck" /></th>
        </tr>
    </thead>

    <tfoot>
        <tr>
            <td rowspan="1" colspan="2" class="align-center alt"><input class="btn pull-left" type="button" value="Edit Selected" id="submitMassEdit" /></td>
            <td rowspan="1" colspan="${(14, 15)[bool(sickbeard.USE_SUBTITLES)]}" class="align-right alt"><input class="btn pull-right" type="button" value="Submit" id="submitMassUpdate" /></td>
        </tr>
    </tfoot>

    <tbody>
        <% myShowList = sickbeard.showList %>
        <% myShowList.sort(lambda x, y: cmp(x.name, y.name)) %>

        % for curShow in myShowList:
        <% curEp = curShow.nextaired %>
        <% curUpdate_disabled = "" %>
        <% curRefresh_disabled = "" %>
        <% curRename_disabled = "" %>
        <% curSubtitle_disabled = "" %>
        <% curDelete_disabled = "" %>
        <% curRemove_disabled = "" %>

        % if sickbeard.showQueueScheduler.action.isBeingUpdated(curShow) or sickbeard.showQueueScheduler.action.isInUpdateQueue(curShow):
            <% curUpdate_disabled = "disabled=\"disabled\" " %>
        % endif

        <% curUpdate = "<input type=\"checkbox\" class=\"updateCheck\" id=\"update-"+str(curShow.indexerid)+"\" "+curUpdate_disabled+"/>" %>

        % if sickbeard.showQueueScheduler.action.isBeingRefreshed(curShow) or sickbeard.showQueueScheduler.action.isInRefreshQueue(curShow):
            <% curRefresh_disabled = "disabled=\"disabled\" " %>
        % endif

        <% curRefresh = "<input type=\"checkbox\" class=\"refreshCheck\" id=\"refresh-"+str(curShow.indexerid)+"\" "+curRefresh_disabled+"/>" %>

        % if sickbeard.showQueueScheduler.action.isBeingRenamed(curShow) or sickbeard.showQueueScheduler.action.isInRenameQueue(curShow):
            <% curRename = "disabled=\"disabled\" " %>
        % endif

        <% curRename = "<input type=\"checkbox\" class=\"renameCheck\" id=\"rename-"+str(curShow.indexerid)+"\" "+curRename_disabled+"/>" %>

        % if not curShow.subtitles or sickbeard.showQueueScheduler.action.isBeingSubtitled(curShow) or sickbeard.showQueueScheduler.action.isInSubtitleQueue(curShow):
            <% curSubtitle_disabled = "disabled=\"disabled\" " %>
        % endif

        <% curSubtitle = "<input type=\"checkbox\" class=\"subtitleCheck\" id=\"subtitle-"+str(curShow.indexerid)+"\" "+curSubtitle_disabled+"/>" %>

        % if sickbeard.showQueueScheduler.action.isBeingRenamed(curShow) or sickbeard.showQueueScheduler.action.isInRenameQueue(curShow) or sickbeard.showQueueScheduler.action.isInRefreshQueue(curShow):
            <% curDelete = "disabled=\"disabled\" " %>
        % endif

        <% curDelete = "<input type=\"checkbox\" class=\"deleteCheck\" id=\"delete-"+str(curShow.indexerid)+"\" "+curDelete_disabled+"/>" %>

        % if sickbeard.showQueueScheduler.action.isBeingRenamed(curShow) or sickbeard.showQueueScheduler.action.isInRenameQueue(curShow) or sickbeard.showQueueScheduler.action.isInRefreshQueue(curShow):
            <% curRemove = "disabled=\"disabled\" " %>
        % endif

        <% curRemove = "<input type=\"checkbox\" class=\"removeCheck\" id=\"remove-"+str(curShow.indexerid)+"\" "+curRemove_disabled+"/>" %>
        <tr>
            <td align="center"><input type="checkbox" class="editCheck" id="edit-${curShow.indexerid}" /></td>
            <td class="tvShow"><a href="${sbRoot}/home/displayShow?show=${curShow.indexerid}">${curShow.name}</a></td>
            <td align="center">${renderQualityPill(curShow.quality)}</td>
            <td align="center"><img src="${sbRoot}/images/${('no16.png" alt="N"', 'yes16.png" alt="Y"')[int(curShow.is_sports) == 1]} width="16" height="16" /></td>
            <td align="center"><img src="${sbRoot}/images/${('no16.png" alt="N"', 'yes16.png" alt="Y"')[int(curShow.is_scene) == 1]} width="16" height="16" /></td>
            <td align="center"><img src="${sbRoot}/images/${('no16.png" alt="N"', 'yes16.png" alt="Y"')[int(curShow.is_anime) == 1]} width="16" height="16" /></td>
            <td align="center"><img src="${sbRoot}/images/${('no16.png" alt="N"', 'yes16.png" alt="Y"')[int(curShow.flatten_folders) == 1]} width="16" height="16" /></td>
            <td align="center"><img src="${sbRoot}/images/${('no16.png" alt="N"', 'yes16.png" alt="Y"')[int(curShow.paused) == 1]} width="16" height="16" /></td>
            <td align="center"><img src="${sbRoot}/images/${('no16.png" alt="N"', 'yes16.png" alt="Y"')[int(curShow.subtitles) == 1]} width="16" height="16" /></td>
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
