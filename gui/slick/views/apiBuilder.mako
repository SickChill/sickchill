<%!
    import sickbeard
%>
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="robots" content="noindex, nofollow">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width">

    <!-- These values come from css/dark.css and css/light.css -->
    % if sbThemeName == "dark":
    <meta name="theme-color" content="#15528F">
    % elif sbThemeName == "light":
    <meta name="theme-color" content="#333333">
    % endif

    <title>SickRage - BRANCH:[${sickbeard.BRANCH}] - ${title}</title>

    <!--[if lt IE 9]>
    <script src="https://oss.maxcdn.com/html5shiv/3.7.2/html5shiv.min.js"></script>
    <script src="https://oss.maxcdn.com/respond/1.4.2/respond.min.js"></script>
    <![endif]-->
    <meta name="msapplication-TileColor" content="#FFFFFF">
    <meta name="msapplication-TileImage" content="${srRoot}/images/ico/favicon-144.png">
    <meta name="msapplication-config" content="${srRoot}/css/browserconfig.xml">

    <meta data-var="srRoot" data-content="${srRoot}">
    <meta data-var="themeSpinner" data-content="${('', '-dark')[sickbeard.THEME_NAME == 'dark']}">
    <meta data-var="anonURL" data-content="${sickbeard.ANON_REDIRECT}">

    <meta data-var="sickbeard.ANIME_SPLIT_HOME" data-content="${sickbeard.ANIME_SPLIT_HOME}">
    <meta data-var="sickbeard.COMING_EPS_LAYOUT" data-content="${sickbeard.COMING_EPS_LAYOUT}">
    <meta data-var="sickbeard.COMING_EPS_SORT" data-content="${sickbeard.COMING_EPS_SORT}">
    <meta data-var="sickbeard.DATE_PRESET" data-content="${sickbeard.DATE_PRESET}">
    <meta data-var="sickbeard.FILTER_ROW" data-content="${sickbeard.FILTER_ROW}">
    <meta data-var="sickbeard.FUZZY_DATING" data-content="${sickbeard.FUZZY_DATING}">
    <meta data-var="sickbeard.HISTORY_LAYOUT" data-content="${sickbeard.HISTORY_LAYOUT}">
    <meta data-var="sickbeard.HOME_LAYOUT" data-content="${sickbeard.HOME_LAYOUT}">
    <meta data-var="sickbeard.POSTER_SORTBY" data-content="${sickbeard.POSTER_SORTBY}">
    <meta data-var="sickbeard.POSTER_SORTDIR" data-content="${sickbeard.POSTER_SORTDIR}">
    <meta data-var="sickbeard.ROOT_DIRS" data-content="${sickbeard.ROOT_DIRS}">
    <meta data-var="sickbeard.SORT_ARTICLE" data-content="${sickbeard.SORT_ARTICLE}">
    <meta data-var="sickbeard.TIME_PRESET" data-content="${sickbeard.TIME_PRESET}">
    <meta data-var="sickbeard.TRIM_ZERO" data-content="${sickbeard.TRIM_ZERO}">

    <link rel="shortcut icon" href="${srRoot}/images/ico/favicon.ico">
    <link rel="icon" sizes="16x16 32x32 64x64" href="${srRoot}/images/ico/favicon.ico">
    <link rel="icon" type="image/png" sizes="196x196" href="${srRoot}/images/ico/favicon-196.png">
    <link rel="icon" type="image/png" sizes="160x160" href="${srRoot}/images/ico/favicon-160.png">
    <link rel="icon" type="image/png" sizes="96x96" href="${srRoot}/images/ico/favicon-96.png">
    <link rel="icon" type="image/png" sizes="64x64" href="${srRoot}/images/ico/favicon-64.png">
    <link rel="icon" type="image/png" sizes="32x32" href="${srRoot}/images/ico/favicon-32.png">
    <link rel="icon" type="image/png" sizes="16x16" href="${srRoot}/images/ico/favicon-16.png">
    <link rel="apple-touch-icon" sizes="152x152" href="${srRoot}/images/ico/favicon-152.png">
    <link rel="apple-touch-icon" sizes="144x144" href="${srRoot}/images/ico/favicon-144.png">
    <link rel="apple-touch-icon" sizes="120x120" href="${srRoot}/images/ico/favicon-120.png">
    <link rel="apple-touch-icon" sizes="114x114" href="${srRoot}/images/ico/favicon-114.png">
    <link rel="apple-touch-icon" sizes="76x76" href="${srRoot}/images/ico/favicon-76.png">
    <link rel="apple-touch-icon" sizes="72x72" href="${srRoot}/images/ico/favicon-72.png">
    <link rel="apple-touch-icon" href="${srRoot}/images/ico/favicon-57.png">

    <link rel="stylesheet" type="text/css" href="${srRoot}/css/lib/bootstrap.min.css?${sbPID}"/>
    <link rel="stylesheet" type="text/css" href="${srRoot}/css/browser.css?${sbPID}" />
    <link rel="stylesheet" type="text/css" href="${srRoot}/css/lib/jquery-ui-1.10.4.custom.min.css?${sbPID}" />
    <link rel="stylesheet" type="text/css" href="${srRoot}/css/style.css?${sbPID}"/>
    <link rel="stylesheet" type="text/css" href="${srRoot}/css/${sbThemeName}.css?${sbPID}" />
