<%inherit file="/layouts/main.mako"/>
<%!
    from sickbeard import subtitles
    import datetime
    import sickbeard
    from sickbeard import common
%>
<%block name="content">
    <div id="content960">
    % if not header is UNDEFINED:
        <h1 class="header">${header}</h1>
    % else:
        <h1 class="title">${title}</h1>
    % endif
    % if whichSubs:
        <% subsLanguage = subtitles.name_from_code(whichSubs) if not whichSubs == 'all' else 'All' %>
    % endif
    % if not whichSubs or (whichSubs and not ep_counts):
        % if whichSubs:
        <h2>All of your episodes have ${subsLanguage} subtitles.</h2>
        <br>
        % endif

        <form action="${srRoot}/manage/subtitleMissed" method="get">
            Manage episodes without <select name="whichSubs" class="form-control form-control-inline input-sm">
            <option value="all">All</option>
            % for sub_code in subtitles.wanted_languages():
                <option value="${sub_code}">${subtitles.name_from_code(sub_code)}</option>
            % endfor
            </select>

            <input class="btn" type="submit" value="Manage" />
        </form>

    % else:
        ##Strange that this is used by js but is an input outside of any form?
        <input type="hidden" id="selectSubLang" name="selectSubLang" value="${whichSubs}" />
        <form action="${srRoot}/manage/downloadSubtitleMissed" method="post">
            <h2>Episodes without ${subsLanguage} subtitles.</h2>
            <br>
            Download missed subtitles for selected episodes <input class="btn btn-inline" type="submit" value="Go" />
            <div>
                <button type="button" class="btn btn-xs selectAllShows">Select all</a></button>
                <button type="button" class="btn btn-xs unselectAllShows">Clear all</a></button>
            </div>
            <br>
            <table class="sickbeardTable manageTable" cellspacing="1" border="0" cellpadding="0">
            % for cur_indexer_id in sorted_show_ids:
                <tr id="${cur_indexer_id}">
                    <th><input type="checkbox" class="allCheck" id="allCheck-${cur_indexer_id}" name="${cur_indexer_id}-all"checked="checked" /></th>
                    <th colspan="3" style="width: 100%; text-align: left;"><a class="whitelink" href="${srRoot}/home/displayShow?show=${cur_indexer_id}">${show_names[cur_indexer_id]}</a> (${ep_counts[cur_indexer_id]}) <input type="button" class="pull-right get_more_eps btn" id="${cur_indexer_id}" value="Expand" /></th>
                </tr>
            % endfor
            </table>
        </form>
    % endif
    </div>
</%block>
