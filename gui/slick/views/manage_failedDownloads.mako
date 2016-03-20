<%inherit file="/layouts/main.mako"/>
<%!
    from sickbeard import providers
    from sickrage.providers.GenericProvider import GenericProvider
%>
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
      <th width="1%">Remove<br>
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
    <% provider = providers.getProviderClass(GenericProvider.make_id(hItem["provider"])) %>
    % if provider is not None:
        <img src="${srRoot}/images/providers/${provider.image_name()}" width="16" height="16" alt="${provider.name}" title="${provider.name}"/>
    % else:
        <img src="${srRoot}/images/providers/missing.png" width="16" height="16" alt="missing provider" title="missing provider"/>
    % endif
    </td>
    <td align="center"><input type="checkbox" class="removeCheck" id="remove-${hItem["release"] | u}" /></td>
  </tr>
% endfor
  </tbody>
</table>
</%block>
