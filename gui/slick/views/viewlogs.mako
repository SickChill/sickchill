<%inherit file="/layouts/main.mako"/>
<%!
    import sickbeard
    from sickbeard.logger import LOGGING_LEVELS
%>
<%block name="content">
    <div class="row">
        <div class="pull-right col-lg-10 col-md-10 col-sm-12 col-xs-12">
            <div class="pull-right" style="padding: 5px;">
                ${_('Minimum logging level to display')}:
                <select name="minLevel" id="minLevel" class="form-control form-control-inline input-sm" title="Minimal level">
                    <%
                        levels = LOGGING_LEVELS.keys()
                        levels.sort(lambda x, y: cmp(LOGGING_LEVELS[x], LOGGING_LEVELS[y]))
                        if not sickbeard.DEBUG:
                            levels.remove('DEBUG')
                        if not sickbeard.DBDEBUG:
                            levels.remove('DB')
                    %>
                    % for level in levels:
                        <option value="${LOGGING_LEVELS[level]}" ${('', 'selected="selected"')[minLevel == LOGGING_LEVELS[level]]}>${level.title()}</option>
                    % endfor
                </select>
            </div>
            <div class="pull-right" style="padding: 5px;">
                ${_('Filter log by')}:
                <select name="logFilter" id="logFilter" class="form-control form-control-inline input-sm" title="filter">
                    % for logNameFilter in sorted(logNameFilters):
                        <option value="${logNameFilter}" ${('', 'selected="selected"')[logFilter == logNameFilter]}>${logNameFilters[logNameFilter]}</option>
                    % endfor
                </select>
            </div>
            <div class="pull-right" style="padding: 5px;">
                ${_('Search log by')}:
                <input type="text" name="logSearch" placeholder="clear to reset" id="logSearch" value="${('', logSearch)[bool(logSearch)]}" class="form-control form-control-inline input-sm" autocapitalize="off" />
            </div>
        </div>
        <div class="col-lg-2 col-md-2 col-sm-12 col-xs-12">
            % if not header is UNDEFINED:
                <h1 class="header">${header}</h1>
            % else:
                <h1 class="title">${title}</h1>
            % endif
        </div>
    </div>
    <div class="row">
        <div class="col-md-12 align-left">
            <pre>${logLines}</pre>
        </div>
    </div>
</%block>
