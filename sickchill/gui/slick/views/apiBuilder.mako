<%inherit file="/layouts/main.mako"/>
<%!
    import json
    from urllib.parse import urljoin

    from sickchill import settings
%>
<%block name="css">
    <style type="text/css">
        .text-toogle[aria-expanded=false] .text-expanded {
            display: none;
        }
        .text-toogle[aria-expanded=true] .text-collapsed {
            display: none;
        }
    </style>
</%block>
<%block name="scripts">
    <script type="text/javascript">
        //noinspection JSUnusedLocalSymbols
        let episodes = ${ json.dumps(episodes) };
        //noinspection JSUnusedLocalSymbols
        let commands = ${ json.dumps(sorted(commands)) };
    </script>
    <script type="text/javascript" src="${static_url('js/apibuilder.js')}"></script>
</%block>

<%block name="navbar">
    <li class="btn-group navbar-btn navbar-toggle" data-toggle="buttons">
        <label class="btn btn-primary">
            <input autocomplete="off" id="option-profile" type="checkbox"/> ${_('Profile')}
        </label>
        <label class="btn btn-primary">
            <input autocomplete="off" id="option-jsonp" type="checkbox"/> ${_('JSONP')}
        </label>
    </li>
</%block>
<%block name="content">
<div class="row">
    <div class="col-md-12">
        % if not header is UNDEFINED:
            <h1 class="header">${header}</h1>
        % else:
            <h1 class="title">${title}</h1>
        % endif
    </div>
</div>
<div class="row">
    <div class="col-md-12">
        <div class="panel-group" id="commands_list">
            % for command in sorted(commands):
                <%
                    command_id = command.replace('.', '-')
                    command_help = commands[command]((), {'help': 1}).run()
                %>
                <div class="panel panel-default">
                    <div class="panel-heading">
                        <h4 class="panel-title">
                            <a data-toggle="collapse" data-parent="#commands_list" class="btn-block text-toogle" aria-expanded="false" href="#command-${command_id}">
                                ${command}
                                <btn class="pull-right btn btn-inline text-collapsed">Show</btn>
                                <btn class="pull-right btn btn-inline text-expanded">Hide</btn>
                            </a>
                        </h4>
                    </div>
                    <div class="panel-collapse collapse" id="command-${command_id}">
                        <div class="panel-body">
                            <div class="row">
                                <div class="col-md-12">
                                    <blockquote>${command_help['message']}</blockquote>
                                </div>
                            </div>
                            % if command_help['data']['optionalParameters'] or command_help['data']['requiredParameters']:
                                <div class="row">
                                    <div class="col-md-12">
                                        <h4>${_('Parameters')}</h4>

                                        <div class="horizontal-scroll">
                                            <table class="tablesorter">
                                                <thead>
                                                    <tr>
                                                        <th>${_('Name')}</th>
                                                        <th>${_('Required')}</th>
                                                        <th>${_('Description')}</th>
                                                        <th>${_('Type')}</th>
                                                        <th>${_('Default value')}</th>
                                                        <th>${_('Allowed values')}</th>
                                                    </tr>
                                                </thead>
                                                ${display_parameters_doc(command_help['data'], True)}
                                                ${display_parameters_doc(command_help['data'], False)}
                                            </table>
                                        </div>
                                    </div>
                                </div>
                            % endif
                            <div class="row">
                                <div class="col-md-12">
                                    <h4>${_('Playground')}</h4>
                                    <span>URL:&nbsp;<kbd id="command-${command_id}-base-url">/api/${apikey}/?cmd=${command}</kbd></span>
                                </div>
                            </div>
                            % if command_help['data']['requiredParameters']:
                                <br/>
                                <div class="row">
                                    <div class="col-md-12">
                                        <label>Required parameters</label>
                                        ${display_parameters_playground(command_help['data'], True, command_id)}
                                    </div>
                                </div>
                            % endif
                            % if command_help['data']['optionalParameters']:
                                <br/>
                                <div class="row">
                                    <div class="col-md-12">
                                        <label>Optional parameters</label>
                                        ${display_parameters_playground(command_help['data'], False, command_id)}
                                    </div>
                                </div>
                            % endif
                            <br/>
                            <div class="row">
                                <div class="col-md-12">
                                    <button class="btn btn-primary" data-action="api-call" data-command-name="${command_id}"
                                            data-base-url="command-${command_id}-base-url"
                                            data-target="#command-${command_id}-response"
                                            data-time="#command-${command_id}-time" data-url="#command-${command_id}-url">
                                        Call API
                                    </button>
                                </div>
                            </div>

                            <div class="result-wrapper hidden">
                                <div class="clearfix">
                                    <span class="pull-left">
                                        Response: <strong id="command-${command_id}-time"></strong><br>
                                        URL: <kbd id="command-${command_id}-url"></kbd>
                                    </span>
                                    <span class="pull-right">
                                        <button class="btn btn-default" data-action="clear-result" data-target="#command-${command_id}-response">${_('Clear')}</button>
                                    </span>
                                </div>
                                <pre><code id="command-${command_id}-response"></code></pre>
                            </div>
                        </div>
                    </div>
                </div>
            % endfor
        </div>
    </div>
