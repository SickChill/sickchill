<%inherit file="/layouts/main.mako"/>
<%!
    import datetime
    from sickchill import settings
    from sickchill.oldbeard import subtitles
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
        <h2>${_('All of your episodes have {subsLanguage} subtitles.').format(subsLanguage=subsLanguage)}</h2>
        <br>
        % endif

        <form action="${scRoot}/manage/subtitleMissed" method="get">
            % if settings.SUBTITLES_MULTI:
                ${_('Manage episodes without')} <select name="whichSubs" class="form-control form-control-inline input-sm">
                <option value="all">${_('All')}</option>
                % for sub_code in subtitles.wanted_languages():
                    <option value="${sub_code}">${subtitles.name_from_code(sub_code)}</option>
                % endfor
            % else:
                ${_('Manage episodes without')} <select name="whichSubs" class="form-control form-control-inline input-sm">
                % if not subtitles.wanted_languages():
                    <option value="all">${_('All')}</option>
                % else:
                    % for index, sub_code in enumerate(subtitles.wanted_languages()):
                        % if index == 0:
                            <option value="und">${subtitles.name_from_code(sub_code)}</option>
                        % endif
                    % endfor
                % endif
            % endif
            </select>
            <input class="btn" type="submit" value="${_('Manage')}" />
        </form>

    % else:
        ##Strange that this is used by js but is an input outside of any form?
        <input type="hidden" id="selectSubLang" name="selectSubLang" value="${whichSubs}" />
        <form action="${scRoot}/manage/downloadSubtitleMissed" method="post">
            % if settings.SUBTITLES_MULTI:
                <h2>${_('Episodes without {subsLanguage} subtitles.').format(subsLanguage=subsLanguage)}</h2>
            % else:
                % for index, sub_code in enumerate(subtitles.wanted_languages()):
                    % if index == 0:
                        <h2>${_('Episodes without {subtitleLanguage} (undefined) subtitles.').format(subtitleLanguage=subtitles.name_from_code(sub_code))}</h2>
                    % endif
                % endfor
            % endif
            <br>
            ${_('Download missed subtitles for selected episodes')} <input class="btn btn-inline" type="submit" value="Go" />
            <div>
                <button type="button" class="btn btn-xs selectAllShows">${_('Select all')}</button>
                <button type="button" class="btn btn-xs deselectAllShows">${_('Clear all')}</button>
            </div>
            <br>
            <table class="sickchillTable manageTable">
            % for cur_indexer_id in sorted_show_ids:
                <tr id="${cur_indexer_id}">
                    <th style="width: 1%;"><input type="checkbox" class="allCheck" id="allCheck-${cur_indexer_id}" name="${cur_indexer_id}-all"checked="checked" /></th>
                    <th colspan="3" style="text-align: left;"><a class="whitelink" href="${scRoot}/home/displayShow?show=${cur_indexer_id}">${show_names[cur_indexer_id]}</a> (${ep_counts[cur_indexer_id]}) <input type="button" class="pull-right get_more_eps btn" id="${cur_indexer_id}" value="Expand" /></th>
                </tr>
            % endfor
            </table>
        </form>
    % endif
    </div>
</%block>