</head>
<body>
<nav class="navbar navbar-default navbar-fixed-top hidden-print" role="navigation">
    <div class="container-fluid">
        <div class="navbar-header">
            <button type="button" class="navbar-toggle collapsed" data-toggle="collapse" data-target="#nav-collapsed">
                <span class="sr-only">Toggle navigation</span>
                <span class="icon-bar"></span>
                <span class="icon-bar"></span>
                <span class="icon-bar"></span>
            </button>
            <a class="navbar-brand" href="${srRoot}/apibuilder/" title="SickRage">
                <img alt="SickRage" src="${srRoot}/images/sickrage.png" style="height: 50px;" class="img-responsive pull-left" />
                <p class="navbar-text hidden-xs">${title}</p>
            </a>
        </div>

        <div class="collapse navbar-collapse" id="nav-collapsed">
            <div class="btn-group navbar-btn" data-toggle="buttons">
                <label class="btn btn-primary">
                    <input autocomplete="off" id="option-profile" type="checkbox" /> Profile
                </label>
                <label class="btn btn-primary">
                    <input autocomplete="off" id="option-jsonp" type="checkbox" /> JSONP
                </label>
            </div>

            <ul class="nav navbar-nav navbar-right">
                <li><a href="${srRoot}/home/">Back to SickRage</a></li>
                <li class="hidden-xs">
                    <a href="https://github.com/SiCKRAGETV/SickRage/wiki/Donations" rel="noreferrer" onclick="window.open('${sickbeard.ANON_REDIRECT}' + this.href); return false;">
                        <img src="${srRoot}/images/donate.jpg" alt="[donate]" class="navbaricon" />
                    </a>
                </li>
            </ul>

            <form class="navbar-form navbar-right">
                <div class="form-group">
                    <input autocomplete="off" class="form-control" id="command-search" placeholder="Command name" type="search"/>
                </div>
            </form>
        </div>
    </div>
</nav>

