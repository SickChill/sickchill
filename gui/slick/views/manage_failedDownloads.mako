<%inherit file="/layouts/main.mako"/>
<%!
    import sickbeard
    import os.path
    import datetime
    import re
    from sickbeard import providers
    from sickbeard.providers import generic
    from sickbeard.common import SKIPPED, WANTED, UNAIRED, ARCHIVED, IGNORED, SNATCHED, SNATCHED_PROPER, SNATCHED_BEST, FAILED
    from sickbeard.common import Quality, qualityPresets, qualityPresetStrings, statusStrings, Overview
%>
<%block name="scripts">
<script type="text/javascript">
$(document).ready(function(){
    $("#failedTable:has(tbody tr)").tablesorter({
        widgets: ['zebra'],
        sortList: [[0,0]],
        headers: { 3: { sorter: false } }
    });
    $('#limit').change(function(){
        url = '${sbRoot}/manage/failedDownloads/?limit='+$(this).val()
        window.location.href = url
    });
});
</script>
<script type="text/javascript" src="${sbRoot}/js/failedDownloads.js?${sbPID}"></script>
</%block>
<%block name="content">
% if not header is UNDEFINED:
    <h1 class="header">${header}</h1>
% else:
    <h1 class="title">${title}</h1>
% endif

<div class="h2footer pull-right"><b>Limit:</b>
    <select name="limit" id="limit" class="form-control form-control-inline input-sm">
        <option value="100" ${('', 'selected="selected"')[limit == '100']}>100</option>
        <option value="250" ${('', 'selected="selected"')[limit == '250']}>250</option>
        <option value="500" ${('', 'selected="selected"')[limit == '500']}>500</option>
        <option value="0" ${('', 'selected="selected"')[limit == '0']}>All</option>
    </select>
</div>

<table id="failedTable" class="sickbeardTable tablesorter" cellspacing="1" border="0" cellpadding="0">
  <thead>
    <tr>
      <th class="nowrap" width="75%" style="text-align: left;">Release</th>
      <th width="10%">Size</th>
      <th width="14%">Provider</th>
      <th width="1%">Remove<br />
          <input type="checkbox" class="bulkCheck" id="removeCheck" />
      </th>
    </tr>
  </thead>
  <tfoot>
    <tr>
      <td rowspan="1" colspan="4"><input type="button" class="btn pull-right" value="Submit" id="submitMassRemove"></td>
    </tr>
  </tfoot>
  <tbody>
% for hItem in failedResults:
<% curRemove  = "<input type=\"checkbox\" class=\"removeCheck\" id=\"remove-"+hItem["release"]+"\" />" %>
  <tr>
    <td class="nowrap">${hItem["release"]}</td>
    <td align="center">
    % if hItem["size"] != -1:
        ${hItem["size"]}
    % else:
        ?
    % endif
    </td>
    <td align="center">
    <% provider = providers.getProviderClass(generic.GenericProvider.makeID(hItem["provider"])) %>
    % if provider != None:
        <img src="${sbRoot}/images/providers/${provider.imageName()}" width="16" height="16" alt="${provider.name}" title="${provider.name}"/>
    % else:
        <img src="${sbRoot}/images/providers/missing.png" width="16" height="16" alt="missing provider" title="missing provider"/>
    % endif
    </td>
    <td align="center">${curRemove}</td>
  </tr>
% endfor
  </tbody>
</table>
</%block>
