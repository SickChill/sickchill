<%!
    import sickbeard
    from sickbeard.helpers import anon_url
%>

<table id="addRootDirTable" class="sickbeardTable tablesorter">
    <thead><tr><th class="col-checkbox"><input type="checkbox" id="checkAll" checked=checked></th><th>${_('Directory')}</th><th width="20%">${_('Show Name (tvshow.nfo)')}<th width="20%">${_('Indexer')}</td></tr></thead>
    <tbody>
% for cur_dir in dirList:
    <%
        if cur_dir['added_already']:
            continue

        show_id = cur_dir['dir']
        if cur_dir['existing_info'][0]:
            show_id = show_id + '|' + str(cur_dir['existing_info'][0]) + '|' + str(cur_dir['existing_info'][1])
            indexer = cur_dir['existing_info'][2]

        indexer = 0
        if cur_dir['existing_info'][0]:
            indexer = cur_dir['existing_info'][2]
        elif sickbeard.INDEXER_DEFAULT > 0:
            indexer = sickbeard.INDEXER_DEFAULT
    %>
    <tr>
        <td class="col-checkbox"><input type="checkbox" id="${show_id}" class="dirCheck" checked=checked></td>
        <td><label for="${show_id}">${cur_dir['display_dir']}</label></td>
        % if cur_dir['existing_info'][1] and indexer > 0:
            <td><a href="${anon_url(sickbeard.indexerApi(indexer).config['show_url'], cur_dir['existing_info'][0])}">${cur_dir['existing_info'][1]}</a></td>
        % else:
            <td>?</td>
        % endif
        <td align="center">
            <select name="indexer">
                % for cur_indexer in sickbeard.indexerApi().indexers.iteritems():
                    <option value="${cur_indexer[0]}" ${('', 'selected="selected"')[cur_indexer[0] == indexer]}>${cur_indexer[1]}</option>
                % endfor
            </select>
        </td>
    </tr>
% endfor
    </tbody>
</table>
