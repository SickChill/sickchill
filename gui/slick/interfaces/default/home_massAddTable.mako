#import sickbeard
#from sickbeard.helpers import anon_url

<table id="addRootDirTable" class="sickbeardTable tablesorter">
  <thead><tr><th class="col-checkbox"><input type="checkbox" id="checkAll" checked=checked></th><th>Directory</th><th width="20%">Show Name (tvshow.nfo)<th width="20%">Indexer</td></tr></thead>
  <tbody>
#for $curDir in $dirList:
#if $curDir['added_already']:
#continue
#end if

#set $show_id = $curDir['dir']
#if $curDir['existing_info'][0]:
#set $show_id = $show_id + '|' + $str($curDir['existing_info'][0]) + '|' + $str($curDir['existing_info'][1])
#set $indexer = $curDir['existing_info'][2]
#end if

#set $indexer = 0
#if $curDir['existing_info'][0]:
    #set $indexer = $curDir['existing_info'][2]
#elif $sickbeard.INDEXER_DEFAULT > 0:
    #set $indexer = $sickbeard.INDEXER_DEFAULT
#end if

  <tr>
    <td class="col-checkbox"><input type="checkbox" id="$show_id" class="dirCheck" checked=checked></td>
    <td><label for="$show_id">$curDir['display_dir']</label></td>
    #if $curDir['existing_info'][1] and $indexer > 0:
        <td><a href="<%= anon_url(sickbeard.indexerApi(indexer).config['show_url'], curDir['existing_info'][0]) %>">$curDir['existing_info'][1]</a></td>
    #else:
        <td>?</td>
    #end if
    <td align="center">
        <select name="indexer">
            #for $curIndexer in $sickbeard.indexerApi().indexers.items():
                <option value="$curIndexer[0]" #if $curIndexer[0] == $indexer then "selected=\"selected\"" else "UNKNOWN"#>$curIndexer[1]</option>
            #end for
        </select>
    </td>
  </tr>
#end for
  </tbody>
</tbody>
</table>