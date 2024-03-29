<%inherit file="/layouts/main.mako" />
<%!
    from sickchill.helper.common import dateTimeFormat, pretty_file_size
    from sickchill.oldbeard.common import Quality
    from sickchill.oldbeard.providers import getProviderClass
%>
<%block name="content">
    <%namespace file="/inc_defs.mako" import="renderQualityPill" />
    <div class="row">
        % if results:
            <table id="manualSearchShowTable" class="sickchillTable tablesorter">
                <thead>
                    <tr>
                        <th class="text-center text-nowrap tablesorter-header">${_('Provider')}</th>
                        <th class="text-center text-nowrap tablesorter-header">${_('Name')}</th>
                        <th class="text-center text-nowrap tablesorter-header">${_('Episode')}</th>
                        <th class="text-center text-nowrap tablesorter-header">${_('Quality')}</th>
                        <th class="text-center text-nowrap tablesorter-header" data-metric-name-abbr="b|B">${_('Size')}</th>
                        <th class="text-center text-nowrap tablesorter-header">${_('Seeders')}</th>
                        <th class="text-center text-nowrap tablesorter-header">${_('Leechers')}</th>
                        <th class="text-center text-nowrap tablesorter-header">${_('Download')}</th>
                    </tr>
                </thead>
                <tbody>
                    % for result in results:
                        <tr class="${('odd', 'even')[loop.index % 2]}">
                            <% provider = getProviderClass(result["provider"]) %>
                            <td class="text-center text-nowrap" title="${provider.name}">
                                <img src="${static_url('images/providers/' + provider.image_name())}" width="16" height="16" alt="${provider.name}" />
                            </td>
                            <td class="text-center text-nowrap">${result['name']}</td>
                            <td class="text-center text-nowrap">${result['ep_string']}</td>
                            <td class="text-center text-nowrap">${renderQualityPill(result['quality'])}</td>
                            <td class="text-center text-nowrap">${pretty_file_size(result['size'])}</td>
                            <td class="text-center text-nowrap">${result['seeders']}</td>
                            <td class="text-center text-nowrap">${result['leechers']}</td>
                            <td class="text-center text-nowrap">
                                <form action="manual_snatch_show_release" method="post">
                                    <input type="hidden" name="url" value="${result['url']}">
                                    <input type="hidden" name="show" value="${result['indexerid']}">
                                    <input type="submit" value="${result['url'].split(':', 1)[0].title()}" class="btn btn-link">
                                </form>
                            </td>
                        </tr>
                    % endfor
                </tbody>
            </table>
        % else:
            No cached results, try an automated search first
        % endif
    </div>
</%block>
