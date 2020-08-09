<%inherit file="/layouts/main.mako"/>
<%!
    from sickchill import settings
    from sickchill.logger import LOGGING_LEVELS, LOG_FILTERS
%>
<%block name="content">
    <div class="row">
        <div class="col-lg-10 col-md-9 col-sm-12 col-xs-12 pull-right">
            <div class="pull-right">
                <a href="" id="log_update_toggle" class="btn" data-state="active" title="${_('Pause updating the log on this page.')}">
                    <i class='fa fa-pause'></i>
                    <span>${_('Pause')}</span>
                </a>
                &nbsp;
                <label>
                    <span>${_('Level')}:</span>
                    <select name="min_level" id="min_level" class="form-control form-control-inline input-sm" title="Minimum log level">
                        <%
                            levels = sorted(LOGGING_LEVELS)
                            if not settings.DEBUG:
                                levels.remove('DEBUG')
                            if not settings.DBDEBUG:
                                levels.remove('DB')
                        %>
                        % for level in levels:
                            <option value="${LOGGING_LEVELS[level]}" ${('', 'selected="selected"')[min_level == LOGGING_LEVELS[level]]}>${level.title()}</option>
                        % endfor
                    </select>
                    &nbsp;
                </label>
                <label>
                    <span>${_('Filter')}:</span>
                    <select name="log_filter" id="log_filter" class="form-control form-control-inline input-sm" title="filter">
                        % for _log_filter in sorted(LOG_FILTERS):
                            <option value="${_log_filter}" ${('', 'selected="selected"')[log_filter == _log_filter]}>${LOG_FILTERS[_log_filter]}</option>
                        % endfor
                    </select>
                </label>
                <label>
                    <span>${_('Search')}:</span>
                    <input type="text" name="log_search" placeholder="clear to reset" id="log_search" value="${log_search}" class="form-control form-control-inline input-sm" autocapitalize="off" />
                </label>
            </div>
        </div>
        <div class="col-lg-2 col-md-3 col-sm-12 col-xs-12">
            % if not header is UNDEFINED:
                <h1 class="header">${header}</h1>
            % else:
                <h1 class="title">${title}</h1>
            % endif
        </div>
    </div>
    <div class="row">
        <div class="col-md-12 align-left">
            <pre id="log_data">${log_data}</pre>
        </div>
    </div>
</%block>