</div>
</%block>

<%def name="display_parameters_doc(parameters, required)">
    <tbody>
        <%
            if required:
                parameter_list = parameters['requiredParameters']
            else:
                parameter_list = parameters['optionalParameters']
        %>
        % for parameter in parameter_list:
            <% parameter_help = parameter_list[parameter] %>
            <tr>
                <td>
                    % if required:
                        <strong>${parameter}</strong>
                    % else:
                        ${parameter}
                    % endif
                </td>
                <td class="text-center">
                    % if required:
                        <span class="glyphicon glyphicon-ok text-success" title="${_('Yes')}"></span>
                    % else:
                        <span class="glyphicon glyphicon-remove text-muted" title="${_('No')}"></span>
                    % endif
                </td>
                <td>${parameter_help.get('desc', '')}</td>
                <td>${parameter_help.get('type', '')}</td>
                <td>${parameter_help.get('defaultValue', '')}</td>
                <td>${parameter_help.get('allowedValues', '')}</td>
            </tr>
        % endfor
    </tbody>
</%def>

<%def name="display_parameters_playground(parameters, required, command)">
    <div class="form-inline">
        <%
            if required:
                # noinspection PyUnusedLocal
                parameter_list = parameters['requiredParameters']
            else:
                # noinspection PyUnusedLocal
                parameter_list = parameters['optionalParameters']
        %>
        % for parameter in parameter_list:
            <%
                parameter_help = parameter_list[parameter]
                allowed_values = parameter_help.get('allowedValues', '')
                type = parameter_help.get('type', '')
            %>

            % if isinstance(allowed_values, list):
                <select class="form-control"${('', ' multiple="multiple"')[type == 'list']} name="${parameter}" data-command="${command}">
                    <option>${parameter}</option>

                    % if allowed_values == [0, 1]:
                        <option value="0">${_('No')}</option>
                        <option value="1">${_('Yes')}</option>
                    % else:
                        % for allowed_value in allowed_values:
                            <option value="${allowed_value}">${allowed_value}</option>
                        % endfor
                    % endif
                </select>
            % elif parameter == 'indexerid':
                <select class="form-control" name="${parameter}" data-action="update-seasons" data-command="${command}">
                    <option>${parameter}</option>

                    % for show in shows:
                        <option value="${show.indexerid}">${show.name}</option>
                    % endfor
                </select>
                % if 'season' in parameters['requiredParameters'] or 'season' in parameters['optionalParameters']:
                    <select class="form-control hidden" name="season" data-action="update-episodes" data-command="${command}">
                        <option>${_('season')}</option>
                    </select>
                % endif

                % if 'episode' in parameters['requiredParameters'] or 'episode' in parameters['optionalParameters']:
                    <select class="form-control hidden" name="episode" data-command="${command}">
                        <option>${_('episode')}</option>
                    </select>
                % endif
            % elif parameter == 'tvdbid':
                <input class="form-control" name="${parameter}" placeholder="${parameter}" type="number" data-command="${command}"/>
            % elif type == 'int':
                % if parameter not in ('episode', 'season'):
                    <input class="form-control" name="${parameter}" placeholder="${parameter}" type="number" data-command="${command}"/>
                % endif
            % elif type == 'string':
                <input class="form-control" name="${parameter}" placeholder="${parameter}" type="text" data-command="${command}"/>
            % endif
        % endfor
    </div>
</%def>
