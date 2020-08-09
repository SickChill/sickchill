<%inherit file="/layouts/main.mako"/>
<%!
    from operator import attrgetter
    from sickchill import settings
    from sickchill.oldbeard.common import statusStrings
%>

<%block name="content">
    <%namespace file="/inc_defs.mako" import="renderQualityPill"/>

    <form name="massUpdateForm" method="post" action="massUpdate">

        <div class="row">
            <div class="col-lg-8 col-md-8 col-sm-8 col-xs-12 pull-right">
                <input class="btn submitMassEdit pull-right" type="button" value="${_('Edit Selected')}" />
                <input class="btn submitMassUpdate pull-right" type="button" value="${_('Submit')}" />
                <span class="show-option">
                    <button id="popover" type="button" class="btn pull-right">${_('Select Columns')} <b class="caret"></b></button>
                </span>
                <span class="show-option">
                    <button type="button" class="resetsorting btn pull-right">${_('Clear Filter(s)')}</button>
                </span>
            </div>
            <div class="col-lg-4 col-md-4 col-sm-4 col-xs-12">
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
                    <table id="massUpdateTable" class="tablesorter" cellspacing="1" border="0" cellpadding="0">
                        <thead>
                            <tr>
                                <th class="col-checkbox">${_('Edit')}<br><input type="checkbox" class="bulkCheck" id="editCheck" /></th>
                                <th class="nowrap" style="text-align: left;">${_('Show Name')}</th>
                                <th class="col-network">${_('Network')}</th>
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
                                % if settings.USE_SUBTITLES:
                                    <th width="1%">${_('Search Subtitle')}<br><input type="checkbox" class="bulkCheck" id="subtitleCheck" /></th>
                                % endif
                                <!-- <th>${_('Force Metadata Regen')} <input type="checkbox" class="bulkCheck" id="metadataCheck" /></th>//-->
                                <th width="1%">${_('Delete')}<br><input type="checkbox" class="bulkCheck" id="deleteCheck" /></th>
                                <th width="1%">${_('Remove')}<br><input type="checkbox" class="bulkCheck" id="removeCheck" /></th>
                            </tr>
                        </thead>
                        <tbody>
                            % for curShow in sorted(settings.showList, key=lambda mbr: attrgetter('sort_name')(mbr)):
                            <%
                                if settings.showQueueScheduler.action.is_in_remove_queue(curShow) or settings.showQueueScheduler.action.is_being_removed(curShow):
                                    continue

                                disabled = settings.showQueueScheduler.action.is_being_updated(curShow) or settings.showQueueScheduler.action.is_in_update_queue(curShow)
                                curUpdate = "<input type=\"checkbox\" class=\"updateCheck\" id=\"update-" + str(curShow.indexerid) + "\" " + ("", "disabled=\"disabled\" ")[disabled] + "/>"

                                disabled = settings.showQueueScheduler.action.is_being_refreshed(curShow) or settings.showQueueScheduler.action.is_in_refresh_queue(curShow)
                                curRefresh = "<input type=\"checkbox\" class=\"refreshCheck\" id=\"refresh-" + str(curShow.indexerid) + "\" " + ("", "disabled=\"disabled\" ")[disabled] + "/>"

                                disabled = settings.showQueueScheduler.action.is_being_renamed(curShow) or settings.showQueueScheduler.action.is_in_rename_queue(curShow)
                                curRename = "<input type=\"checkbox\" class=\"renameCheck\" id=\"rename-" + str(curShow.indexerid) + "\" " + ("", "disabled=\"disabled\" ")[disabled] + "/>"

                                disabled = not curShow.subtitles or settings.showQueueScheduler.action.is_being_subtitled(curShow) or settings.showQueueScheduler.action.is_in_subtitle_queue(curShow)
                                curSubtitle = "<input type=\"checkbox\" class=\"subtitleCheck\" id=\"subtitle-" + str(curShow.indexerid) + "\" " + ("", "disabled=\"disabled\" ")[disabled] + "/>"

                                disabled = settings.showQueueScheduler.action.is_being_renamed(curShow) or settings.showQueueScheduler.action.is_in_rename_queue(curShow) or settings.showQueueScheduler.action.is_in_refresh_queue(curShow)
                                curDelete = "<input type=\"checkbox\" class=\"confirm deleteCheck\" id=\"delete-" + str(curShow.indexerid) + "\" " + ("", "disabled=\"disabled\" ")[disabled] + "/>"

                                disabled = settings.showQueueScheduler.action.is_being_renamed(curShow) or settings.showQueueScheduler.action.is_in_rename_queue(curShow) or settings.showQueueScheduler.action.is_in_refresh_queue(curShow)
                                curRemove = "<input type=\"checkbox\" class=\"removeCheck\" id=\"remove-" + str(curShow.indexerid) + "\" " + ("", "disabled=\"disabled\" ")[disabled] + "/>"
                            %>
                                <tr>
                                    <td align="center"><input type="checkbox" class="editCheck" id="edit-${curShow.indexerid}" /></td>
                                    <td class="tvShow"><a href="${scRoot}/home/displayShow?show=${curShow.indexerid}">${curShow.name}</a></td>
                                    <td align="center">
                                        % if curShow.network:
                                            <span title="${curShow.network}">
                                                <img class="show-network-image" src="${static_url("images/network/nonetwork.png")}"
                                                     data-src="${static_url(curShow.network_image_url)}" alt="${curShow.network}" title="${curShow.network}" />
                                            </span>
                                        % endif
                                    </td>
                                    <td align="center">${renderQualityPill(curShow.quality, showTitle=True)}</td>
                                    <td align="center"><span class="displayshow-icon-${("disable", "enable")[bool(curShow.is_sports)]}" title=${("N", "Y")[bool(curShow.is_sports)]}></span></td>
                                    <td align="center"><span class="displayshow-icon-${("disable", "enable")[bool(curShow.is_scene)]}" title=${("N", "Y")[bool(curShow.is_scene)]}></span></td>
                                    <td align="center"><span class="displayshow-icon-${("disable", "enable")[bool(curShow.is_anime)]}" title=${("N", "Y")[bool(curShow.is_anime)]}></span></td>
                                    <td align="center"><span class="displayshow-icon-${("disable", "enable")[bool(curShow.season_folders)]}" title=${("N", "Y")[bool(curShow.season_folders)]}></span></td>
                                    <td align="center"><span class="displayshow-icon-${("disable", "enable")[bool(curShow.paused)]}" title=${("N", "Y")[bool(curShow.paused)]}></span></td>
                                    <td align="center"><span class="displayshow-icon-${("disable", "enable")[bool(curShow.subtitles)]}" title=${("N", "Y")[bool(curShow.subtitles)]}></span></td>
                                    <td align="center">${statusStrings[curShow.default_ep_status]}</td>
                                    <td align="center">${_(curShow.status)}</td>
                                    <td align="center">${curUpdate}</td>
                                    <td align="center">${curRefresh}</td>
                                    <td align="center">${curRename}</td>
                                    % if settings.USE_SUBTITLES:
                                        <td align="center">${curSubtitle}</td>
                                    % endif
                                    <td align="center">${curDelete}</td>
                                    <td align="center">${curRemove}</td>
                                </tr>
                            % endfor
                        </tbody>
                        <tfoot>
                            <tr>
                                <td rowspan="1" colspan="2" class="align-center alt"><input class="btn pull-left submitMassEdit" type="button" value="${_('Edit Selected')}" /></td>
                                <td rowspan="1" colspan="${(15, 16)[bool(settings.USE_SUBTITLES)]}" class="align-right alt"><input class="btn pull-right submitMassUpdate" type="button" value="${_('Submit')}" /></td>
                            </tr>
                        </tfoot>
                    </table>
                </div>
            </div>
        </div>

    </form>
</%block>
