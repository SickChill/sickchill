<%inherit file="/layouts/main.mako"/>
<%!
    from sickchill.oldbeard import providers
    from sickchill.providers.GenericProvider import GenericProvider
%>
<%block name="content">
    <div class="row">
        <div class="col-lg-4 col-md-4 col-sm-4 col-xs-12 pull-right">
            <div class="pull-right">
                <label>
                    <span>${_('Limit')}:</span>
                    <select name="limit" id="limit" class="form-control form-control-inline input-sm" title="limit">
                        <option value="100" ${('', 'selected="selected"')[limit == '100']}>${_('100')}</option>
                        <option value="250" ${('', 'selected="selected"')[limit == '250']}>${_('250')}</option>
                        <option value="500" ${('', 'selected="selected"')[limit == '500']}>${_('500')}</option>
                        <option value="0" ${('', 'selected="selected"')[limit == '0']}>${_('All')}</option>
                    </select>
                </label>
            </div>
        </div>
        <div class="col-lg-6 col-md-6 col-sm-8 col-xs-12">
            % if not header is UNDEFINED:
                <h1 class="header">${header}</h1>
            % else:
                <h1 class="title">${title}</h1>
            % endif
        </div>
    </div>
    <div class="row">
        <div class="col-md-12">
            <div class="horizontal-scroll">
                <table id="failedTable" class="sickchillTable">
                    <thead>
                        <tr>
                            <th width="1%" data-sorter="false"></th>
                            <th>
                                <label>${_('Release')}</label>
                            </th>
                            <th width="8%">
                                <label>${_('Size')}</label>
                            </th>
                            <th width="1%" data-sorter="false">
                                <label for="removeCheck">${_('Remove')}</label>
                                <br>
                                <input type="checkbox" class="bulkCheck" id="removeCheck" />
                            </th>
                        </tr>
                    </thead>
                    <tbody>
                        % for hItem in failedResults:
                            <tr>
                                <td>
                                    <% provider = providers.getProviderClass(GenericProvider.make_id(hItem["provider"])) %>
                                    % if provider is not None:
                                        <img src="${static_url('images/providers/' + provider.image_name())}" width="16" height="16" alt="${provider.name}" title="${provider.name}"/>
                                    % else:
                                        <img src="${static_url('images/providers/missing.png')}" width="16" height="16" alt="Missing provider" title="Missing provider"/>
                                    % endif
                                </td>
                                <td>
                                    <span>&nbsp;${hItem["release"]}</span>
                                </td>
                                <td align="center">
                                    % if hItem["size"] != -1:
                                        ${round(hItem["size"] / 10e+5, 2)} MB
                                    % else:
                                        <i>${_("Unknown")}</i>
                                    % endif
                                </td>
                                <td align="center">
                                    <input type="checkbox" class="removeCheck" id="remove-${hItem["release"] | u}" />
                                </td>
                            </tr>
                        % endfor
                    </tbody>
                    <tfoot>
                        <tr>
                            <td rowspan="1" colspan="4"><input type="button" class="btn pull-right" value="${_('Submit')}" id="submitMassRemove"></td>
                        </tr>
                    </tfoot>
                </table>
            </div>
        </div>
    </div>
</%block>
