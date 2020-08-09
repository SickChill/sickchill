<%inherit file="/layouts/main.mako"/>
<%!
    from sickchill import settings
    from sickchill.oldbeard import common
%>

<%block name="scripts">
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
            <form action="${scRoot}/manage/episodeStatuses" method="get">
                <label for="whichStatus">${_('Manage episodes with status')}</label>
                <select name="whichStatus" class="form-control form-control-inline input-sm" title="whichStatus">
                    % for curStatus in [common.SKIPPED, common.SNATCHED, common.WANTED, common.IGNORED] + common.Quality.DOWNLOADED + common.Quality.ARCHIVED:
                        %if curStatus not in [common.ARCHIVED, common.DOWNLOADED]:
                            <option value="${curStatus}">${common.statusStrings[curStatus]}</option>
                        %endif
                    % endfor
                </select>
                <input class="btn btn-inline" type="submit" value="${_('Manage')}" />
            </form>
        </div>
    </div>

    % if not whichStatus or (whichStatus and not ep_counts):

        % if whichStatus:
            <div class="row">
                <div class="col-md-12">
                    <h3>${_('None of your episodes have status')} ${common.statusStrings[whichStatus]}</h3>
                </div>
            </div>
        % endif
    % else:
        <form action="${scRoot}/manage/changeEpisodeStatuses" method="post">
            <input type="hidden" id="oldStatus" name="oldStatus" value="${whichStatus}" />
            <br/>
            <div class="row">
                <div class="col-md-12">
                    <h2>${_('Shows containing')} ${common.statusStrings[whichStatus]} ${_('episodes')}</h2>
                </div>
            </div>
            <div class="row">
                <div class="col-md-12">
                    <%
                        if int(whichStatus) in [common.IGNORED, common.SNATCHED, common.SNATCHED_PROPER, common.SNATCHED_BEST] + common.Quality.DOWNLOADED + common.Quality.ARCHIVED:
                            row_class = "good"
                        else:
                            row_class = common.Overview.overviewStrings[int(whichStatus)]
                    %>
                    <input type="hidden" id="row_class" value="${row_class}" />

                    <label for="newStatus">${_('Set checked shows/episodes to')}</label>
                    <select name="newStatus" class="form-control form-control-inline input-sm" title="newStatus">
                        <%
                            statusList = [common.SKIPPED, common.WANTED, common.IGNORED] + common.Quality.DOWNLOADED + common.Quality.ARCHIVED
                            # Do not allow setting to bare downloaded or archived!
                            statusList.remove(common.DOWNLOADED)
                            statusList.remove(common.ARCHIVED)
                            if int(whichStatus) in statusList:
                                statusList.remove(int(whichStatus))

                            if int(whichStatus) in [common.SNATCHED, common.SNATCHED_PROPER, common.SNATCHED_BEST] + common.Quality.ARCHIVED + common.Quality.DOWNLOADED and settings.USE_FAILED_DOWNLOADS:
                                statusList.append(common.FAILED)
                        %>
                        % for curStatus in statusList:
                            <option value="${curStatus}">${common.statusStrings[curStatus]}</option>
                        % endfor
                    </select>

                    <input class="btn btn-inline" type="submit" value="${_('Go')}" />
                </div>
            </div>
            <div class="row">
                <div class="col-md-12">
                    <button type="button" class="btn btn-xs selectAllShows">${_('Select all')}</button>
                    <button type="button" class="btn btn-xs deselectAllShows">${_('Clear all')}</button>
                </div>
            </div>
            <br/>
            <div class="row">
                <div class="col-md-12">
                    <div class="horizontal-scroll">
                        <table class="sickchillTable manageTable">
                            % for cur_indexer_id in sorted_show_ids:
                                <tr id="${cur_indexer_id}">
                                    <th>
                                        <input type="checkbox" class="allCheck" id="allCheck-${cur_indexer_id}" name="${cur_indexer_id}-all" checked="checked"  title="allCheck"/>
                                    </th>
                                    <th colspan="2" style="width: 100%; text-align: left;">
                                        <a class="whitelink" href="${scRoot}/home/displayShow?show=${cur_indexer_id}">${show_names[cur_indexer_id]}</a>
                                        (${ep_counts[cur_indexer_id]}) <input type="button" class="pull-right get_more_eps btn" id="${cur_indexer_id}" value="Expand"/>
                                    </th>
                                </tr>
                            % endfor
                            <tr>
                                <td style="padding:0;"></td>
                                <td style="padding:0;"></td>
                                <td style="padding:0;"></td>
                            </tr>
                        </table>
                    </div>
                </div>
            </div>
        </form>

    % endif
</%block>