<div id="content">
    <div class="panel-group" id="commands_list">
        % for command in sorted(commands):
        <%
            command_id = command.replace('.', '-')
            help = commands[command]((), {'help': 1}).run()
        %>
        <div class="panel panel-default">
            <div class="panel-heading">
                <h4 class="panel-title">
                    <a data-toggle="collapse" data-parent="#commands_list" href="#command-${command_id}">${command}</a>
                </h4>
            </div>
            <div class="panel-collapse collapse" id="command-${command_id}">
                <div class="panel-body">
                    <blockquote>${help['message']}</blockquote>

                    % if help['data']['optionalParameters'] or help['data']['requiredParameters']:
                    <h4>Parameters</h4>

                    <table class="tablesorter">
                    <thead>
                        <tr>
                            <th>Name</th>
                            <th>Required</th>
                            <th>Description</th>
                            <th>Type</th>
                            <th>Default value</th>
                            <th>Allowed values</th>
                        </tr>
                    </thead>
                    ${display_parameters_doc(help['data']['requiredParameters'], True)}
                    ${display_parameters_doc(help['data']['optionalParameters'], False)}
                    </table>
                    % endif

                    <h4>Playground</h4>

                    URL: <kbd id="command-${command_id}-base-url">/api/${apikey}/?cmd=${command}</kbd><br>

                    % if help['data']['requiredParameters']:
                        Required parameters: ${display_parameters_playground(help['data']['requiredParameters'], True, command_id)}<br>
                    % endif

                    % if help['data']['optionalParameters']:
                        Optional parameters: ${display_parameters_playground(help['data']['optionalParameters'], False, command_id)}<br>
                    % endif

                    <button class="btn btn-primary" data-action="api-call" data-command-name="${command_id}" data-base-url="command-${command_id}-base-url" data-target="#command-${command_id}-response" data-time="#command-${command_id}-time" data-url="#command-${command_id}-url">Call API</button><br>

                    <div class="result-wrapper hidden">
                        <div class="clearfix">
                            <span class="pull-left">
                                Response: <strong id="command-${command_id}-time"></strong><br>
                                URL: <kbd id="command-${command_id}-url"></kbd>
                            </span>
                            <span class="pull-right">
                                <button class="btn btn-default" data-action="clear-result" data-target="#command-${command_id}-response">Clear</button>
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

<script type="text/javascript">
var commands = ${sorted(commands)};
var episodes = ${episodes};
</script>
<script type="text/javascript" src="${srRoot}/js/_bower.min.js?${sbPID}"></script>
<script type="text/javascript" src="${srRoot}/js/new/meta.js?${sbPID}"></script>
<script type="text/javascript" src="${srRoot}/js/new/core.js?${sbPID}"></script>
<script type="text/javascript" src="${srRoot}/js/apibuilder.js?${sbPID}"></script>
</body>
</html>

<%def name="display_parameters_doc(parameters, required)">
<tbody>
% for parameter in parameters:
    <% parameter_help = parameters[parameter] %>
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
                <span class="glyphicon glyphicon-ok text-success" title="Yes"></span>
            % else:
                <span class="glyphicon glyphicon-remove text-muted" title="No"></span>
            % endif
        </td>
        <td>${parameter_help['desc'] if 'desc' in parameter_help else ''}</td>
        <td>${parameter_help['type'] if 'type' in parameter_help else ''}</td>
        <td>${parameter_help['defaultValue'] if 'defaultValue' in parameter_help else ''}</td>
        <td>${parameter_help['allowedValues'] if 'allowedValues' in parameter_help else ''}</td>
    </tr>
% endfor
</tbody>
</%def>

<%def name="display_parameters_playground(parameters, required, command)">
<div class="form-inline">
    % for parameter in parameters:
    <%
        parameter_help = parameters[parameter]
        allowed_values = parameter_help['allowedValues'] if 'allowedValues' in parameter_help else ''
        type = parameter_help['type'] if 'type' in parameter_help else ''
    %>

    % if isinstance(allowed_values, list):
        <select class="form-control"${('', ' multiple="multiple"')[type == 'list']} name="${parameter}" data-command="${command}">
            <option>${parameter}</option>

            % if allowed_values == [0, 1]:
                <option value="0">No</option>
                <option value="1">Yes</option>
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

        % if 'season' in parameters:
        <select class="form-control hidden" name="season" data-action="update-episodes" data-command="${command}">
            <option>season</option>
        </select>
        % endif

        % if 'episode' in parameters:
        <select class="form-control hidden" name="episode" data-command="${command}">
            <option>episode</option>
        </select>
        % endif
    % elif parameter == 'tvdbid':
        <select class="form-control" name="${parameter}" data-command="${command}">
            <option>${parameter}</option>

            % for show in shows:
            <option value="${show.indexerid}">${show.name}</option>
            % endfor
        </select>
    % elif type == 'int':
        % if parameter not in ('episode', 'season'):
        <input class="form-control" name="${parameter}" placeholder="${parameter}" type="number" data-command="${command}" />
        % endif
    % elif type == 'string':
        <input class="form-control" name="${parameter}" placeholder="${parameter}" type="text" data-command="${command}" />
    % endif
% endfor
</div>
</%def>
