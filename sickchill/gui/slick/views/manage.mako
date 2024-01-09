<%inherit file="/layouts/main.mako" />
<%!
    from operator import attrgetter
    from sickchill import settings
    from sickchill.oldbeard.common import statusStrings
%>

<%block name="content">
    <%namespace file="/inc_defs.mako" import="renderQualityPill" />

    <form name="massUpdateForm" method="post" action="massUpdate">

        <div class="row">
            <div class="col-lg-8 col-md-8 col-sm-8 col-xs-12 pull-right">
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
                    <table id="massUpdateTable" class="tablesorter">
                        <thead>
                            <tr>
                                <th class="col-checkbox">${_('Edit')}<br>
                                    <label for="editCheck" class="sr-only">${_('Edit All')}</label>
                                    <input type="checkbox" class="bulkCheck" id="editCheck" />
                                </th>
                                <th class="col-legend nowrap">${_('Show Name')}</th>
                                <th class="col-network filter-select filter-onlyAvail text-nowrap" data-placeholder="${_('All')}">${_('Network')}</th>
                                <th class="col-quality filter-select filter-onlyAvail text-nowrap" data-placeholder="${_('All')}">${_('Quality')}</th>
                                <th class="col-legend filter-select filter-onlyAvail text-nowrap" data-placeholder="${_('All')}">${_('Sports')}</th>
                                <th class="col-legend filter-select filter-onlyAvail text-nowrap" data-placeholder="${_('All')}">${_('Scene')}</th>
                                <th class="col-legend filter-select filter-onlyAvail text-nowrap" data-placeholder="${_('All')}">${_('Anime')}</th>
                                <th class="col-legend col-shrink filter-select filter-onlyAvail text-nowrap" data-placeholder="${_('All')}">${_('S. folders')}</th>
                                <th class="col-legend filter-select filter-onlyAvail text-nowrap" data-placeholder="${_('All')}">${_('Paused')}</th>
                                <th class="col-legend filter-select filter-onlyAvail text-nowrap" data-placeholder="${_('All')}">${_('Subtitle')}</th>
                                <th class="col-legend col-shrink filter-select filter-onlyAvail text-nowrap" data-placeholder="${_('All')}">${_('Default Status')}</th>
                                <th class="col-legend filter-select filter-onlyAvail text-nowrap" data-placeholder="${_('All')}">${_('Status')}</th>
                                <th class="col-legend filter-select filter-onlyAvail text-nowrap" data-placeholder="${_('All')}">${_('Root dir')}</th>

                                <th class="col-checkbox text-nowrap">${_('Update')}<br>
                                    <label for="updateCheck" class="sr-only">${_('Update All')}</label>
                                    <input type="checkbox" class="bulkCheck" id="updateCheck" />
                                </th>
                                <th class="col-checkbox text-nowrap">${_('Rescan')}<br>
                                    <label for="refreshCheck" class="sr-only">${_('Rescan All')}</label>
                                    <input type="checkbox" class="bulkCheck" id="refreshCheck" />
                                </th>
                                <th class="col-checkbox text-nowrap">${_('Rename')}<br>
                                    <label for="renameCheck" class="sr-only">${_('Rename All')}</label>
                                    <input type="checkbox" class="bulkCheck" id="renameCheck" />
                                </th>
                                % if settings.USE_SUBTITLES:
                                    <th class="col-checkbox text-nowrap">${_('Search Subtitle')}<br>
                                        <label for="subtitleCheck" class="sr-only">${_('Subtitle All')}</label>
                                        <input type="checkbox" class="bulkCheck" id="subtitleCheck" />
                                    </th>
                                % endif
                                <th class="col-checkbox text-nowrap">${_('Delete')}<br>
                                    <label for="deleteCheck" class="sr-only">${_('Delete All')}</label>
                                    <input type="checkbox" class="bulkCheck" id="deleteCheck" />
                                </th>
                                <th class="col-checkbox text-nowrap">${_('Remove')}<br>
                                    <label for="removeCheck" class="sr-only">${_('Remove All')}</label>
                                    <input type="checkbox" class="bulkCheck" id="removeCheck" />
                                </th>
                            </tr>
                        </thead>
                        <tbody>
                            % for curShow in sorted(settings.showList, key=lambda mbr: attrgetter('sort_name')(mbr)):
                            <%
                                if settings.showQueueScheduler.action.is_in_remove_queue(curShow) or settings.showQueueScheduler.action.is_being_removed(curShow):
                                    continue
                            %>
                                <tr>
                                    <td class="text-center">
                                        <label for="edit-${curShow.indexerid}" class="sr-only">${_('Edit')} ${curShow.name}</label>
                                        <input type="checkbox" class="editCheck" name="edit" value="${curShow.indexerid}" id="edit-${curShow.indexerid}" />
                                    </td>
                                    <td class="tvShow text-nowrap"><a href="${scRoot}/home/displayShow?show=${curShow.indexerid}">${curShow.name}</a></td>
                                    <td class="text-center">
                                        % if curShow.network:
                                            <span title="${curShow.network}">
                                                <img class="show-network-image" src="${static_url('images/network/nonetwork.png')}"
                                                     data-src="${static_url(curShow.network_image_url)}" alt="${curShow.network}" title="${curShow.network}" />
                                            </span>
                                        % endif
                                    </td>
                                    <td class="text-center">${renderQualityPill(curShow.quality, showTitle=True)}</td>
                                    <td class="text-center"><span class="displayshow-icon-${('disable', 'enable')[bool(curShow.is_sports)]}" title=${("N", "Y")[bool(curShow.is_sports)]}></span></td>
                                    <td class="text-center"><span class="displayshow-icon-${('disable', 'enable')[bool(curShow.is_scene)]}" title=${("N", "Y")[bool(curShow.is_scene)]}></span></td>
                                    <td class="text-center"><span class="displayshow-icon-${('disable', 'enable')[bool(curShow.is_anime)]}" title=${("N", "Y")[bool(curShow.is_anime)]}></span></td>
                                    <td class="text-center"><span class="displayshow-icon-${('disable', 'enable')[bool(curShow.season_folders)]}" title=${("N", "Y")[bool(curShow.season_folders)]}></span></td>
                                    <td class="text-center"><span class="displayshow-icon-${('disable', 'enable')[bool(curShow.paused)]}" title=${("N", "Y")[bool(curShow.paused)]}></span></td>
                                    <td class="text-center"><span class="displayshow-icon-${('disable', 'enable')[bool(curShow.subtitles)]}" title=${("N", "Y")[bool(curShow.subtitles)]}></span></td>
                                    <td class="text-center">${statusStrings[curShow.default_ep_status]}</td>
                                    <td class="text-center">${_(curShow.status)}</td>

                                    <td class="text-center">${curShow._location.rsplit('\\', 1)[0]}</td>
                                    <td class="text-center">
                                        <% disabled = settings.showQueueScheduler.action.is_being_updated(curShow) or settings.showQueueScheduler.action.is_in_update_queue(curShow) %>
                                        <label for="update-${curShow.indexerid}" class="sr-only">${_('Update')} ${curShow.name}</label>
                                        <input type="checkbox" class="updateCheck" name="update" value="${curShow.indexerid}" id="update-${curShow.indexerid}" ${("", "disabled")[disabled]}/>
                                    </td>

                                    <td class="text-center">
                                        <% disabled = settings.showQueueScheduler.action.is_being_refreshed(curShow) or settings.showQueueScheduler.action.is_in_refresh_queue(curShow) %>
                                        <label for="refresh-${curShow.indexerid}" class="sr-only">${_('Refresh')} ${curShow.name}</label>
                                        <input type="checkbox" class="refreshCheck" name="refresh" value="${curShow.indexerid}" id="refresh-${curShow.indexerid}" ${("", "disabled")[disabled]}/>
                                    </td>

                                    <td class="text-center">
                                        <% disabled = settings.showQueueScheduler.action.is_being_renamed(curShow) or settings.showQueueScheduler.action.is_in_rename_queue(curShow) %>
                                        <label for="rename-${curShow.indexerid}" class="sr-only">${_('Rename')} ${curShow.name}</label>
                                        <input type="checkbox" class="renameCheck" name="rename" value="${curShow.indexerid}" id="rename-${curShow.indexerid}" ${("", "disabled")[disabled]}/>
                                    </td>

                                    % if settings.USE_SUBTITLES:
                                        <td class="text-center">
                                            <% disabled = not curShow.subtitles or settings.showQueueScheduler.action.is_being_subtitled(curShow) or settings.showQueueScheduler.action.is_in_subtitle_queue(curShow) %>
                                            <label for="subtitle-${curShow.indexerid}" class="sr-only">${_('Subtitle')} ${curShow.name}</label>
                                            <input type="checkbox" class="subtitleCheck" name="subtitle" value="${curShow.indexerid}" id="subtitle-${curShow.indexerid}" ${("", "disabled")[disabled]}/>
                                        </td>
                                    % endif

                                    <td class="text-center">
                                        <%
                                            disabled = any([
                                                settings.showQueueScheduler.action.is_being_renamed(curShow),
                                                settings.showQueueScheduler.action.is_in_rename_queue(curShow),
                                                settings.showQueueScheduler.action.is_in_refresh_queue(curShow)
                                            ])
                                        %>
                                        <label for="delete-${curShow.indexerid}" class="sr-only">${_('Delete')} ${curShow.name}</label>
                                        <input type="checkbox" class="confirm deleteCheck" name="delete" value="${curShow.indexerid}" id="delete-${curShow.indexerid}" ${("", "disabled")[disabled]}/>
                                    </td>

                                    <td class="text-center">
                                        <%
                                            disabled = any([
                                                settings.showQueueScheduler.action.is_being_renamed(curShow),
                                                settings.showQueueScheduler.action.is_in_rename_queue(curShow),
                                                settings.showQueueScheduler.action.is_in_refresh_queue(curShow)
                                            ])
                                        %>
                                        <label for="remove-${curShow.indexerid}" class="sr-only">${_('Remove')} ${curShow.name}</label>
                                        <input type="checkbox" class="removeCheck" name="remove" value="${curShow.indexerid}" id="remove-${curShow.indexerid}" ${("", "disabled")[disabled]}/>
                                    </td>
                                </tr>
                            % endfor
                        </tbody>
                        <tfoot>
                            <tr>
                                <td rowspan="1" colspan="${(18, 19)[bool(settings.USE_SUBTITLES)]}" class="align-right alt"><input class="btn pull-right submitMassUpdate" type="button" value="${_('Submit')}" /></td>
                            </tr>
                        </tfoot>
                    </table>
                </div>
            </div>
        </div>

    </form>
</%block>
