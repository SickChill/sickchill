<%inherit file="main.mako"/>
<%!
    import os
    import datetime
    import sickbeard
    from sickbeard.common import SKIPPED, ARCHIVED, IGNORED, statusStrings, cpu_presets
    from sickbeard.sbdatetime import sbdatetime, date_presets, time_presets
    from sickbeard.helpers import anon_url
%>

<%block name="scripts">
	<script type="text/javascript" src="${srRoot}/js/rootDirs.js?${sbPID}"></script>
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
			<form id="configForm" action="saveGeneral" method="post">
                <div class="row">
                    <div class="col-md-12">
	                    <div id="config-components">
		                    <ul>
                                <%block name="tabs"/>
		                    </ul>

                            <%block name="pages"/>
	                    </div>

                        <br/>
	                    <h6 class="pull-right">
		                    <b>
                                ${_('All non-absolute folder locations are relative to ')}
			                    <span class="path">${sickbeard.DATA_DIR}</span>
		                    </b>
	                    </h6>
	                    <input type="submit" class="btn pull-left config_submitter button" value="${_('Save Changes')}"/>
                    </div>
                </div>
			</form>
		</div>
	</div>
</%block>

