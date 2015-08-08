<%!
    import sickbeard
    from sickbeard.helpers import anon_url
%>

<table id="addRootDirTable" class="sickbeardTable tablesorter">
    <thead><tr><th class="col-checkbox"><input type="checkbox" id="checkAll" checked=checked></th><th>Directory</th><th width="20%">Show Name (tvshow.nfo)<th width="20%">Indexer</td></tr></thead>
    <tbody>
% for curDir in dirList:
    <%
        if curDir['added_already']:
            continue

        show_id = curDir['dir']
        if curDir['existing_info'][0]:
            show_id = show_id + '|' + str(curDir['existing_info'][0]) + '|' + str(curDir['existing_info'][1])
            indexer = curDir['existing_info'][2]

        indexer = 0
        if curDir['existing_info'][0]:
            indexer = curDir['existing_info'][2]
        elif sickbeard.INDEXER_DEFAULT > 0:
            indexer = sickbeard.INDEXER_DEFAULT
    %>
    <tr>
        <td class="col-checkbox"><input type="checkbox" id="${show_id}" class="dirCheck" checked=checked></td>
        <td><label for="${show_id}">${curDir['display_dir']}</label></td>
        % if curDir['existing_info'][1] and indexer > 0:
            <td><a href="${anon_url(sickbeard.indexerApi(indexer).config['show_url'], curDir['existing_info'][0])}">${curDir['existing_info'][1]}</a></td>
        % else:
            <td>?</td>
        % endif
        <td align="center">
            <select name="indexer">
                % for curIndexer in sickbeard.indexerApi().indexers.iteritems():
                    <option value="${curIndexer[0]}" ${('', 'selected="selected"')[curIndexer[0] == indexer]}>${curIndexer[1]}</option>
                % endfor
            </select>
        </td>
    </tr>
% endfor
    </tbody>
</table>
