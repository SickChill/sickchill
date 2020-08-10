<%inherit file="/layouts/main.mako"/>
<%!
    from sickchill.helper.common import dateTimeFormat, pretty_file_size
    from sickchill.oldbeard.common import Quality
    from sickchill.oldbeard.providers import getProviderClass
    quality = Quality.qualityStrings
%>
<%block name="content">
    <div class="row">
        % if results:
            <table class="sickchillTable tablesorter">
                <thead>
                    <tr>
                        <th align="center" class="text-nowrap tablesorter-header">${_('Provider')}</th>
                        <th align="center" class="text-nowrap tablesorter-header">${_('Name')}</th>
                        <th align="center" class="text-nowrap tablesorter-header">${_('Episode')}</th>
                        <th align="center" class="text-nowrap tablesorter-header">${_('Quality')}</th>
                        <th align="center" class="text-nowrap tablesorter-header">${_('Size')}</th>
                        <th align="center" class="text-nowrap tablesorter-header">${_('Seeders')}</th>
                        <th align="center" class="text-nowrap tablesorter-header">${_('Leechers')}</th>
                    </tr>
                </thead>
                <tbody>
                    % for result in results:
                        <tr>
                            <% provider = getProviderClass(result["provider"]) %>
                            <td align="center" class="text-nowrap" title="${provider.name}">
                                <img src="${static_url('images/providers/' + provider.image_name())}" width="16" height="16" alt="${provider.name}"/>
                            </td>
                            <td align="center" class="text-nowrap">${result['name']}</td>
                            <td align="center" class="text-nowrap">${result['ep_string']}</td>
                            <td align="center" class="text-nowrap">${quality[result['quality']]}</td>
                            <td align="center" class="text-nowrap">${pretty_file_size(result['size'])}</td>
                            <td align="center" class="text-nowrap">${result['seeders']}</td>
                            <td align="center" class="text-nowrap">${result['leechers']}</td>
                        </tr>
                    % endfor
                </tbody>
            </table>
        % else:
            No cached results, try an automated search first
        % endif
    </div>
</%block>
