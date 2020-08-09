<%!
    from sickchill import settings
    from sickchill.oldbeard.helpers import anon_url
    import sickchill
%>

<table id="addRootDirTable" class="sickchillTable tablesorter">
    <thead>
        <tr>
            <th class="col-checkbox"><input type="checkbox" id="checkAll" checked=checked></th>
            <th>${_('Directory')}</th>
            <th width="20%">${_('Show Name (tvshow.nfo)')}
            <th width="20%">${_('Indexer')}</th>
        </tr>
    </thead>
    <tbody>
        % for curDir in dirList:
            <%
                if curDir['added_already']:
                    continue

                indexer = 0
                show_id = curDir['dir']
                if curDir['existing_info'][0]:
                    show_id = show_id + '|' + str(curDir['existing_info'][0]) + '|' + str(curDir['existing_info'][1])
                    indexer = curDir['existing_info'][2]

                if curDir['existing_info'][0]:
                    indexer = curDir['existing_info'][2]
                elif settings.INDEXER_DEFAULT > 0:
                    indexer = settings.INDEXER_DEFAULT
            %>
            <tr>
                <td class="col-checkbox"><input type="checkbox" id="${show_id}" class="dirCheck" checked=checked></td>
                <td><label for="${show_id}">${curDir['display_dir']}</label></td>
                % if curDir['existing_info'][1] and indexer > 0:
                    <td>
                        <a href="${anon_url(sickchill.indexer[indexer].show_url, curDir['existing_info'][0])}">${curDir['existing_info'][1]}</a>
                    </td>
                % else:
                    <td>?</td>
                % endif
                <td align="center">
                    <select name="indexer">
                        % for index, curIndexer in sickchill.indexer:
                            <option value="${index}" ${('', 'selected="selected"')[index == indexer]}>${curIndexer.name}</option>
                        % endfor
                    </select>
                </td>
            </tr>
        % endfor
    </tbody>
</table>
