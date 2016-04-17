<%inherit file="/layouts/main.mako"/>
<%!
    import sickbeard
    from sickbeard.logger import LOGGING_LEVELS
%>
<%block name="css">
<style>
pre {
  overflow: auto;
  word-wrap: normal;
  white-space: pre;
}
</style>
</%block>
<%block name="content">
    <div class="container-fluid">
        <div class="row">
	        <div class="pull-right col-lg-10 col-md-10 col-sm-9 col-xs-12">
                <div class="row">
                    <div class="col-lg-4 col-md-4 col-sm-6 col-xs-12">
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
	                <div class="col-lg-4 col-md-4 col-sm-6 col-xs-12">
                        ${_('Filter log by')}:
	                    <select name="logFilter" id="logFilter" class="form-control form-control-inline input-sm" title="filter">
                            % for logNameFilter in sorted(logNameFilters):
			                    <option value="${logNameFilter}" ${('', 'selected="selected"')[logFilter == logNameFilter]}>${logNameFilters[logNameFilter]}</option>
                            % endfor
	                    </select>
                    </div>
	                <div class="col-lg-4 col-md-4 col-sm-6 col-xs-12">
                        ${_('Search log by')}:
	                    <input type="text" name="logSearch" placeholder="clear to reset" id="logSearch" value="${('', logSearch)[bool(logSearch)]}" class="form-control form-control-inline input-sm" autocapitalize="off" />
                    </div>
                </div>
	        </div>
	        <div class="col-lg-2 col-md-2 col-sm-3 col-xs-12">
                % if not header is UNDEFINED:
			        <h1 class="header">${header}</h1>
                % else:
			        <h1 class="title">${title}</h1>
                % endif
	        </div>
        </div>
        <div class="row">
	        <div class="col-md-12">
            <pre>
                ${logLines}
            </pre>
	        </div>
        </div>
    </div>
</%block>
