<%inherit file="/layouts/main.mako"/>
<%!
    import sickbeard
    from sickbeard.logger import LOGGING_LEVELS
%>
<%block name="content">
    <div class="row">
        <div class="col-lg-10 col-md-9 col-sm-12 col-xs-12 pull-right">
            <div class="pull-right">
                <label>
                    <span>${_('Minimum logging level to display')}:</span>
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
                    &nbsp;
                </label>
                <label>
                    <span>${_('Filter log by')}:</span>
                    <select name="logFilter" id="logFilter" class="form-control form-control-inline input-sm" title="filter">
                        % for logNameFilter in sorted(logNameFilters):
                            <option value="${logNameFilter}" ${('', 'selected="selected"')[logFilter == logNameFilter]}>${logNameFilters[logNameFilter]}</option>
                        % endfor
                    </select>
                    &nbsp;
                </label>
                <label>
                    <span>${_('Search log by')}:</span>
                    <input type="text" name="logSearch" placeholder="clear to reset" id="logSearch" value="${('', logSearch)[bool(logSearch)]}" class="form-control form-control-inline input-sm" autocapitalize="off" />
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
            <pre>${logLines}</pre>
        </div>
    </div>
</%block>
